import os
import sys
sys.path.append(os.getcwd())

from src.features import download_user

if __name__ == '__main__':
    try:
        download_user(sys.argv[1])
    except RuntimeError as err:
        print(*err.args)