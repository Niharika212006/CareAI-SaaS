"""Pydantic schemas for the Lab Management and Diagnostic Workflow."""
import json
from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.lab import (
    LabOrderPriority,
    LabOrderStatus,
    SampleCondition,
    ResultFlag,
)


# --- Lab Test Catalog Schemas ---

class LabTestBase(BaseModel):
    test_name: str = Field(..., min_length=2, max_length=255)
    test_code: str = Field(..., min_length=2, max_length=50)
    category: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    specimen_type: str = Field(..., min_length=2, max_length=100)
    reference_range: Optional[str] = None
    unit: Optional[str] = None
    preparation_instructions: Optional[str] = None
    estimated_turnaround_time: Optional[str] = None
    is_active: bool = True


class LabTestCreate(LabTestBase):
    pass


class LabTestUpdate(BaseModel):
    test_name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    specimen_type: Optional[str] = None
    reference_range: Optional[str] = None
    unit: Optional[str] = None
    preparation_instructions: Optional[str] = None
    estimated_turnaround_time: Optional[str] = None
    is_active: Optional[bool] = None


class LabTestRead(LabTestBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Lab Sample Schemas ---

class LabSampleCreate(BaseModel):
    specimen_type: str
    sample_condition: SampleCondition = SampleCondition.ACCEPTABLE
    collection_notes: Optional[str] = None


class LabSampleRead(BaseModel):
    id: int
    lab_order_id: int
    technician_id: int
    technician_name: Optional[str] = None
    specimen_type: str
    collected_at: datetime
    sample_condition: SampleCondition
    collection_notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# --- Lab Result Schemas ---

class LabResultCreateItem(BaseModel):
    lab_order_item_id: int
    numeric_value: Optional[float] = None
    text_value: Optional[str] = None
    unit: Optional[str] = None
    reference_range: Optional[str] = None


class LabResultBatchCreate(BaseModel):
    results: List[LabResultCreateItem] = Field(..., min_length=1)


class LabResultRead(BaseModel):
    id: int
    lab_order_item_id: int
    test_name: str
    numeric_value: Optional[float] = None
    text_value: Optional[str] = None
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    result_flag: ResultFlag
    entered_by_user_id: int
    entered_by_name: Optional[str] = None
    entered_at: datetime
    verified_by_user_id: Optional[int] = None
    verified_by_name: Optional[str] = None
    verified_at: Optional[datetime] = None
    verification_notes: Optional[str] = None
    is_critical: bool

    model_config = ConfigDict(from_attributes=True)


class LabVerificationRequest(BaseModel):
    verification_notes: Optional[str] = None


# --- Lab Order Item & Order Schemas ---

class LabOrderItemCreate(BaseModel):
    lab_test_id: int
    instructions: Optional[str] = None


class LabOrderItemRead(BaseModel):
    id: int
    lab_order_id: int
    lab_test_id: int
    test: LabTestRead
    instructions: Optional[str] = None
    result: Optional[LabResultRead] = None

    model_config = ConfigDict(from_attributes=True)


class LabOrderCreate(BaseModel):
    patient_id: int = Field(..., description="Target patient profile ID or user ID")
    items: List[LabOrderItemCreate] = Field(..., min_length=1, description="List of lab tests to order")
    priority: LabOrderPriority = LabOrderPriority.ROUTINE
    clinical_notes: Optional[str] = None


class LabAuditEventRead(BaseModel):
    id: int
    lab_order_id: int
    action: str
    performed_by_user_id: int
    performed_by_name: Optional[str] = None
    details: Optional[Any] = None

    @field_validator("details", mode="before")
    @classmethod
    def format_details(cls, v):
        if isinstance(v, dict):
            return v.get("message") or json.dumps(v)
        return v

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LabOrderSummary(BaseModel):
    id: int
    patient_id: int
    patient_name: str
    doctor_id: int
    doctor_name: str
    priority: LabOrderPriority
    status: LabOrderStatus
    test_count: int
    test_names: List[str]
    is_critical_flagged: bool = False
    ordered_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LabOrderRead(BaseModel):
    id: int
    patient_id: int
    patient_name: str
    doctor_id: int
    doctor_name: str
    clinical_notes: Optional[str] = None
    priority: LabOrderPriority
    status: LabOrderStatus
    ordered_at: datetime
    updated_at: datetime
    items: List[LabOrderItemRead] = []
    samples: List[LabSampleRead] = []
    audit_events: List[LabAuditEventRead] = []

    model_config = ConfigDict(from_attributes=True)


# --- Patient Released Report Schemas ---

class PatientReleasedItemRead(BaseModel):
    test_name: str
    category: str
    numeric_value: Optional[float] = None
    text_value: Optional[str] = None
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    result_flag: ResultFlag
    is_critical: bool


class PatientReleasedLabReportRead(BaseModel):
    id: int
    doctor_name: str
    doctor_specialization: Optional[str] = None
    priority: LabOrderPriority
    status: LabOrderStatus
    ordered_at: datetime
    released_at: Optional[datetime] = None
    verified_by_name: Optional[str] = None
    results: List[PatientReleasedItemRead] = []


# --- Statistics & Dashboard Schemas ---

class LabQueueStats(BaseModel):
    pending_samples: int = 0
    samples_collected_today: int = 0
    tests_in_progress: int = 0
    results_awaiting_verification: int = 0
    completed_tests_today: int = 0
    critical_alerts_count: int = 0


class LabAdminStats(BaseModel):
    total_orders_all_time: int = 0
    tests_pending_processing: int = 0
    orders_completed_today: int = 0
    total_critical_events: int = 0
    active_test_catalog_count: int = 0
