"""update settlement ref_transaction_id

Revision ID: 2fe174056924
Revises: d0e607783484
Create Date: 2025-12-29 21:42:40.016042

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2fe174056924'
down_revision: Union[str, None] = 'd0e607783484'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -------------------------------------------------------
    # 1. ENUM UPDATES (SAFE: only ADD / CONVERT)
    # -------------------------------------------------------

    # bookingstatus enum
    op.execute("ALTER TYPE bookingstatus ADD VALUE IF NOT EXISTS 'Verified'")

    # casestatus enum
    op.execute("ALTER TYPE casestatus ADD VALUE IF NOT EXISTS 'Resolved'")

    # prescriptionstatus enum (if needed)
    # op.execute("ALTER TYPE prescriptionstatus ADD VALUE IF NOT EXISTS 'Partially_Dispensed'")


    # -------------------------------------------------------
    # 2. SERVICE_BUNDLE FIX (IMPORTANT)
    # -------------------------------------------------------

    # Add soft-delete column
    op.add_column(
        'service_bundle',
        sa.Column('is_deleted', sa.Boolean(), nullable=True)
    )

    # Create new enum if it doesn't exist
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_type WHERE typname = 'bundlestatus'
            ) THEN
                CREATE TYPE bundlestatus AS ENUM ('Active', 'Suspended');
            END IF;
        END$$;
    """)

    # Convert old servicetype values → bundlestatus
    op.execute("""
        ALTER TABLE service_bundle
        ALTER COLUMN bundle_type TYPE bundlestatus
        USING
            CASE
                WHEN bundle_type IN (
                    'Laboratory',
                    'Administration',
                    'Consultation',
                    'Appointment',
                    'Enrollment'
                )
                THEN 'Active'::bundlestatus
                ELSE 'Suspended'::bundlestatus
            END
    """)


    # -------------------------------------------------------
    # 3. REFERRED TRANSACTION SETTLEMENT
    # -------------------------------------------------------

    # Add commission column
    op.add_column(
        'referred_transaction_settlement',
        sa.Column('commission', sa.Float(), nullable=True)
    )

    # Fix ref_transaction_id type + FK
    op.drop_constraint(
        'referred_transaction_settlement_detail_ref_transaction_id_fkey',
        'referred_transaction_settlement_detail',
        type_='foreignkey'
    )

    op.alter_column(
        'referred_transaction_settlement_detail',
        'ref_transaction_id',
        type_=sa.BigInteger(),
        postgresql_using='ref_transaction_id::bigint'
    )

    op.create_foreign_key(
        'fk_settlement_detail_transaction',
        'referred_transaction_settlement_detail',
        'transaction',
        ['ref_transaction_id'],
        ['id'],
        ondelete='CASCADE'
    )


    # -------------------------------------------------------
    # 4. SERVICE BOOKING SAFETY
    # -------------------------------------------------------

    # Ensure transaction_id is BIGINT and unique
    op.alter_column(
        'service_booking',
        'transaction_id',
        existing_type=sa.BigInteger(),
        nullable=False
    )

    op.create_unique_constraint(
        'uq_service_booking_transaction_id',
        'service_booking',
        ['transaction_id']
    )


def downgrade() -> None:
    # -------------------------------------------------------
    # 1. SERVICE_BOOKING (reverse constraints safely)
    # -------------------------------------------------------

    op.drop_constraint(
        'uq_service_booking_transaction_id',
        'service_booking',
        type_='unique'
    )

    op.alter_column(
        'service_booking',
        'transaction_id',
        existing_type=sa.BigInteger(),
        nullable=True
    )


    # -------------------------------------------------------
    # 2. REFERRED TRANSACTION SETTLEMENT
    # -------------------------------------------------------

    # Drop FK to transaction
    op.drop_constraint(
        'fk_settlement_detail_transaction',
        'referred_transaction_settlement_detail',
        type_='foreignkey'
    )

    # Revert ref_transaction_id to INTEGER
    op.alter_column(
        'referred_transaction_settlement_detail',
        'ref_transaction_id',
        type_=sa.Integer(),
        postgresql_using='ref_transaction_id::integer'
    )

    # Restore original FK (adjust table name if needed)
    op.create_foreign_key(
        'referred_transaction_settlement_detail_ref_transaction_id_fkey',
        'referred_transaction_settlement_detail',
        'referred_transaction',
        ['ref_transaction_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # Remove commission column
    op.drop_column(
        'referred_transaction_settlement',
        'commission'
    )


    # -------------------------------------------------------
    # 3. SERVICE_BUNDLE (CRITICAL PART)
    # -------------------------------------------------------

    # Re-create old servicetype enum if missing
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_type WHERE typname = 'servicetype'
            ) THEN
                CREATE TYPE servicetype AS ENUM (
                    'Laboratory',
                    'Administration',
                    'Consultation',
                    'Appointment',
                    'Enrollment'
                );
            END IF;
        END$$;
    """)

    # Convert bundlestatus → servicetype
    op.execute("""
        ALTER TABLE service_bundle
        ALTER COLUMN bundle_type TYPE servicetype
        USING
            CASE
                WHEN bundle_type = 'Active'
                THEN 'Laboratory'::servicetype
                ELSE 'Administration'::servicetype
            END
    """)

    # Drop soft-delete column
    op.drop_column(
        'service_bundle',
        'is_deleted'
    )


    # -------------------------------------------------------
    # 4. ENUM STATUS VALUES (NO-OP BY DESIGN)
    # -------------------------------------------------------
    # Postgres does NOT allow removing enum values safely.
    # Values like 'Verified' and 'Resolved' are left in place intentionally.
    # This is standard and safe practice.

