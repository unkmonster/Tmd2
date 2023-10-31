import os
import sys
sys.path.append(os.getcwd())

from src.features import download_user

if __name__ == '__main__':
    #login(config.cookie[1])
    download_user('xiaoxiuzaizi')