import os
import logging

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.sql.expression import func

from .entities.orm_base import create_all
from .storage_base import StorageBase
from .entities.trial import Trial
from .entities.parameter_config import ParameterConfig
from .entities.parameter import Parameter
from .entities.experiment import Experiment

logger = logging.getLogger(__name__)

class RelationalDB(StorageBase):
  def __init__(self, dialect, username, password, host_url, dbname, experiment=None, experiment_id=None):
    self.dialect = dialect
    self.username = username
    self.password = password
    self.host_url = host_url
    self.dbname = dbname
    self.engine_url = f'{dialect}://{username}:{password}@{host_url}/{dbname}'

    self.initialized = False
    self.engine = create_engine(self.engine_url)
    self.Session = sessionmaker(bind=self.engine)

    self.experiment = experiment
    self.experiment_id = experiment_id
    self.run_number = -1

    # setup the database
    self._setup()
  
  def _getNextRunNumber(self, session):
    if not self.initialized:
      self._setup()
    
    max_trial = session.query(func.max(Trial.run_number)) \
      .filter(Trial.experiment_id == self.experiment_id) \
      .first()
    max_run_number = max_trial[0]
    if max_run_number == None:
      return 0
    return max_run_number + 1
  
  def _setup(self):
    # initialize database
    logger.info(f'Setting up db engine')
    # create database if it doesn't exist
    if not database_exists(self.engine.url):
      create_database(self.engine.url)
    create_all(self.engine)
    self.initialized = True

    # create a new experiment or fetch it
    session = self.Session()
    if self.experiment != None:
      self._createExperiment(session)
    elif self.experiment_id != None:
      experiment = session.query(Experiment) \
        .filter(Experiment.id == self.experiment_id) \
        .first()
      if experiment != None:
        self.experiment = experiment
      else:
        raise Exception("Unable to find experiment with id {}".format(self.experiment_id))
    else:
      raise Exception("Must provide an experiment id or object to construct a new experiment")

    # get next run number
    self.run_number = self._getNextRunNumber(session)
  
  def _createExperiment(self, session=None):
    if not self.initialized:
      self._setup()
      return

    if not isinstance(self.experiment, Experiment):
      raise Exception("Invalid experiment; expected it to be instance of Experiment")
    
    logger.info("Creating Experiment {}".format(self.experiment))
    session.add(self.experiment)
    session.commit()
    self.experiment_id = self.experiment.id
  
  def _putParameter(self, session, parameter_name, minimum, maximum):
    if not self.initialized:
      self._setup()

    param = session.query(Parameter).filter(Parameter.name == parameter_name).first()
    if None == param:
      logger.info(f'Creating Parameter {parameter_name} to database')
      param = Parameter(name=parameter_name, minimum=minimum, maximum=maximum)
      session.add(param)
      session.commit()
    return param

  def saveResult(self, param_configs, result):
    if not self.initialized:
      self._setup()
    
    session = self.Session()
    param_config_objs = []
    for pc_name in param_configs:
      # get parameter from database
      # TODO: this should also filter using experiment...
      param = session.query(Parameter) \
        .filter(Parameter.name == pc_name) \
        .filter(Parameter.experiment_id == self.experiment_id) \
        .first()
      if param == None:
        raise Exception(f'Unable to find parameter: {pc_name}')
      new_config = ParameterConfig(parameter=param, value=param_configs[pc_name])
      param_config_objs.append(new_config)
    
    session.add_all(param_config_objs)
    trial = Trial(
      outcome=result[2],
      parameter_configs=param_config_objs,
      run_number=self.run_number,
      experiment_id=self.experiment_id
    )
    logger.info(f'Saving trial to database: {trial}')
    session.add(trial)
    session.commit()
  
  def getPreviousTrials(self):
    if not self.initialized:
      self._setup()

    session = self.Session()
    all_results = session.query(Trial) \
      .filter(Trial.run_number < self.run_number) \
      .filter(Trial.experiment_id == self.experiment_id) \
      .join(ParameterConfig, Trial.parameter_configs) \
      .join(Parameter, ParameterConfig.parameter) \
      .all()
    
    return all_results
  
  def getPreviousTrialsList(self):
    prev_trials = self.getPreviousTrials()
    return Trial.trialsToDicts(prev_trials)
  
  def getExperiment(self):
    if not self.initialized:
      self._setup()

    session = self.Session()
    experiment = session.query(Experiment) \
      .filter(Experiment.id == self.experiment_id) \
      .first()

    return experiment
  
  def getParameters(self):
    session = self.Session()
    parameters = session.query(Parameter) \
      .filter(Parameter.experiment_id == self.experiment_id) \
      .all()
    
    return parameters
  
  def getParametersDict(self):
    parameters = self.getParameters()
    return Parameter.parametersToDict(parameters)
