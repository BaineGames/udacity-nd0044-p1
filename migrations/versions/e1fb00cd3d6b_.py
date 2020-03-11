"""empty message

Revision ID: e1fb00cd3d6b
Revises: 
Create Date: 2020-03-10 17:30:00.438859

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e1fb00cd3d6b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('artist', sa.Column('seeking_description', sa.String(), nullable=True))
    op.add_column('artist', sa.Column('seeking_talent', sa.Boolean(), nullable=True))
    op.add_column('artist', sa.Column('website', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('artist', 'website')
    op.drop_column('artist', 'seeking_talent')
    op.drop_column('artist', 'seeking_description')
    # ### end Alembic commands ###
