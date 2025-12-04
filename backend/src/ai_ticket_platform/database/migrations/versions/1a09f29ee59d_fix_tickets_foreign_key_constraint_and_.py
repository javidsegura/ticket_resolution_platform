"""fix tickets foreign key constraint and updated_at column

Revision ID: 1a09f29ee59d
Revises: 78ab650fd335
Create Date: 2025-11-20 20:39:48.892062

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "1a09f29ee59d"
down_revision: Union[str, Sequence[str], None] = "78ab650fd335"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
	op.drop_constraint(op.f("tickets_ibfk_1"), "tickets", type_="foreignkey")
	op.create_foreign_key(
		"fk_tickets_intent_id",
		"tickets",
		"intents",
		["intent_id"],
		["id"],
		ondelete="SET NULL",
	)

	op.execute(
		"UPDATE tickets SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL"
	)
	op.execute(
		"ALTER TABLE tickets "
		"MODIFY updated_at DATETIME NOT NULL "
		"DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
	)
	# ### end Alembic commands ###


def downgrade() -> None:
	op.execute(
		"ALTER TABLE tickets MODIFY updated_at DATETIME NULL DEFAULT CURRENT_TIMESTAMP"
	)

	op.drop_constraint("fk_tickets_intent_id", "tickets", type_="foreignkey")
	op.create_foreign_key(
		op.f("tickets_ibfk_1"),
		"tickets",
		"intents",
		["intent_id"],
		["id"],
	)
	# ### end Alembic commands ###
