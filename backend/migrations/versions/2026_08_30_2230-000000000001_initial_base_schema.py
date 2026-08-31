"""initial_base_schema

Revision ID: 000000000001
Revises: 
Create Date: 2026-08-30 22:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '000000000001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('phone_number', sa.String(length=50), nullable=True),
        sa.Column('role', sa.Enum('PATIENT', 'DOCTOR', 'ADMIN', 'LAB_TECHNICIAN', 'PHARMACY_STAFF', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)

    # 2. patient_profiles table
    op.create_table(
        'patient_profiles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('gender', sa.String(length=20), nullable=True),
        sa.Column('blood_group', sa.String(length=10), nullable=True),
        sa.Column('allergies', sa.JSON(), nullable=True),
        sa.Column('chronic_conditions', sa.JSON(), nullable=True),
        sa.Column('emergency_contact', sa.String(length=100), nullable=True),
        sa.Column('medical_history_summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_patient_profiles_id'), 'patient_profiles', ['id'], unique=False)
    op.create_index(op.f('ix_patient_profiles_user_id'), 'patient_profiles', ['user_id'], unique=True)

    # 3. doctor_profiles table
    op.create_table(
        'doctor_profiles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('specialization', sa.String(length=100), nullable=False),
        sa.Column('license_number', sa.String(length=100), nullable=False),
        sa.Column('experience_years', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('hospital_affiliation', sa.String(length=255), nullable=True),
        sa.Column('consultation_fee', sa.Numeric(precision=10, scale=2), nullable=False, server_default=sa.text('0.00')),
        sa.Column('approval_status', sa.Enum('PENDING', 'APPROVED', 'REJECTED', name='doctorapprovalstatus'), nullable=False),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('license_number')
    )
    op.create_index(op.f('ix_doctor_profiles_id'), 'doctor_profiles', ['id'], unique=False)
    op.create_index(op.f('ix_doctor_profiles_user_id'), 'doctor_profiles', ['user_id'], unique=True)
    op.create_index(op.f('ix_doctor_profiles_specialization'), 'doctor_profiles', ['specialization'], unique=False)
    op.create_index(op.f('ix_doctor_profiles_approval_status'), 'doctor_profiles', ['approval_status'], unique=False)

    # 4. appointments table
    op.create_table(
        'appointments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('doctor_id', sa.Integer(), nullable=False),
        sa.Column('scheduled_start', sa.DateTime(), nullable=False),
        sa.Column('scheduled_end', sa.DateTime(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'CONFIRMED', 'CANCELLED', 'COMPLETED', 'REJECTED', name='appointmentstatus'), nullable=False),
        sa.Column('reason_for_visit', sa.Text(), nullable=True),
        sa.Column('patient_notes', sa.Text(), nullable=True),
        sa.Column('doctor_notes', sa.Text(), nullable=True),
        sa.Column('meeting_link', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['doctor_id'], ['doctor_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['patient_id'], ['patient_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_appointments_id'), 'appointments', ['id'], unique=False)
    op.create_index(op.f('ix_appointments_doctor_id'), 'appointments', ['doctor_id'], unique=False)
    op.create_index(op.f('ix_appointments_patient_id'), 'appointments', ['patient_id'], unique=False)
    op.create_index(op.f('ix_appointments_scheduled_start'), 'appointments', ['scheduled_start'], unique=False)
    op.create_index(op.f('ix_appointments_status'), 'appointments', ['status'], unique=False)

    # 5. prescriptions table
    op.create_table(
        'prescriptions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('doctor_id', sa.Integer(), nullable=False),
        sa.Column('appointment_id', sa.Integer(), nullable=True),
        sa.Column('diagnosis', sa.Text(), nullable=False),
        sa.Column('clinical_notes', sa.Text(), nullable=True),
        sa.Column('valid_until', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['doctor_id'], ['doctor_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['patient_id'], ['patient_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('appointment_id')
    )
    op.create_index(op.f('ix_prescriptions_id'), 'prescriptions', ['id'], unique=False)
    op.create_index(op.f('ix_prescriptions_doctor_id'), 'prescriptions', ['doctor_id'], unique=False)
    op.create_index(op.f('ix_prescriptions_patient_id'), 'prescriptions', ['patient_id'], unique=False)

    # 6. prescription_items table
    op.create_table(
        'prescription_items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('prescription_id', sa.Integer(), nullable=False),
        sa.Column('medication_name', sa.String(length=200), nullable=True),
        sa.Column('drug_name', sa.String(length=200), nullable=True),
        sa.Column('dosage', sa.String(length=100), nullable=False),
        sa.Column('frequency', sa.String(length=100), nullable=False),
        sa.Column('duration', sa.String(length=100), nullable=False),
        sa.Column('instructions', sa.Text(), nullable=True),
        sa.Column('route_of_administration', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['prescription_id'], ['prescriptions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_prescription_items_id'), 'prescription_items', ['id'], unique=False)
    op.create_index(op.f('ix_prescription_items_medication_name'), 'prescription_items', ['medication_name'], unique=False)
    op.create_index(op.f('ix_prescription_items_drug_name'), 'prescription_items', ['drug_name'], unique=False)
    op.create_index(op.f('ix_prescription_items_prescription_id'), 'prescription_items', ['prescription_id'], unique=False)

    # 7. ai_analysis_reports table
    op.create_table(
        'ai_analysis_reports',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('prescription_id', sa.Integer(), nullable=True),
        sa.Column('analyzed_by_user_id', sa.Integer(), nullable=True),
        sa.Column('overall_risk_level', sa.Enum('NONE', 'LOW', 'MODERATE', 'HIGH', 'CRITICAL', name='interactionseverity'), nullable=False),
        sa.Column('clinical_summary', sa.Text(), nullable=False),
        sa.Column('ai_recommendations', sa.Text(), nullable=True),
        sa.Column('drug_drug_interactions', sa.JSON(), nullable=True),
        sa.Column('drug_food_interactions', sa.JSON(), nullable=True),
        sa.Column('drug_allergy_interactions', sa.JSON(), nullable=True),
        sa.Column('raw_ai_response', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['analyzed_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['prescription_id'], ['prescriptions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_analysis_reports_id'), 'ai_analysis_reports', ['id'], unique=False)
    op.create_index(op.f('ix_ai_analysis_reports_overall_risk_level'), 'ai_analysis_reports', ['overall_risk_level'], unique=False)
    op.create_index(op.f('ix_ai_analysis_reports_prescription_id'), 'ai_analysis_reports', ['prescription_id'], unique=False)


def downgrade() -> None:
    op.drop_table('ai_analysis_reports')
    op.drop_table('prescription_items')
    op.drop_table('prescriptions')
    op.drop_table('appointments')
    op.drop_table('doctor_profiles')
    op.drop_table('patient_profiles')
    op.drop_table('users')
