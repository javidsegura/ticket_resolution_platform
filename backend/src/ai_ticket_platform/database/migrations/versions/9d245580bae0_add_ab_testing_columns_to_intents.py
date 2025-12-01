"""add ab testing columns to intents

Revision ID: 9d245580bae0
Revises: 1a09f29ee59d
Create Date: 2025-01-27 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9d245580bae0"
down_revision: Union[str, Sequence[str], None] = "1a09f29ee59d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
	"""Upgrade schema."""
	op.add_column(
		"intents",
		sa.Column(
			"variant_a_impressions", sa.Integer(), nullable=False, server_default="0"
		),
	)
	op.add_column(
		"intents",
		sa.Column(
			"variant_b_impressions", sa.Integer(), nullable=False, server_default="0"
		),
	)
	op.add_column(
		"intents",
		sa.Column(
			"variant_a_resolutions", sa.Integer(), nullable=False, server_default="0"
		),
	)
	op.add_column(
		"intents",
		sa.Column(
			"variant_b_resolutions", sa.Integer(), nullable=False, server_default="0"
		),
	)


def downgrade() -> None:
	"""Downgrade schema."""
	op.drop_column("intents", "variant_b_resolutions")
	op.drop_column("intents", "variant_a_resolutions")
	op.drop_column("intents", "variant_b_impressions")
	op.drop_column("intents", "variant_a_impressions")
