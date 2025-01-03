# ckanext/regx/model.py

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from ckan.model.meta import metadata

Base = declarative_base(metadata=metadata)


class CompanyProfile(Base):
    """Database model for storing company profiles."""
    __tablename__ = 'company_profiles'

    id = sa.Column(sa.Integer, primary_key=True)
    company_name = sa.Column(sa.String, nullable=False)
    website = sa.Column(sa.String, nullable=False)
    address = sa.Column(sa.String, nullable=False)
    # Status field to track approval
    status = sa.Column(sa.String, default='Pending')
