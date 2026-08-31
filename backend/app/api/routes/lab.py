"""FastAPI API routes for Laboratory Management and Diagnostic Workflows."""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Path, Body, status, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User, UserRole
from app.models.lab import (
    LabTest,
    LabOrder,
    LabOrderStatus,
    LabOrderPriority,
    SampleCondition,
    ResultFlag,
)
from app.dependencies.auth import (
    get_current_active_user,
    require_role,
    get_current_doctor_user,
    get_current_patient_user,
    get_current_admin_user,
    get_current_lab_technician_user,
)
from app.schemas.lab import (
    LabTestCreate,
    LabTestUpdate,
    LabTestRead,
    LabOrderCreate,
    LabOrderRead,
    LabOrderSummary,
    LabSampleCreate,
    LabSampleRead,
    LabResultBatchCreate,
    LabVerificationRequest,
    LabQueueStats,
    LabAdminStats,
    PatientReleasedLabReportRead,
    PatientReleasedItemRead,
)
from app.services.lab_service import lab_service

router = APIRouter(prefix="/lab", tags=["Lab Management & Diagnostics"])


def _serialize_order_summary(order: LabOrder) -> LabOrderSummary:
    """Format LabOrder instance to LabOrderSummary."""
    patient_name = order.patient.user.full_name if order.patient and order.patient.user else f"Patient #{order.patient_id}"
    doctor_name = order.doctor.user.full_name if order.doctor and order.doctor.user else f"Dr. #{order.doctor_id}"
    test_names = [item.test.test_name for item in order.items if item.test]
    is_critical_flagged = any(
        item.result and item.result.is_critical for item in order.items
    )
    return LabOrderSummary(
        id=order.id,
        patient_id=order.patient_id,
        patient_name=patient_name,
        doctor_id=order.doctor_id,
        doctor_name=doctor_name,
        priority=order.priority,
        status=order.status,
        test_count=len(order.items),
        test_names=test_names,
        is_critical_flagged=is_critical_flagged,
        ordered_at=order.ordered_at,
        updated_at=order.updated_at,
    )


def _serialize_order_detail(order: LabOrder) -> LabOrderRead:
    """Format LabOrder instance to full LabOrderRead."""
    patient_name = order.patient.user.full_name if order.patient and order.patient.user else f"Patient #{order.patient_id}"
    doctor_name = order.doctor.user.full_name if order.doctor and order.doctor.user else f"Dr. #{order.doctor_id}"

    # Format items
    items_read = []
    for item in order.items:
        res_read = None
        if item.result:
            entered_by_name = item.result.entered_by.full_name if item.result.entered_by else "Staff"
            verified_by_name = item.result.verified_by.full_name if item.result.verified_by else None
            res_read = {
                "id": item.result.id,
                "lab_order_item_id": item.result.lab_order_item_id,
                "test_name": item.result.test_name,
                "numeric_value": item.result.numeric_value,
                "text_value": item.result.text_value,
                "unit": item.result.unit,
                "reference_range": item.result.reference_range,
                "result_flag": item.result.result_flag,
                "entered_by_user_id": item.result.entered_by_user_id,
                "entered_by_name": entered_by_name,
                "entered_at": item.result.entered_at,
                "verified_by_user_id": item.result.verified_by_user_id,
                "verified_by_name": verified_by_name,
                "verified_at": item.result.verified_at,
                "verification_notes": item.result.verification_notes,
                "is_critical": item.result.is_critical,
            }

        items_read.append({
            "id": item.id,
            "lab_order_id": item.lab_order_id,
            "lab_test_id": item.lab_test_id,
            "test": item.test,
            "instructions": item.instructions,
            "result": res_read,
        })

    # Format samples
    samples_read = []
    for s in order.samples:
        samples_read.append({
            "id": s.id,
            "lab_order_id": s.lab_order_id,
            "technician_id": s.technician_id,
            "technician_name": s.technician.full_name if s.technician else "Lab Technician",
            "specimen_type": s.specimen_type,
            "collected_at": s.collected_at,
            "sample_condition": s.sample_condition,
            "collection_notes": s.collection_notes,
        })

    # Format audit events
    audits_read = []
    for a in order.audit_events:
        audits_read.append({
            "id": a.id,
            "lab_order_id": a.lab_order_id,
            "action": a.action,
            "performed_by_user_id": a.performed_by_user_id,
            "performed_by_name": a.performed_by.full_name if a.performed_by else "System",
            "details": a.details,
            "created_at": a.created_at,
        })

    return LabOrderRead(
        id=order.id,
        patient_id=order.patient_id,
        patient_name=patient_name,
        doctor_id=order.doctor_id,
        doctor_name=doctor_name,
        clinical_notes=order.clinical_notes,
        priority=order.priority,
        status=order.status,
        ordered_at=order.ordered_at,
        updated_at=order.updated_at,
        items=items_read,
        samples=samples_read,
        audit_events=audits_read,
    )


