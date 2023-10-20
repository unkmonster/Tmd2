import os
import sys
sys.path.append(os.getcwd())

from src.twitter.user import TwitterUser


usr = TwitterUser("XiaoGuai78666")
print(usr.rest_id)
print(usr.name)