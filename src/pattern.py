import re

url = re.compile(r'(https?|ftp|file)://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]')
at = re.compile(r'@\S+\s')
tag = re.compile(r'#\S+\s')
enter = re.compile(r'\r|\n\r?')
nonsupport = re.compile(r'[/\\:*?"<>\|]')