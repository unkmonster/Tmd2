import os
import sys
sys.path.append(os.getcwd())

from src.features import *
#from src.utils.utility import get_following

download_following(TwitterUser(screen_name='menghubaobao'))
pass