"""Initial complete migration.

Revision ID: a1b2c3d4e5f6
Revises: 
Create Date: 2023-10-05 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=120), unique=True, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False)
    )
    op.create_table(
        'clothes',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('image_filename', sa.String(length=300), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('upload_time', sa.DateTime, server_default=sa.func.now(), nullable=False)
    )
    op.create_table(
        'preference',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('style_text', sa.Text, nullable=False),
        sa.Column('date', sa.DateTime, server_default=sa.func.now(), nullable=False)
    )
    op.create_table(
        'recommendation',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('outfit_description', sa.Text, nullable=False),
        sa.Column('reason', sa.Text, nullable=False),
        sa.Column('generated_image', sa.String(length=300), nullable=True),
        sa.Column('timestamp', sa.DateTime, server_default=sa.func.now(), nullable=False)
    )


def downgrade():
    op.drop_table('recommendation')
    op.drop_table('preference')
    op.drop_table('clothes')
    op.drop_table('users')
