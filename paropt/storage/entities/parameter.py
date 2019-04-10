from sqlalchemy import Column, Integer, Numeric, String, ForeignKey
from sqlalchemy.orm import relationship, backref

from .orm_base import ORMBase

class Parameter(ORMBase):
  __tablename__ = 'parameters'

  id = Column(Integer, primary_key=True)
  name = Column(String)
  minimum = Column(Integer)
  maximum = Column(Integer)
  experiment_id = Column(Integer, ForeignKey('experiments.id'))

  @staticmethod
  def parametersToDict(parameterList):
    return {param.name: [param.minimum, param.maximum] for param in parameterList}
