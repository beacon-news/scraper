import logging
import os
import time
import redis
from datetime import timedelta
from src.article_cache import ArticleCache
from src.utils import log_utils

class RedisArticleCache(ArticleCache):

  @classmethod
  def configure_logging(cls, level: int):
    cls.loglevel = level
    cls.log = log_utils.create_console_logger(
      name=cls.__name__,
      level=level
    )

  def __init__(self):
    self.configure_logging(logging.INFO)

    host = os.getenv("CACHE_REDIS_HOST", "localhost")
    port = int(os.getenv("CACHE_REDIS_PORT", 6379))

    try:
      self.__redis = redis.Redis(host=host, port=port)
      backoff = 1
      while not self.__redis.ping():
        print(f"redis not ready, waiting {backoff} seconds")
        time.sleep(backoff)
        backoff *= 2

    except Exception as e:
      logging.exception("failed to connect to redis")
      raise e


  def contains(self, article_url: str) -> bool:
    return bool(self.__redis.exists(article_url))

  def store(self, article_url: str, ttl: timedelta = timedelta(weeks=1)) -> None:
    key = f"article:{article_url}"
    self.__redis.set(key, "", ex=ttl)
  
  def remove(self, article_url: str) -> None:
    key = f"article:{article_url}"
    self.__redis.delete(key)
