import requests
from urllib3.util import Retry
from requests.adapters import HTTPAdapter

ses = requests.session()
retries = Retry(
    backoff_factor=0.1,
    status_forcelist=[502, 503, 504],
    status=10,
    connect=10
)
ses.mount('https://', HTTPAdapter(max_retries=retries))
