import os
import sys
sys.path.append(os.getcwd())

from src.twitter.user import TwitterUser
from src.twitter.list import TwitterList

def download_user(screen_name: str, save_to = "other"):
    local = TwitterList(-1, save_to, -1)
    usr = TwitterUser(screen_name, local)
    usr.download()

download_user("XiaoGuai78666")