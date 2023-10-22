import os
import sys
sys.path.append(os.getcwd())

from src.features import download_user
from src.session import login
from src.settings import config

if __name__ == '__main__':
    #login(config.cookie[1])
    download_user(sys.argv[1])