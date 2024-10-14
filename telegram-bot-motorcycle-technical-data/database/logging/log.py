import os

from loguru import logger


current_dir = os.path.dirname(os.path.abspath(__file__))
active_dir = 'log_history'
log_file_path = os.path.join(current_dir, active_dir, '{time}_log.log')
logger.add(log_file_path,
           level="DEBUG",
           rotation="10 MB",
           retention="7 days")
