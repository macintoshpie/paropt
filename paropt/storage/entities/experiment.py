from sqlalchemy import Column, Integer, Float, String, ForeignKey
from sqlalchemy.orm import relationship, backref

from .orm_base import ORMBase

class Experiment(ORMBase):
  __tablename__ = 'experiments'

  id = Column(Integer, primary_key=True)
  # TODO: replace these string cols with relationships to entities
  tool_name = Column(String)
  command_template_string = Column(String)
  parameters = relationship("Parameter")
  trials = relationship("Trial")