from datetime import datetime
from sys import argv

if __name__ == '__main__':
    exit(int(datetime.strptime(argv[1], argv[2]).timestamp()))