"""create lab management tables

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-08-31 12:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd0e1f2a3b4c5'
down_revision: Union[str, None] = 'c9d0e1f2a3b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def ensure_enum(enum_name: str, values: list) -> None:
    bind = op.get_bind()
    if bind.engine.name == "postgresql":
        with op.get_context().autocommit_block():
            check_sql = sa.text("SELECT 1 FROM pg_type WHERE typname = :name")
            exists = bind.execute(check_sql, {"name": enum_name}).scalar()
            if not exists:
                vals_str = ", ".join(f"'{v}'" for v in values)
                bind.execute(sa.text(f"CREATE TYPE {enum_name} AS ENUM ({vals_str})"))


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    ensure_enum('laborderpriority', ['ROUTINE', 'URGENT', 'STAT'])
    ensure_enum('laborderstatus', ['ORDERED', 'SAMPLE_PENDING', 'SAMPLE_COLLECTED', 'IN_PROGRESS', 'RESULTS_ENTERED', 'VERIFIED', 'RELEASED', 'CANCELLED'])
    ensure_enum('samplecondition', ['ACCEPTABLE', 'HEMOLYZED', 'CLOTTED', 'INSUFFICIENT', 'CONTAMINATED'])
    ensure_enum('resultflag', ['NORMAL', 'LOW', 'HIGH', 'CRITICAL'])

    # 1. Create lab_tests table
    if 'lab_tests' not in tables:
        op.create_table(
            'lab_tests',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('test_name', sa.String(length=255), nullable=False),
            sa.Column('test_code', sa.String(length=50), nullable=False),
            sa.Column('category', sa.String(length=100), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('specimen_type', sa.String(length=100), nullable=False),
            sa.Column('reference_range', sa.String(length=255), nullable=True),
            sa.Column('unit', sa.String(length=50), nullable=True),
            sa.Column('preparation_instructions', sa.Text(), nullable=True),
            sa.Column('estimated_turnaround_time', sa.String(length=100), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_lab_tests_id'), 'lab_tests', ['id'], unique=False)
        op.create_index(op.f('ix_lab_tests_test_name'), 'lab_tests', ['test_name'], unique=False)
        op.create_index(op.f('ix_lab_tests_test_code'), 'lab_tests', ['test_code'], unique=True)
        op.create_index(op.f('ix_lab_tests_category'), 'lab_tests', ['category'], unique=False)
        op.create_index(op.f('ix_lab_tests_is_active'), 'lab_tests', ['is_active'], unique=False)

    # 2. Create lab_orders table
    if 'lab_orders' not in tables:
        op.create_table(
            'lab_orders',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('patient_id', sa.Integer(), nullable=False),
            sa.Column('doctor_id', sa.Integer(), nullable=False),
            sa.Column('clinical_notes', sa.Text(), nullable=True),
            sa.Column(
                'priority',
                sa.Enum('ROUTINE', 'URGENT', 'STAT', name='laborderpriority', create_type=False),
                nullable=False,
                server_default='ROUTINE',
            ),
            sa.Column(
                'status',
                sa.Enum(
                    'ORDERED',
                    'SAMPLE_PENDING',
                    'SAMPLE_COLLECTED',
                    'IN_PROGRESS',
                    'RESULTS_ENTERED',
                    'VERIFIED',
                    'RELEASED',
                    'CANCELLED',
                    name='laborderstatus',
                    create_type=False,
                ),
                nullable=False,
                server_default='ORDERED',
            ),
            sa.Column('ordered_at', sa.DateTime(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['doctor_id'], ['doctor_profiles.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['patient_id'], ['patient_profiles.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_lab_orders_id'), 'lab_orders', ['id'], unique=False)
        op.create_index(op.f('ix_lab_orders_patient_id'), 'lab_orders', ['patient_id'], unique=False)
        op.create_index(op.f('ix_lab_orders_doctor_id'), 'lab_orders', ['doctor_id'], unique=False)
        op.create_index(op.f('ix_lab_orders_priority'), 'lab_orders', ['priority'], unique=False)
        op.create_index(op.f('ix_lab_orders_status'), 'lab_orders', ['status'], unique=False)

    # 3. Create lab_order_items table
    if 'lab_order_items' not in tables:
        op.create_table(
            'lab_order_items',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('lab_order_id', sa.Integer(), nullable=False),
            sa.Column('lab_test_id', sa.Integer(), nullable=False),
            sa.Column('instructions', sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(['lab_order_id'], ['lab_orders.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['lab_test_id'], ['lab_tests.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_lab_order_items_id'), 'lab_order_items', ['id'], unique=False)
        op.create_index(op.f('ix_lab_order_items_lab_order_id'), 'lab_order_items', ['lab_order_id'], unique=False)
        op.create_index(op.f('ix_lab_order_items_lab_test_id'), 'lab_order_items', ['lab_test_id'], unique=False)

    # 4. Create lab_samples table
    if 'lab_samples' not in tables:
        op.create_table(
            'lab_samples',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('lab_order_id', sa.Integer(), nullable=False),
            sa.Column('technician_id', sa.Integer(), nullable=False),
            sa.Column('specimen_type', sa.String(length=100), nullable=False),
            sa.Column('collected_at', sa.DateTime(), nullable=False),
            sa.Column(
                'sample_condition',
                sa.Enum(
                    'ACCEPTABLE',
                    'HEMOLYZED',
                    'CLOTTED',
                    'INSUFFICIENT',
                    'CONTAMINATED',
                    name='samplecondition',
                    create_type=False,
                ),
                nullable=False,
                server_default='ACCEPTABLE',
            ),
            sa.Column('collection_notes', sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(['lab_order_id'], ['lab_orders.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['technician_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_lab_samples_id'), 'lab_samples', ['id'], unique=False)
        op.create_index(op.f('ix_lab_samples_lab_order_id'), 'lab_samples', ['lab_order_id'], unique=False)
        op.create_index(op.f('ix_lab_samples_technician_id'), 'lab_samples', ['technician_id'], unique=False)

    # 5. Create lab_results table
    if 'lab_results' not in tables:
        op.create_table(
            'lab_results',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('lab_order_item_id', sa.Integer(), nullable=False),
            sa.Column('test_name', sa.String(length=255), nullable=False),
            sa.Column('numeric_value', sa.Float(), nullable=True),
            sa.Column('text_value', sa.String(length=255), nullable=True),
            sa.Column('unit', sa.String(length=50), nullable=True),
            sa.Column('reference_range', sa.String(length=255), nullable=True),
            sa.Column(
                'result_flag',
                sa.Enum('NORMAL', 'LOW', 'HIGH', 'CRITICAL', name='resultflag', create_type=False),
                nullable=False,
                server_default='NORMAL',
            ),
            sa.Column('entered_by_user_id', sa.Integer(), nullable=False),
            sa.Column('entered_at', sa.DateTime(), nullable=False),
            sa.Column('verified_by_user_id', sa.Integer(), nullable=True),
            sa.Column('verified_at', sa.DateTime(), nullable=True),
            sa.Column('verification_notes', sa.Text(), nullable=True),
            sa.Column('is_critical', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.ForeignKeyConstraint(['entered_by_user_id'], ['users.id']),
            sa.ForeignKeyConstraint(['lab_order_item_id'], ['lab_order_items.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['verified_by_user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('lab_order_item_id'),
        )
        op.create_index(op.f('ix_lab_results_id'), 'lab_results', ['id'], unique=False)
        op.create_index(op.f('ix_lab_results_lab_order_item_id'), 'lab_results', ['lab_order_item_id'], unique=True)
        op.create_index(op.f('ix_lab_results_result_flag'), 'lab_results', ['result_flag'], unique=False)
        op.create_index(op.f('ix_lab_results_is_critical'), 'lab_results', ['is_critical'], unique=False)

    # 6. Create lab_audit_events table
    if 'lab_audit_events' not in tables:
        op.create_table(
            'lab_audit_events',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('lab_order_id', sa.Integer(), nullable=False),
            sa.Column('action', sa.String(length=100), nullable=False),
            sa.Column('performed_by_user_id', sa.Integer(), nullable=False),
            sa.Column('details', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['lab_order_id'], ['lab_orders.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['performed_by_user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_lab_audit_events_id'), 'lab_audit_events', ['id'], unique=False)
        op.create_index(op.f('ix_lab_audit_events_lab_order_id'), 'lab_audit_events', ['lab_order_id'], unique=False)
        op.create_index(op.f('ix_lab_audit_events_action'), 'lab_audit_events', ['action'], unique=False)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'lab_audit_events' in tables:
        op.drop_table('lab_audit_events')
    if 'lab_results' in tables:
        op.drop_table('lab_results')
    if 'lab_samples' in tables:
        op.drop_table('lab_samples')
    if 'lab_order_items' in tables:
        op.drop_table('lab_order_items')
    if 'lab_orders' in tables:
        op.drop_table('lab_orders')
    if 'lab_tests' in tables:
        op.drop_table('lab_tests')
