"""Initial migration.

Revision ID: initial_migration
Revises: 
Create Date: 2023-10-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'initial_migration'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('clothes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('image_filename', sa.String(length=300), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('upload_time', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('preference',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('style_text', sa.Text(), nullable=False),
    sa.Column('date', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('recommendation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('outfit_description', sa.Text(), nullable=False),
    sa.Column('reason', sa.Text(), nullable=False),
    sa.Column('generated_image', sa.String(length=300), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('recommendation')
    op.drop_table('preference')
    op.drop_table('clothes')
