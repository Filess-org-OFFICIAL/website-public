"""empty message

Revision ID: 4a7f7e247d72
Revises: d018ca8fc831
Create Date: 2022-06-27 13:57:05.969490

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4a7f7e247d72'
down_revision = 'd018ca8fc831'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('plan', sa.Column('spent', sa.String(length=320), nullable=True))
    op.create_index(op.f('ix_plan_spent'), 'plan', ['spent'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_plan_spent'), table_name='plan')
    op.drop_column('plan', 'spent')
    # ### end Alembic commands ###