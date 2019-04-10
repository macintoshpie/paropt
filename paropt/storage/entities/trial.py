from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.types import TIMESTAMP
from sqlalchemy.sql.expression import func


from .orm_base import ORMBase

class Trial(ORMBase):
  __tablename__ = 'trials'

  id = Column(Integer, primary_key=True)
  experiment_id = Column(Integer, ForeignKey('experiments.id'))
  run_number = Column(Integer)
  outcome = Column(Float)
  parameter_configs = relationship("ParameterConfig")
  timestamp = Column(TIMESTAMP, server_default=func.now(), onupdate=func.current_timestamp())
