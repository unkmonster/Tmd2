import logging
import os
from datetime import date

class ColoredFormatter(logging.Formatter):
    color = {
        "DEBUG": 94,
        "INFO": 92,
        "WARNING": 93,
        "ERROR": 91 
    }
    color_format = "\x1b[{}m{}\x1b[0m"

    def __init__(self, fmt, datefmt):
        super().__init__(fmt, datefmt)

    def format(self, record):
        record.levelname = ColoredFormatter.color_format.format(ColoredFormatter.color[record.levelname], record.levelname)
        return logging.Formatter.format(self, record)
    pass

# create floder
dir = os.getenv('appdata') + '\\Tmd2'
if not os.path.exists(dir):
    os.mkdir(dir)
if not os.path.exists(dir + '\\log'):
    os.mkdir(dir + '\\log')

# create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# create handler
today = date.today().strftime('%Y-%m-%d')
log_path = f"{dir}\\log\\{today}.log"

sh = logging.StreamHandler()
fh = logging.FileHandler(log_path, 'a', 'utf-8')

# create formatter
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %I:%M:%S')
con_formatter = ColoredFormatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %I:%M:%S')

# add formatter to handler
sh.setFormatter(con_formatter)
fh.setFormatter(formatter)

# add handler to logger
logger.addHandler(sh)
logger.addHandler(fh)

logger.info("hello")
logger.warning("hello")
logger.debug("debug")
logger.error("error")
# 'application' code
#print('-----Logger initlalized-----')
# logger.info('Logger initialized')
# logger.info('Created {}'.format(log_dir))
