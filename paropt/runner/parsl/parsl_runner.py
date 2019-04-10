import logging
import os
import time
import traceback
from string import Template

import parsl

from paropt import setFileLogger

logger = logging.getLogger(__name__)

class ParslRunner:
  def __init__(self, experiment, parsl_config, parsl_app, optimizer, storage):
    self.experiment = experiment
    self.parsl_config = parsl_config
    self.parsl_app = parsl_app
    self.command = experiment.command_template_string
    self.optimizer = optimizer
    self.storage = storage

    # setup paropt info directories
    self.paropt_dir = f'./optinfo'
    if not os.path.exists(self.paropt_dir):
      os.mkdir(self.paropt_dir)

    run_number = 0
    run_dir = f'{self.paropt_dir}/{run_number:03}'
    while os.path.exists(run_dir):
      run_number += 1
      run_dir = f'{self.paropt_dir}/{run_number:03}'
    self.run_dir = run_dir
    os.mkdir(self.run_dir)

    self.templated_scripts_dir = f'{self.run_dir}/templated_scripts'
    os.mkdir(self.templated_scripts_dir)

    setFileLogger(f'{self.run_dir}/paropt.log')

  def _validateResult(self, params, res):
    if res[0] != 0:
      raise Exception("NON_ZERO_EXIT:\n  PARAMS: {}\n  OUT: {}".format(params, res[1]))

  def _writeScript(self, params):
    script = Template(self.command).safe_substitute(params)
    script_path = f'{self.templated_scripts_dir}/timeScript_{self.experiment.tool_name}_{int(time.time())}.sh'
    with open(script_path, "w") as f:
      f.write(script)
    return script_path, script
  
  def run(self, debug=False):
    if debug:
      parsl.set_stream_logger()
    parsl.load(self.parsl_config)
    try:
      for config in self.optimizer:
        logger.info(f'Writing script with config {config}')
        script_path, script_content = self._writeScript(config)
        # TODO: add user hook for customization
        # Hook should take in tool param configuration and current parsl configuration as arguments
        # Hook should return a new parsl configuration if it needs to be changed, or None if not
        # self.prerun_hook(config, self.parsl_config)
        logger.info(f'Running script {script_path}')
        result = self.parsl_app(script_content).result()
        self._validateResult(config, result)
        self.storage.saveResult(config, result)
        self.optimizer.register(config, result)
    except Exception as e:
      logger.info('Whoops, something went wrong... {e}')
      logger.exception(traceback.format_exc())
    logger.info('Exiting program')
  
  def getMax(self):
    return self.optimizer.getMax()
