"""store raw bytes

Revision ID: 4e1378c97a67
Revises: 2e0600ea20c0
Create Date: 2022-03-30 22:20:56.251049

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4e1378c97a67'
down_revision = '2e0600ea20c0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_files_fileSize', table_name='files')
    op.drop_column('files', 'fileSize')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('files', sa.Column('fileSize', sa.VARCHAR(length=320), nullable=True))
    op.create_index('ix_files_fileSize', 'files', ['fileSize'], unique=False)
    # ### end Alembic commands ###
