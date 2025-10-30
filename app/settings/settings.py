import logging
import os
import sys
from dotenv import load_dotenv
from pydantic import ValidationError
from settings.env_configs_models import Settings
from settings.logging_c_formatter import CustomFormatter


env_paths = ['..', '']
debug_mode_flags = [1, True, 'true', 'True', '1', None]

for _p in env_paths:
    base_path = os.path.join(_p, '.env')
    if os.path.exists(base_path):
        with open(os.path.join(base_path), 'r') as file:
            load_dotenv(stream=file)
        break

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)  # дефолтный уровень логирования

for _h in root_logger.handlers:
    root_logger.removeHandler(_h)
logging.getLogger('botocore').setLevel(logging.WARNING)

# логи в консоль
consoleHandler = logging.StreamHandler(stream=sys.stdout)
consoleHandler.setFormatter(CustomFormatter())
root_logger.addHandler(consoleHandler)

debug = os.environ.get('DEBUG_MODE') in debug_mode_flags
root_logger.info(f'Starting in {"debug" if debug else "production"} mode')
logging.getLogger('botocore').setLevel(logging.WARNING)
current_logger = logging.getLogger(__name__)

try:
    settings = Settings(**os.environ)
except ValidationError as e:
    current_logger.critical(exc_info=e, msg='Env parameters validation error')
    sys.exit(-1)
