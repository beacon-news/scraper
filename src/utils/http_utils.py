from random import randint
from urllib import request

os_versions = [
  "(Windows NT 6.1; Win64; x64; rv:47.0)",
  "(Windows NT 10.0; Win64; x64)",
  "(X11; Linux x86_64)",
  "(Macintosh; Intel Mac OS X x.y; rv:42.0)",
  "(Macintosh; Intel Mac OS X 10.15; rv:77.0)",
  "(Macintosh; Intel Mac OS X 10_15_5)",
]

applewebkit_versions = [
  '605.1.15',
  '603.1.30',
  '605.1.15',
  '537.36',
  '532+',
  '531.9',
  '530.19.2',
  '528.4+',
  '528.18',
  '525.28.3'
]

chrome_versions = [
  '118.0.5993.89',
  '118.0.5993.88',
  '118.0.5993.80',
  '118.0.5993.92',
  '118.0.5993.65',
  '118.0.5993.69',
  '118.0.5993.70',
  '118.0.5993.71',
  '117.0.5938.157',
  '118.0.5993.58',
  '117.0.5938.153',
  '89.0.4389.82',
]

# all user agent headers are for Chrome browsers
def __get_random_ua_header() -> str:
  moz = "Mozilla/5.0"
  os = os_versions[randint(0, len(os_versions) - 1)]
  webkit = "AppleWebKit/" + applewebkit_versions[randint(0, len(applewebkit_versions) - 1)] + " (KHTML, like Gecko)"
  chrome = "Chrome/" + chrome_versions[randint(0, len(chrome_versions) - 1)]
  safari = "Safari/537.36"
  return f"{moz} {os} {webkit} {chrome} {safari}"

def create_request(url: str) -> request.Request:
  req = request.Request(url)
  req.add_header("User-Agent", __get_random_ua_header())
  return req