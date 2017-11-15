
import logging
import logging.config
import yaml
import os


class LogSema4:

    def __init__(self):
        self.logconfig = None
        self.logger = logging.getLogger()


    def setup_logging(self):
        default_path = 'modules/logging.yaml'
        default_level = logging.INFO
        """Setup logging configuration"""
        path = default_path
        if os.path.exists(path):
            with open(path, 'rt') as f:
                config = yaml.safe_load(f.read())
            logging.config.dictConfig(config)
        else:
            logging.basicConfig(level=default_level)
