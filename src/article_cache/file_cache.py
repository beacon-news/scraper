from datetime import datetime, timedelta
import json
from pathlib import Path
from article_cache import ArticleCache

class FileArticleCache(ArticleCache):

  def __init__(self, cache_file_path: str):
    self.__cache_file_path = cache_file_path
    self.__cache = {} 
    self.__create_cache_file()
    self.__load_cache()
    # prune old entries
    self.__recreate_cache()
  
  def __create_cache_file(self):
    file = Path(self.__cache_file_path)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.touch(exist_ok=True)

  def __load_cache(self):
    with open(self.__cache_file_path, "r") as f:
      for line in f:
        url, exp_date = self.__parse_line(line)
        self.__cache[url] = exp_date 
  
  def __parse_line(self, line: str) -> tuple[str, str]:
    try:
      d = json.loads(line)
      return d["url"], datetime.fromisoformat(d["expiration_date"])
    except json.decoder.JSONDecodeError as e:
      raise ValueError(f"Invalid cache file: {self.__cache_file_path}, json decoder error at line {line}, json error: {e}")
    except KeyError as e:
      raise ValueError(f"Invalid cache file: {self.__cache_file_path}, key {e.args} not found in line {line}")

  def contains(self, article_url: str) -> bool:
    if article_url in self.__cache:
      if self.__cache[article_url] > datetime.now():
        return True
      else:
        # trigger a prune in case the TTL has expired
        self.__recreate_cache()
    return False
  
  def __recreate_cache(self):
    self.__recreate_valid_file()
    self.__load_cache()
        
  def __recreate_valid_file(self):
    # recreates the file with only the valid entries
    valid_ttls = [(url, exp_date) for url, exp_date in self.__cache.items() if exp_date > datetime.now()]
    if len(valid_ttls) < len(self.__cache):
      with open(self.__cache_file_path, "w") as f:
        for url, exp_date in valid_ttls:
          self.__write_line_to_file(f, url, exp_date)

  def store(self, article_url: str, ttl: timedelta = timedelta(weeks=1)) -> None:
    # prevent overflow
    now = datetime.now()
    if now > datetime.max - ttl:
      exp_date = datetime.max
    else:
      exp_date = datetime.now() + ttl
      
    if article_url in self.__cache:
      # update the cache and trigger a prune (easy fix instead of changing a specific line in the file)
      self.__cache[article_url] = exp_date
      self.__recreate_cache()
    else:
      # append to the cache file
      self.__cache[article_url] = exp_date
      with open(self.__cache_file_path, "a") as f:
        self.__write_line_to_file(f, article_url, exp_date)
      
  def __write_line_to_file(self, fdesc, article_url: str, exp_date: datetime) -> None:
    d = {
      "url": article_url,
      "expiration_date": exp_date.isoformat()
    }
    fdesc.write(json.dumps(d) + "\n")
  
  def remove(self, article_url: str) -> None:
    if article_url in self.__cache:
      del self.__cache[article_url]
      self.__recreate_cache()
      
    