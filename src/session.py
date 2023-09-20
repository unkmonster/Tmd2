import requests
import core
from api import Settings
from urllib3.util import Retry
from requests.adapters import HTTPAdapter
from logger import logger
from utility import raise_if_error
from exception import TWRequestError

ses = requests.session()
retries = Retry(
    backoff_factor=0.1,
    status_forcelist=[502, 503, 504],
    status=10,
    connect=10
)
ses.mount('https://', HTTPAdapter(max_retries=retries))
