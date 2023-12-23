import logging
import os
from datetime import date
import sys
from src.settings import project

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
        newrecord = record
        newrecord.levelname = ColoredFormatter.color_format.format(ColoredFormatter.color[record.levelname], record.levelname)
        return logging.Formatter.format(self, newrecord)
    pass


class MyHandler(logging.StreamHandler):
    def __init__(self, stream=None):
        super().__init__(stream)

    def emit(self, record):
        try:
            msg = self.format(record)
            print(msg)
        except RecursionError:  # See issue 36272
            raise
        except Exception:
            self.handleError(record)
        pass


# create logger
logger = logging.getLogger("rich")
logger.setLevel(logging.DEBUG)

# create handler
today = date.today().strftime('%Y-%m')
log_path = project.logs_dir.joinpath('{}.log'.format(today))

sh = MyHandler(sys.stdout)
fh = logging.FileHandler(log_path, 'a', 'utf-8')

# create formatter
file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
con_formatter = ColoredFormatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# add formatter and filter to handler
sh.setFormatter(con_formatter)
fh.setFormatter(file_formatter)

fh.addFilter(lambda record: record.levelno >= logging.INFO)

# add handler to 
logger.addHandler(fh)
logger.addHandler(sh)

# 'application' code
#print('-----Logger initlalized-----')
# logger.info('Logger initialized')
# logger.info('Created {}'.format(log_dir))
