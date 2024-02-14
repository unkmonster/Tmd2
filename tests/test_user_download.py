import os
import sys
sys.path.append(os.getcwd())

from src.features import download_user
import time

if __name__ == '__main__':
    try:
        begin = time.time()
        download_user(sys.argv[1])
        print(time.time() - begin)
    except RuntimeError as err:
        print(*err.args)