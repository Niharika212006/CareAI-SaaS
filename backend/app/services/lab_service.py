"""Comprehensive domain service for Laboratory Management and Diagnostic Workflows."""
import logging
from datetime import datetime, timezone, date
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, and_
from fastapi import HTTPException, status

from app.models.lab import (
    LabTest,
    LabOrder,
    LabOrderItem,
    LabSample,
    LabResult,
    LabAuditEvent,
    LabOrderPriority,
    LabOrderStatus,
    SampleCondition,
    ResultFlag,
)
from app.models.doctor import DoctorProfile, DoctorApprovalStatus
from app.models.patient import PatientProfile
from app.models.appointment import Appointment, AppointmentStatus
from app.models.prescription import Prescription
from app.models.user import User, UserRole
from app.models.notification import Notification, NotificationType, NotificationPriority
from app.schemas.lab import (
    LabTestCreate,
    LabTestUpdate,
    LabOrderCreate,
    LabSampleCreate,
    LabResultBatchCreate,
    LabQueueStats,
    LabAdminStats,
    PatientReleasedLabReportRead,
    PatientReleasedItemRead,
)
from app.services.lab_critical_rules import evaluate_result_flag
from app.services.notification_service import notification_service

logger = logging.getLogger("healthcare.lab.service")


class LabService:
    """Domain service managing the complete diagnostic lifecycle from ordering to release."""

    # -----------------------------------------------------------------------
    # 1. LAB TEST CATALOG (ADMIN / DOCTOR / LAB TECH)
    # -----------------------------------------------------------------------
    @staticmethod
    def create_lab_test(db: Session, test_in: LabTestCreate, admin_user: User) -> LabTest:
        """Create a new diagnostic test in the catalog (Admin only)."""
        existing = db.query(LabTest).filter(LabTest.test_code == test_in.test_code.strip().upper()).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A laboratory test with code '{test_in.test_code}' already exists.",
            )

        test = LabTest(
            test_name=test_in.test_name.strip(),
            test_code=test_in.test_code.strip().upper(),
            category=test_in.category.strip(),
            description=test_in.description,
            specimen_type=test_in.specimen_type.strip(),
            reference_range=test_in.reference_range,
            unit=test_in.unit,
            preparation_instructions=test_in.preparation_instructions,
            estimated_turnaround_time=test_in.estimated_turnaround_time,
            is_active=test_in.is_active,
        )
        db.add(test)
        db.commit()
        db.refresh(test)
        return test

    @staticmethod
    def update_lab_test(db: Session, test_id: int, test_in: LabTestUpdate, admin_user: User) -> LabTest:
        """Update diagnostic test parameters in the catalog (Admin only)."""
        test = db.query(LabTest).filter(LabTest.id == test_id).first()
        if not test:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab test not found.")

        for field, val in test_in.model_dump(exclude_unset=True).items():
            if val is not None:
                if field == "test_name":
                    setattr(test, field, val.strip())
                elif field == "category":
                    setattr(test, field, val.strip())
                else:
                    setattr(test, field, val)

        db.commit()
        db.refresh(test)
        return test

    @staticmethod
    def toggle_test_status(db: Session, test_id: int, is_active: bool, admin_user: User) -> LabTest:
        """Activate or deactivate a laboratory test (Admin only)."""
        test = db.query(LabTest).filter(LabTest.id == test_id).first()
        if not test:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab test not found.")
        test.is_active = is_active
        db.commit()
        db.refresh(test)
        return test

    @staticmethod
    def list_lab_tests(
        db: Session,
        category: Optional[str] = None,
        search: Optional[str] = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[LabTest], int]:
        """List and search laboratory tests in the diagnostic catalog."""
        query = db.query(LabTest)
        if active_only:
            query = query.filter(LabTest.is_active.is_(True))
        if category and category.strip():
            query = query.filter(LabTest.category.ilike(f"%{category.strip()}%"))
        if search and search.strip():
            s = f"%{search.strip()}%"
            query = query.filter(or_(LabTest.test_name.ilike(s), LabTest.test_code.ilike(s), LabTest.description.ilike(s)))

        total = query.count()
        items = query.order_by(LabTest.category.asc(), LabTest.test_name.asc()).offset(skip).limit(limit).all()
        return items, total

    @staticmethod
    def get_test_by_id(db: Session, test_id: int) -> LabTest:
        """Retrieve single test by ID."""
        test = db.query(LabTest).filter(LabTest.id == test_id).first()
        if not test:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab test not found.")
        return test

    # -----------------------------------------------------------------------
    # 2. DOCTOR LAB ORDERING & CLINICAL RELATIONSHIP CHECKS
    # -----------------------------------------------------------------------
    @staticmethod
    def create_lab_order(db: Session, doctor_user: User, order_in: LabOrderCreate) -> LabOrder:
        """
        Create a new diagnostic lab order for a legitimately related patient.
        Enforces doctor approval and clinical relationship validation.
        """
        doctor_profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == doctor_user.id).first()
        if not doctor_profile:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only registered doctors can create laboratory orders.",
            )
        if doctor_profile.approval_status != DoctorApprovalStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your doctor credentials are currently pending administrative approval.",
            )

        # Resolve patient profile (by patient_profile.id or patient user.id)
        patient_profile = (
            db.query(PatientProfile)
            .filter(or_(PatientProfile.id == order_in.patient_id, PatientProfile.user_id == order_in.patient_id))
            .first()
        )
        if not patient_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient with identifier #{order_in.patient_id} not found.",
            )

        # Enforce Doctor-Patient clinical relationship check
        has_relationship = (
            db.query(Appointment)
            .filter(
                Appointment.doctor_id == doctor_profile.id,
                Appointment.patient_id == patient_profile.id,
            )
            .first()
        )
        if not has_relationship:
            # Also check if doctor has issued prescriptions for this patient
            has_prescription = (
                db.query(Prescription)
                .filter(
                    Prescription.doctor_id == doctor_profile.id,
                    Prescription.patient_id == patient_profile.id,
                )
                .first()
            )
            if not has_prescription:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Clinical authorization failed. Doctors may only order diagnostic tests for patients with an established appointment or consultation relationship.",
                )

        now = datetime.now(timezone.utc)
        order = LabOrder(
            patient_id=patient_profile.id,
            doctor_id=doctor_profile.id,
            clinical_notes=order_in.clinical_notes,
            priority=order_in.priority,
            status=LabOrderStatus.SAMPLE_PENDING,  # Automatically ready for sample collection
            ordered_at=now,
        )
        db.add(order)
        db.flush()  # Populate order.id

        # Add order items
        for item_in in order_in.items:
            test = db.query(LabTest).filter(LabTest.id == item_in.lab_test_id).first()
            if not test or not test.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Lab test #{item_in.lab_test_id} is inactive or does not exist.",
                )
            item = LabOrderItem(
                lab_order_id=order.id,
                lab_test_id=test.id,
                instructions=item_in.instructions,
            )
            db.add(item)

        # Record audit event
        audit = LabAuditEvent(
            lab_order_id=order.id,
            action="ORDER_CREATED",
            performed_by_user_id=doctor_user.id,
            details={"message": f"Doctor {doctor_user.full_name} created {order_in.priority.value} lab order with {len(order_in.items)} test(s)."},
            created_at=now,
        )
        db.add(audit)

        # If priority is URGENT or STAT, notify active Lab Technicians
        if order_in.priority in [LabOrderPriority.URGENT, LabOrderPriority.STAT]:
            techs = db.query(User).filter(User.role == UserRole.LAB_TECHNICIAN, User.is_active.is_(True)).all()
            for tech in techs:
                notification_service.create_notification(
                    db=db,
                    user_id=tech.id,
                    title=f"New {order_in.priority.value} Lab Requisition",
                    message=f"Order #{order.id} ({order_in.priority.value}) was placed by Dr. {doctor_user.full_name} requiring immediate specimen handling.",
                    notification_type=NotificationType.SYSTEM,
                    priority=NotificationPriority.CRITICAL if order_in.priority == LabOrderPriority.STAT else NotificationPriority.HIGH,
                )

        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def list_doctor_orders(db: Session, doctor_user: User, skip: int = 0, limit: int = 50) -> Tuple[List[LabOrder], int]:
        """List lab orders created by the authenticated doctor."""
        doctor_profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == doctor_user.id).first()
        if not doctor_profile:
            return [], 0

        query = (
            db.query(LabOrder)
            .options(
                joinedload(LabOrder.patient).joinedload(PatientProfile.user),
                joinedload(LabOrder.doctor).joinedload(DoctorProfile.user),
                joinedload(LabOrder.items).joinedload(LabOrderItem.test),
                joinedload(LabOrder.items).joinedload(LabOrderItem.result),
            )
            .filter(LabOrder.doctor_id == doctor_profile.id)
        )
        total = query.count()
        items = query.order_by(LabOrder.ordered_at.desc()).offset(skip).limit(limit).all()
        return items, total

    @staticmethod
    def get_order_by_id(db: Session, order_id: int, current_user: User) -> LabOrder:
        """Retrieve full lab order with RBAC authorization enforcement."""
        order = (
            db.query(LabOrder)
            .options(
                joinedload(LabOrder.patient).joinedload(PatientProfile.user),
                joinedload(LabOrder.doctor).joinedload(DoctorProfile.user),
                joinedload(LabOrder.items).joinedload(LabOrderItem.test),
                joinedload(LabOrder.items).joinedload(LabOrderItem.result),
                joinedload(LabOrder.samples).joinedload(LabSample.technician),
                joinedload(LabOrder.audit_events).joinedload(LabAuditEvent.performed_by),
            )
            .filter(LabOrder.id == order_id)
            .first()
        )
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Lab order #{order_id} not found.")

        # RBAC Authorization Check
        if current_user.role == UserRole.PATIENT:
            patient_profile = db.query(PatientProfile).filter(PatientProfile.user_id == current_user.id).first()
            if not patient_profile or order.patient_id != patient_profile.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
            if order.status != LabOrderStatus.RELEASED:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="This laboratory report is currently undergoing clinical processing/verification and has not been released.",
                )
        elif current_user.role == UserRole.DOCTOR:
            doctor_profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == current_user.id).first()
            if not doctor_profile:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Doctor profile required.")
            if order.doctor_id != doctor_profile.id:
                # Check clinical relationship
                rel = db.query(Appointment).filter(
                    Appointment.doctor_id == doctor_profile.id,
                    Appointment.patient_id == order.patient_id,
                ).first()
                if not rel:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You are not authorized to inspect lab orders for unrelated patients.",
                    )
        elif current_user.role in [UserRole.LAB_TECHNICIAN, UserRole.ADMIN]:
            pass  # Allowed
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized role.")

        return order

    @staticmethod
    def cancel_lab_order(db: Session, order_id: int, user: User, reason: Optional[str] = None) -> LabOrder:
        """Cancel a pending lab order."""
        order = db.query(LabOrder).filter(LabOrder.id == order_id).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab order not found.")

        if order.status in [LabOrderStatus.RELEASED, LabOrderStatus.CANCELLED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel order in '{order.status.value}' state.",
            )

        order.status = LabOrderStatus.CANCELLED
        audit = LabAuditEvent(
            lab_order_id=order.id,
            action="ORDER_CANCELLED",
            performed_by_user_id=user.id,
            details={"message": f"Cancelled by {user.full_name}. Reason: {reason or 'No reason provided.'}"},
            created_at=datetime.now(timezone.utc),
        )
        db.add(audit)
        db.commit()
        db.refresh(order)
        return order

    # -----------------------------------------------------------------------
    # 3. LAB TECHNICIAN WORK QUEUE & PROCESSING WORKFLOWS
    # -----------------------------------------------------------------------
    @staticmethod
    def get_work_queue(
        db: Session,
        status_filter: Optional[LabOrderStatus] = None,
        priority_filter: Optional[LabOrderPriority] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[LabOrder], int]:
        """Retrieve filterable work queue for Lab Technician dashboard."""
        query = (
            db.query(LabOrder)
            .options(
                joinedload(LabOrder.patient).joinedload(PatientProfile.user),
                joinedload(LabOrder.doctor).joinedload(DoctorProfile.user),
                joinedload(LabOrder.items).joinedload(LabOrderItem.test),
                joinedload(LabOrder.items).joinedload(LabOrderItem.result),
            )
            .filter(LabOrder.status != LabOrderStatus.CANCELLED)
        )

        if status_filter:
            query = query.filter(LabOrder.status == status_filter)
        if priority_filter:
            query = query.filter(LabOrder.priority == priority_filter)
        if search and search.strip():
            s = f"%{search.strip()}%"
            query = query.join(LabOrder.patient).join(PatientProfile.user).filter(
                or_(
                    User.full_name.ilike(s),
                    User.email.ilike(s),
                    LabOrder.clinical_notes.ilike(s),
                )
            )

        total = query.count()
        # STAT and URGENT prioritized first, then chronological
        items = (
            query.order_by(
                LabOrder.priority.desc(),
                LabOrder.ordered_at.desc(),
            )
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

    @staticmethod
    def collect_sample(
        db: Session,
        order_id: int,
        tech_user: User,
        sample_in: LabSampleCreate,
    ) -> LabSample:
        """
        Record specimen collection for a lab order.
        If specimen condition is invalid (HEMOLYZED/CLOTTED/INSUFFICIENT/CONTAMINATED),
        records rejection and requires recollection.
        """
        order = db.query(LabOrder).filter(LabOrder.id == order_id).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab order not found.")

        if order.status in [LabOrderStatus.RELEASED, LabOrderStatus.CANCELLED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot collect sample for order in '{order.status.value}' state.",
            )

        now = datetime.now(timezone.utc)
        sample = LabSample(
            lab_order_id=order.id,
            technician_id=tech_user.id,
            specimen_type=sample_in.specimen_type.strip(),
            collected_at=now,
            sample_condition=sample_in.sample_condition,
            collection_notes=sample_in.collection_notes,
        )
        db.add(sample)

        # Handle sample condition validity
        if sample_in.sample_condition == SampleCondition.ACCEPTABLE:
            order.status = LabOrderStatus.SAMPLE_COLLECTED
            audit = LabAuditEvent(
                lab_order_id=order.id,
                action="SAMPLE_COLLECTED",
                performed_by_user_id=tech_user.id,
                details={"message": f"Specimen ({sample_in.specimen_type}) collected by {tech_user.full_name}. Condition: ACCEPTABLE."},
                created_at=now,
            )
        else:
            # Invalid specimen requires recollection
            order.status = LabOrderStatus.SAMPLE_PENDING
            audit = LabAuditEvent(
                lab_order_id=order.id,
                action="SAMPLE_REJECTED",
                performed_by_user_id=tech_user.id,
                details={"message": f"Specimen ({sample_in.specimen_type}) rejected by {tech_user.full_name}. Condition: {sample_in.sample_condition.value}. Reason: {sample_in.collection_notes or 'Specimen integrity compromised'}. Recollection required."},
                created_at=now,
            )
            # Notify ordering doctor about rejected sample
            doc_user_id = order.doctor.user_id if order.doctor else None
            if doc_user_id:
                notification_service.create_notification(
                    db=db,
                    user_id=doc_user_id,
                    title="Specimen Recollection Required",
                    message=f"Specimen for Order #{order.id} was rejected ({sample_in.sample_condition.value}). Reason: {sample_in.collection_notes or 'Sample integrity issue'}.",
                    notification_type=NotificationType.SYSTEM,
                    priority=NotificationPriority.HIGH,
                )

        db.add(audit)
        db.commit()
        db.refresh(sample)
        return sample

    @staticmethod
    def start_processing(db: Session, order_id: int, tech_user: User) -> LabOrder:
        """Transition collected order to IN_PROGRESS analytical testing."""
        order = db.query(LabOrder).filter(LabOrder.id == order_id).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab order not found.")

        if order.status not in [LabOrderStatus.SAMPLE_COLLECTED, LabOrderStatus.SAMPLE_PENDING]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order must be in SAMPLE_COLLECTED state to begin analytical processing (current: '{order.status.value}').",
            )

        now = datetime.now(timezone.utc)
        order.status = LabOrderStatus.IN_PROGRESS
        audit = LabAuditEvent(
            lab_order_id=order.id,
            action="PROCESSING_STARTED",
            performed_by_user_id=tech_user.id,
            details={"message": f"Laboratory technician {tech_user.full_name} commenced analytical processing."},
            created_at=now,
        )
        db.add(audit)
        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def enter_results(
        db: Session,
        order_id: int,
        tech_user: User,
        batch_in: LabResultBatchCreate,
    ) -> LabOrder:
        """
        Enter diagnostic results for ordered tests.
        Evaluates critical thresholds deterministically and dispatches instant doctor alerts.
        """
        order = (
            db.query(LabOrder)
            .options(joinedload(LabOrder.items).joinedload(LabOrderItem.test))
            .filter(LabOrder.id == order_id)
            .first()
        )
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab order not found.")

        if order.status in [LabOrderStatus.RELEASED, LabOrderStatus.CANCELLED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot enter results for order in '{order.status.value}' state.",
            )

        now = datetime.now(timezone.utc)
        items_dict = {item.id: item for item in order.items}
        critical_findings = []

        for res_in in batch_in.results:
            item = items_dict.get(res_in.lab_order_item_id)
            if not item:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Lab order item #{res_in.lab_order_item_id} does not belong to Order #{order.id}.",
                )

            # Evaluate result flag deterministically
            flag, is_critical, explanation = evaluate_result_flag(
                test_code=item.test.test_code,
                test_name=item.test.test_name,
                numeric_value=res_in.numeric_value,
                text_value=res_in.text_value,
                custom_reference_range=res_in.reference_range or item.test.reference_range,
            )

            # Upsert result
            existing_result = db.query(LabResult).filter(LabResult.lab_order_item_id == item.id).first()
            if existing_result:
                existing_result.numeric_value = res_in.numeric_value
                existing_result.text_value = res_in.text_value
                existing_result.unit = res_in.unit or item.test.unit
                existing_result.reference_range = res_in.reference_range or item.test.reference_range
                existing_result.result_flag = flag
                existing_result.is_critical = is_critical
                existing_result.entered_by_user_id = tech_user.id
                existing_result.entered_at = now
            else:
                new_result = LabResult(
                    lab_order_item_id=item.id,
                    test_name=item.test.test_name,
                    numeric_value=res_in.numeric_value,
                    text_value=res_in.text_value,
                    unit=res_in.unit or item.test.unit,
                    reference_range=res_in.reference_range or item.test.reference_range,
                    result_flag=flag,
                    is_critical=is_critical,
                    entered_by_user_id=tech_user.id,
                    entered_at=now,
                )
                db.add(new_result)

            if is_critical:
                critical_findings.append((item.test.test_name, res_in.numeric_value or res_in.text_value, explanation))

        order.status = LabOrderStatus.RESULTS_ENTERED
        audit_details = f"Results entered by {tech_user.full_name} for {len(batch_in.results)} test(s)."
        if critical_findings:
            audit_details += f" [CRITICAL ALERTS DETECTED: {len(critical_findings)}]"

        audit = LabAuditEvent(
            lab_order_id=order.id,
            action="RESULTS_ENTERED",
            performed_by_user_id=tech_user.id,
            details={"message": audit_details},
            created_at=now,
        )
        db.add(audit)

        # If Critical findings exist, dispatch immediate urgent alert to ordering doctor and log critical audit
        if critical_findings:
            for test_name, val, expl in critical_findings:
                crit_audit = LabAuditEvent(
                    lab_order_id=order.id,
                    action="CRITICAL_RESULT_DETECTED",
                    performed_by_user_id=tech_user.id,
                    details={"message": f"CRITICAL VALUE: {test_name} = {val}. {expl}"},
                    created_at=now,
                )
                db.add(crit_audit)

            doc_user_id = order.doctor.user_id if order.doctor else None
            if doc_user_id:
                crit_summary = ", ".join([f"{t}: {v}" for t, v, _ in critical_findings])
                notification_service.create_notification(
                    db=db,
                    user_id=doc_user_id,
                    title="CRITICAL LAB VALUE ALERT",
                    message=f"CRITICAL PANIC VALUE for Order #{order.id} ({crit_summary}). Immediate clinical intervention advised.",
                    notification_type=NotificationType.SYSTEM,
                    priority=NotificationPriority.CRITICAL,
                )

        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def verify_results(
        db: Session,
        order_id: int,
        tech_user: User,
        verification_notes: Optional[str] = None,
    ) -> LabOrder:
        """
        Verify entered laboratory results.
        Enforces controlled verification signoff.
        """
        order = (
            db.query(LabOrder)
            .options(joinedload(LabOrder.items).joinedload(LabOrderItem.result))
            .filter(LabOrder.id == order_id)
            .first()
        )
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab order not found.")

        if order.status != LabOrderStatus.RESULTS_ENTERED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order must be in RESULTS_ENTERED state to perform clinical verification (current: '{order.status.value}').",
            )

        now = datetime.now(timezone.utc)
        for item in order.items:
            if not item.result:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot verify order: Missing result for item '{item.test.test_name}'.",
                )
            item.result.verified_by_user_id = tech_user.id
            item.result.verified_at = now
            item.result.verification_notes = verification_notes

        order.status = LabOrderStatus.VERIFIED
        audit = LabAuditEvent(
            lab_order_id=order.id,
            action="RESULTS_VERIFIED",
            performed_by_user_id=tech_user.id,
            details={"message": f"Clinical results verified by {tech_user.full_name}. Notes: {verification_notes or 'Verified against standard QC parameters.'}"},
            created_at=now,
        )
        db.add(audit)
        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def release_results(db: Session, order_id: int, tech_user: User) -> LabOrder:
        """
        Release verified laboratory results to patient and ordering doctor.
        Dispatches in-app notifications to both parties.
        """
        order = (
            db.query(LabOrder)
            .options(
                joinedload(LabOrder.patient).joinedload(PatientProfile.user),
                joinedload(LabOrder.doctor).joinedload(DoctorProfile.user),
                joinedload(LabOrder.items).joinedload(LabOrderItem.result),
            )
            .filter(LabOrder.id == order_id)
            .first()
        )
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab order not found.")

        if order.status != LabOrderStatus.VERIFIED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order must be VERIFIED before release (current: '{order.status.value}').",
            )

        now = datetime.now(timezone.utc)
        order.status = LabOrderStatus.RELEASED

        audit = LabAuditEvent(
            lab_order_id=order.id,
            action="RESULTS_RELEASED",
            performed_by_user_id=tech_user.id,
            details={"message": f"Verified diagnostic report released by {tech_user.full_name} for patient access."},
            created_at=now,
        )
        db.add(audit)

        # 1. Notify Patient
        if order.patient and order.patient.user_id:
            notification_service.create_notification(
                db=db,
                user_id=order.patient.user_id,
                title="Laboratory Report Available",
                message=f"Your diagnostic laboratory test results for Order #{order.id} are now verified and available in your patient portal.",
                notification_type=NotificationType.SYSTEM,
                priority=NotificationPriority.NORMAL,
            )

        # 2. Notify Ordering Doctor
        if order.doctor and order.doctor.user_id:
            notification_service.create_notification(
                db=db,
                user_id=order.doctor.user_id,
                title="Diagnostic Report Released",
                message=f"Laboratory results for Order #{order.id} (Patient: {order.patient.user.full_name if order.patient and order.patient.user else 'Patient'}) have been released.",
                notification_type=NotificationType.SYSTEM,
                priority=NotificationPriority.NORMAL,
            )

        db.commit()
        db.refresh(order)
        return order

    # -----------------------------------------------------------------------
    # 4. PATIENT RELEASED REPORTS
    # -----------------------------------------------------------------------
    @staticmethod
    def get_patient_released_reports(
        db: Session,
        patient_user: User,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[LabOrder], int]:
        """Retrieve all RELEASED lab orders for the authenticated patient."""
        patient_profile = db.query(PatientProfile).filter(PatientProfile.user_id == patient_user.id).first()
        if not patient_profile:
            return [], 0

        query = (
            db.query(LabOrder)
            .options(
                joinedload(LabOrder.doctor).joinedload(DoctorProfile.user),
                joinedload(LabOrder.items).joinedload(LabOrderItem.test),
                joinedload(LabOrder.items).joinedload(LabOrderItem.result),
            )
            .filter(
                LabOrder.patient_id == patient_profile.id,
                LabOrder.status == LabOrderStatus.RELEASED,
            )
        )
        total = query.count()
        items = query.order_by(LabOrder.ordered_at.desc()).offset(skip).limit(limit).all()
        return items, total

    # -----------------------------------------------------------------------
    # 5. DASHBOARD & OPERATIONAL STATISTICS
    # -----------------------------------------------------------------------
    @staticmethod
    def get_lab_queue_stats(db: Session) -> LabQueueStats:
        """Aggregate real-time statistics for the Lab Technician dashboard."""
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        pending_samples = (
            db.query(func.count(LabOrder.id))
            .filter(LabOrder.status.in_([LabOrderStatus.ORDERED, LabOrderStatus.SAMPLE_PENDING]))
            .scalar()
            or 0
        )
        samples_collected_today = (
            db.query(func.count(LabSample.id))
            .filter(LabSample.collected_at >= today_start)
            .scalar()
            or 0
        )
        tests_in_progress = (
            db.query(func.count(LabOrder.id))
            .filter(LabOrder.status.in_([LabOrderStatus.SAMPLE_COLLECTED, LabOrderStatus.IN_PROGRESS]))
            .scalar()
            or 0
        )
        results_awaiting_verification = (
            db.query(func.count(LabOrder.id))
            .filter(LabOrder.status == LabOrderStatus.RESULTS_ENTERED)
            .scalar()
            or 0
        )
        completed_tests_today = (
            db.query(func.count(LabOrder.id))
            .filter(LabOrder.status == LabOrderStatus.RELEASED, LabOrder.updated_at >= today_start)
            .scalar()
            or 0
        )
        critical_alerts_count = (
            db.query(func.count(LabResult.id))
            .filter(LabResult.is_critical.is_(True))
            .scalar()
            or 0
        )

        return LabQueueStats(
            pending_samples=pending_samples,
            samples_collected_today=samples_collected_today,
            tests_in_progress=tests_in_progress,
            results_awaiting_verification=results_awaiting_verification,
            completed_tests_today=completed_tests_today,
            critical_alerts_count=critical_alerts_count,
        )

    @staticmethod
    def get_admin_lab_stats(db: Session) -> LabAdminStats:
        """Aggregate operational and compliance metrics for Admin dashboard."""
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        total_orders = db.query(func.count(LabOrder.id)).scalar() or 0
        tests_pending = (
            db.query(func.count(LabOrder.id))
            .filter(LabOrder.status.in_([LabOrderStatus.ORDERED, LabOrderStatus.SAMPLE_PENDING, LabOrderStatus.IN_PROGRESS]))
            .scalar()
            or 0
        )
        completed_today = (
            db.query(func.count(LabOrder.id))
            .filter(LabOrder.status == LabOrderStatus.RELEASED, LabOrder.updated_at >= today_start)
            .scalar()
            or 0
        )
        total_critical = (
            db.query(func.count(LabAuditEvent.id))
            .filter(LabAuditEvent.action == "CRITICAL_RESULT_DETECTED")
            .scalar()
            or 0
        )
        active_catalog_count = (
            db.query(func.count(LabTest.id))
            .filter(LabTest.is_active.is_(True))
            .scalar()
            or 0
        )

        return LabAdminStats(
            total_orders_all_time=total_orders,
            tests_pending_processing=tests_pending,
            orders_completed_today=completed_today,
            total_critical_events=total_critical,
            active_test_catalog_count=active_catalog_count,
        )


lab_service = LabService()
