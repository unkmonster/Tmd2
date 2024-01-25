import os
import sys
sys.path.append(os.getcwd())

from src.twitter.user import TwitterUser

if __name__ == '__main__':
    usr = TwitterUser(screen_name=sys.argv[1])
    print(usr._rest_id)
    print(usr._name)