# ---------------------------------------------------------------------------
# 1. LAB TEST CATALOG
# ---------------------------------------------------------------------------
@router.get("/tests", response_model=List[LabTestRead])
def list_lab_tests(
    category: Optional[str] = Query(None, description="Filter by category (Hematology, Biochemistry, etc.)"),
    search: Optional[str] = Query(None, description="Search by test name or code"),
    active_only: bool = Query(True, description="Filter only active tests"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List available laboratory tests in the diagnostic catalog."""
    items, _ = lab_service.list_lab_tests(
        db=db,
        category=category,
        search=search,
        active_only=active_only,
        skip=skip,
        limit=limit,
    )
    return items


@router.get("/tests/{test_id}", response_model=LabTestRead)
def get_lab_test(
    test_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get single lab test details from catalog."""
    return lab_service.get_test_by_id(db=db, test_id=test_id)


@router.post("/tests", response_model=LabTestRead, status_code=status.HTTP_201_CREATED)
def create_lab_test(
    test_in: LabTestCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    """Create a new diagnostic test definition (Admin only)."""
    return lab_service.create_lab_test(db=db, test_in=test_in, admin_user=admin_user)


@router.put("/tests/{test_id}", response_model=LabTestRead)
def update_lab_test(
    test_id: int = Path(..., ge=1),
    test_in: LabTestUpdate = Body(...),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    """Update lab test catalog parameters (Admin only)."""
    return lab_service.update_lab_test(db=db, test_id=test_id, test_in=test_in, admin_user=admin_user)


@router.patch("/tests/{test_id}/status", response_model=LabTestRead)
def toggle_lab_test_status(
    test_id: int = Path(..., ge=1),
    is_active: bool = Query(..., description="Active status flag"),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    """Toggle lab test active status (Admin only)."""
    return lab_service.toggle_test_status(db=db, test_id=test_id, is_active=is_active, admin_user=admin_user)


# ---------------------------------------------------------------------------
# 2. DOCTOR LAB ORDERS
# ---------------------------------------------------------------------------
@router.post("/orders", response_model=LabOrderRead, status_code=status.HTTP_201_CREATED)
def create_lab_order(
    order_in: LabOrderCreate,
    db: Session = Depends(get_db),
    doctor_user: User = Depends(get_current_doctor_user),
):
    """
    Create a laboratory test requisition for a patient.
    Requires doctor approval and active clinical relationship.
    """
    order = lab_service.create_lab_order(db=db, doctor_user=doctor_user, order_in=order_in)
    return _serialize_order_detail(order)


@router.get("/orders/my-doctor-orders", response_model=List[LabOrderSummary])
def list_doctor_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    doctor_user: User = Depends(get_current_doctor_user),
):
    """List diagnostic lab orders authored by the authenticated doctor."""
    orders, _ = lab_service.list_doctor_orders(db=db, doctor_user=doctor_user, skip=skip, limit=limit)
    return [_serialize_order_summary(o) for o in orders]


@router.get("/orders/{order_id}", response_model=LabOrderRead)
def get_lab_order(
    order_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """View full lab order details with RBAC authorization validation."""
    order = lab_service.get_order_by_id(db=db, order_id=order_id, current_user=current_user)
    return _serialize_order_detail(order)


@router.post("/orders/{order_id}/cancel", response_model=LabOrderRead)
def cancel_lab_order(
    order_id: int = Path(..., ge=1),
    reason: Optional[str] = Query(None, description="Cancellation reason"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Cancel a pending lab order (Doctor or Admin)."""
    if current_user.role not in [UserRole.DOCTOR, UserRole.ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized to cancel lab orders.")
    order = lab_service.cancel_lab_order(db=db, order_id=order_id, user=current_user, reason=reason)
    return _serialize_order_detail(order)


# ---------------------------------------------------------------------------
# 3. LAB TECHNICIAN WORK QUEUE & PROCESSING WORKFLOWS
# ---------------------------------------------------------------------------
@router.get("/queue", response_model=List[LabOrderSummary])
def get_lab_work_queue(
    status_filter: Optional[LabOrderStatus] = Query(None, alias="status"),
    priority_filter: Optional[LabOrderPriority] = Query(None, alias="priority"),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    tech_user: User = Depends(get_current_lab_technician_user),
):
    """Retrieve operational work queue for Lab Technician dashboard."""
    orders, _ = lab_service.get_work_queue(
        db=db,
        status_filter=status_filter,
        priority_filter=priority_filter,
        search=search,
        skip=skip,
        limit=limit,
    )
    return [_serialize_order_summary(o) for o in orders]


@router.get("/stats", response_model=LabQueueStats)
def get_lab_queue_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve real-time operational statistics for lab dashboard."""
    if current_user.role not in [UserRole.LAB_TECHNICIAN, UserRole.ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    return lab_service.get_lab_queue_stats(db=db)


@router.get("/admin-stats", response_model=LabAdminStats)
def get_admin_lab_stats(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    """Retrieve aggregated diagnostic analytics for platform administration."""
    return lab_service.get_admin_lab_stats(db=db)


@router.post("/orders/{order_id}/collect-sample", response_model=LabSampleRead)
def collect_lab_sample(
    order_id: int = Path(..., ge=1),
    sample_in: LabSampleCreate = Body(...),
    db: Session = Depends(get_db),
    tech_user: User = Depends(get_current_lab_technician_user),
):
    """
    Record specimen collection for a lab order (Lab Technician only).
    Rejects compromised specimens and prompts recollection.
    """
    sample = lab_service.collect_sample(db=db, order_id=order_id, tech_user=tech_user, sample_in=sample_in)
    return {
        "id": sample.id,
        "lab_order_id": sample.lab_order_id,
        "technician_id": sample.technician_id,
        "technician_name": tech_user.full_name,
        "specimen_type": sample.specimen_type,
        "collected_at": sample.collected_at,
        "sample_condition": sample.sample_condition,
        "collection_notes": sample.collection_notes,
    }


@router.post("/orders/{order_id}/start-processing", response_model=LabOrderRead)
def start_lab_processing(
    order_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    tech_user: User = Depends(get_current_lab_technician_user),
):
    """Commence analytical laboratory processing (Lab Technician only)."""
    order = lab_service.start_processing(db=db, order_id=order_id, tech_user=tech_user)
    return _serialize_order_detail(order)


@router.post("/orders/{order_id}/enter-results", response_model=LabOrderRead)
def enter_lab_results(
    order_id: int = Path(..., ge=1),
    batch_in: LabResultBatchCreate = Body(...),
    db: Session = Depends(get_db),
    tech_user: User = Depends(get_current_lab_technician_user),
):
    """
    Enter analytical test results with automatic critical value evaluation (Lab Technician only).
    """
    order = lab_service.enter_results(db=db, order_id=order_id, tech_user=tech_user, batch_in=batch_in)
    return _serialize_order_detail(order)


@router.post("/orders/{order_id}/verify", response_model=LabOrderRead)
def verify_lab_results(
    order_id: int = Path(..., ge=1),
    req: Optional[LabVerificationRequest] = Body(None),
    db: Session = Depends(get_db),
    tech_user: User = Depends(get_current_lab_technician_user),
):
    """Verify diagnostic results (Lab Technician only)."""
    notes = req.verification_notes if req else None
    order = lab_service.verify_results(db=db, order_id=order_id, tech_user=tech_user, verification_notes=notes)
    return _serialize_order_detail(order)


@router.post("/orders/{order_id}/release", response_model=LabOrderRead)
def release_lab_results(
    order_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    tech_user: User = Depends(get_current_lab_technician_user),
):
    """
    Release verified diagnostic report for patient and ordering doctor access (Lab Technician only).
    """
    order = lab_service.release_results(db=db, order_id=order_id, tech_user=tech_user)
    return _serialize_order_detail(order)


# ---------------------------------------------------------------------------
# 4. PATIENT RELEASED REPORTS
# ---------------------------------------------------------------------------
@router.get("/patient/my-reports", response_model=List[PatientReleasedLabReportRead])
def get_patient_lab_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    patient_user: User = Depends(get_current_patient_user),
):
    """Retrieve all verified and released diagnostic laboratory reports for the calling patient."""
    orders, _ = lab_service.get_patient_released_reports(db=db, patient_user=patient_user, skip=skip, limit=limit)

    reports = []
    for order in orders:
        doctor_name = order.doctor.user.full_name if order.doctor and order.doctor.user else "Attending Physician"
        doctor_spec = order.doctor.specialization if order.doctor else None
        
        # Determine verified by name
        verified_name = None
        for item in order.items:
            if item.result and item.result.verified_by:
                verified_name = item.result.verified_by.full_name
                break

        results = []
        for item in order.items:
            if item.result:
                results.append(
                    PatientReleasedItemRead(
                        test_name=item.result.test_name,
                        category=item.test.category if item.test else "General",
                        numeric_value=item.result.numeric_value,
                        text_value=item.result.text_value,
                        unit=item.result.unit,
                        reference_range=item.result.reference_range,
                        result_flag=item.result.result_flag,
                        is_critical=item.result.is_critical,
                    )
                )

        reports.append(
            PatientReleasedLabReportRead(
                id=order.id,
                doctor_name=doctor_name,
                doctor_specialization=doctor_spec,
                priority=order.priority,
                status=order.status,
                ordered_at=order.ordered_at,
                released_at=order.updated_at,
                verified_by_name=verified_name,
                results=results,
            )
        )

    return reports


@router.get("/patient/my-reports/{order_id}", response_model=PatientReleasedLabReportRead)
def get_patient_lab_report_detail(
    order_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    patient_user: User = Depends(get_current_patient_user),
):
    """View details of a single released laboratory report."""
    order = lab_service.get_order_by_id(db=db, order_id=order_id, current_user=patient_user)
    doctor_name = order.doctor.user.full_name if order.doctor and order.doctor.user else "Attending Physician"
    doctor_spec = order.doctor.specialization if order.doctor else None

    verified_name = None
    for item in order.items:
        if item.result and item.result.verified_by:
            verified_name = item.result.verified_by.full_name
            break

    results = []
    for item in order.items:
        if item.result:
            results.append(
                PatientReleasedItemRead(
                    test_name=item.result.test_name,
                    category=item.test.category if item.test else "General",
                    numeric_value=item.result.numeric_value,
                    text_value=item.result.text_value,
                    unit=item.result.unit,
                    reference_range=item.result.reference_range,
                    result_flag=item.result.result_flag,
                    is_critical=item.result.is_critical,
                )
            )

    return PatientReleasedLabReportRead(
        id=order.id,
        doctor_name=doctor_name,
        doctor_specialization=doctor_spec,
        priority=order.priority,
        status=order.status,
        ordered_at=order.ordered_at,
        released_at=order.updated_at,
        verified_by_name=verified_name,
        results=results,
    )
