import logging.config
import warnings
from ast import literal_eval
from configparser import ConfigParser
from pathlib import Path

import pkg_resources


def _read_config(path) -> dict:
    parser = ConfigParser()
    parser.read(path)
    config = {}
    for section in parser.sections():
        typed_config = [(key, literal_eval(val)) for key, val in parser.items(section)]
        config.update(dict(typed_config))
    return config


# Logging config
logging_config = pkg_resources.resource_filename(__name__, str(Path('config/logging.ini')))
logging.config.fileConfig(logging_config, disable_existing_loggers=False)

# App config
app_config_path = pkg_resources.resource_filename(__name__, str(Path('config/app.ini')))
settings = _read_config(app_config_path)

# Ignore warnings from Torch
warnings.filterwarnings("ignore")
