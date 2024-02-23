import os
import sys
sys.path.append(os.getcwd())

from src.features import *
#from src.utils.utility import get_following

if __name__ == '__main__':
    download_following(TwitterUser(screen_name=sys.argv[1]))
    pass