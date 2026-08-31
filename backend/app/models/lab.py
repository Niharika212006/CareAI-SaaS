"""SQLAlchemy database models for Lab Management and Diagnostic Workflow."""
import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Float,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.models.base import TimeStampedModel


class LabOrderPriority(str, enum.Enum):
    """Clinical priority of a laboratory order."""
    ROUTINE = "ROUTINE"
    URGENT = "URGENT"
    STAT = "STAT"


class LabOrderStatus(str, enum.Enum):
    """Lifecycle stages of a diagnostic laboratory order."""
    ORDERED = "ORDERED"
    SAMPLE_PENDING = "SAMPLE_PENDING"
    SAMPLE_COLLECTED = "SAMPLE_COLLECTED"
    IN_PROGRESS = "IN_PROGRESS"
    RESULTS_ENTERED = "RESULTS_ENTERED"
    VERIFIED = "VERIFIED"
    RELEASED = "RELEASED"
    CANCELLED = "CANCELLED"


class SampleCondition(str, enum.Enum):
    """Quality and integrity condition of a collected biological specimen."""
    ACCEPTABLE = "ACCEPTABLE"
    HEMOLYZED = "HEMOLYZED"
    CLOTTED = "CLOTTED"
    INSUFFICIENT = "INSUFFICIENT"
    CONTAMINATED = "CONTAMINATED"


class ResultFlag(str, enum.Enum):
    """Clinical alert flag comparing result value against diagnostic reference intervals."""
    NORMAL = "NORMAL"
    LOW = "LOW"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class LabTest(Base, TimeStampedModel):
    """Standardized diagnostic test definition in the laboratory catalog."""
    __tablename__ = "lab_tests"

    test_name = Column(String(255), nullable=False, index=True)
    test_code = Column(String(50), unique=True, nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)  # Hematology, Biochemistry, etc.
    description = Column(Text, nullable=True)
    specimen_type = Column(String(100), nullable=False)  # Whole Blood, Serum, Plasma, Urine, etc.
    reference_range = Column(String(255), nullable=True)  # e.g., "70 - 99 mg/dL"
    unit = Column(String(50), nullable=True)  # e.g., "mg/dL", "mmol/L", "%"
    preparation_instructions = Column(Text, nullable=True)  # e.g., "Fasting 8-12 hours required"
    estimated_turnaround_time = Column(String(100), nullable=True)  # e.g., "2-4 hours"
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Relationships
    order_items = relationship("LabOrderItem", back_populates="test")

    def __repr__(self) -> str:
        return f"<LabTest(id={self.id}, code='{self.test_code}', name='{self.test_name}', active={self.is_active})>"


class LabOrder(Base, TimeStampedModel):
    """Laboratory test requisition order placed by a doctor for an authorized patient."""
    __tablename__ = "lab_orders"

    patient_id = Column(
        Integer,
        ForeignKey("patient_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    doctor_id = Column(
        Integer,
        ForeignKey("doctor_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    clinical_notes = Column(Text, nullable=True)
    priority = Column(
        SQLEnum(LabOrderPriority),
        default=LabOrderPriority.ROUTINE,
        nullable=False,
        index=True,
    )
    status = Column(
        SQLEnum(LabOrderStatus),
        default=LabOrderStatus.ORDERED,
        nullable=False,
        index=True,
    )
    ordered_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    patient = relationship("PatientProfile", backref="lab_orders")
    doctor = relationship("DoctorProfile", backref="lab_orders")
    items = relationship(
        "LabOrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="LabOrderItem.id.asc()",
    )
    samples = relationship(
        "LabSample",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="LabSample.collected_at.asc()",
    )
    audit_events = relationship(
        "LabAuditEvent",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="LabAuditEvent.created_at.asc()",
    )

    def __repr__(self) -> str:
        return f"<LabOrder(id={self.id}, patient_id={self.patient_id}, doctor_id={self.doctor_id}, status='{self.status}')>"


class LabOrderItem(Base):
    """Specific diagnostic test included in a laboratory requisition order."""
    __tablename__ = "lab_order_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    lab_order_id = Column(
        Integer,
        ForeignKey("lab_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lab_test_id = Column(
        Integer,
        ForeignKey("lab_tests.id"),
        nullable=False,
        index=True,
    )
    instructions = Column(Text, nullable=True)

    # Relationships
    order = relationship("LabOrder", back_populates="items")
    test = relationship("LabTest", back_populates="order_items")
    result = relationship(
        "LabResult",
        back_populates="order_item",
        uselist=False,
        cascade="all, delete-orphan",
    )


class LabSample(Base):
    """Biological specimen collection record for a laboratory order."""
    __tablename__ = "lab_samples"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    lab_order_id = Column(
        Integer,
        ForeignKey("lab_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    technician_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    specimen_type = Column(String(100), nullable=False)
    collected_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    sample_condition = Column(
        SQLEnum(SampleCondition),
        default=SampleCondition.ACCEPTABLE,
        nullable=False,
    )
    collection_notes = Column(Text, nullable=True)

    # Relationships
    order = relationship("LabOrder", back_populates="samples")
    technician = relationship("User", foreign_keys=[technician_id])


class LabResult(Base):
    """Analytical test result entered and verified by laboratory staff."""
    __tablename__ = "lab_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    lab_order_item_id = Column(
        Integer,
        ForeignKey("lab_order_items.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    test_name = Column(String(255), nullable=False)
    numeric_value = Column(Float, nullable=True)
    text_value = Column(String(255), nullable=True)
    unit = Column(String(50), nullable=True)
    reference_range = Column(String(255), nullable=True)
    result_flag = Column(
        SQLEnum(ResultFlag),
        default=ResultFlag.NORMAL,
        nullable=False,
        index=True,
    )
    entered_by_user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    entered_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    verified_by_user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    verified_at = Column(DateTime, nullable=True)
    verification_notes = Column(Text, nullable=True)
    is_critical = Column(Boolean, default=False, nullable=False, index=True)

    # Relationships
    order_item = relationship("LabOrderItem", back_populates="result")
    entered_by = relationship("User", foreign_keys=[entered_by_user_id])
    verified_by = relationship("User", foreign_keys=[verified_by_user_id])


class LabAuditEvent(Base):
    """Immutable audit event log tracking all state mutations and critical alerts."""
    __tablename__ = "lab_audit_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    lab_order_id = Column(
        Integer,
        ForeignKey("lab_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action = Column(String(100), nullable=False, index=True)
    performed_by_user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    details = Column(Text, nullable=True)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    order = relationship("LabOrder", back_populates="audit_events")
    performed_by = relationship("User", foreign_keys=[performed_by_user_id])
