import logging
import os
import time
import redis
from article_store import ArticleStore
from utils import log_utils

class RedisStreamArticleStore(ArticleStore):

  @classmethod
  def configure_logging(cls, level: int):
    cls.loglevel = level
    cls.log = log_utils.create_console_logger(
      name=cls.__name__,
      level=level
    )

  def __init__(self):
    self.configure_logging(logging.INFO)

    host = os.getenv("STORE_REDIS_HOST", "localhost")
    port = int(os.getenv("STORE_REDIS_PORT", 6379))
    self.stream_name = os.getenv("STORE_REDIS_STREAM_NAME", "scraped_articles")

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


  def store(self, article_url: str, article: dict) -> bool:
    try:
      id = self.__redis.xadd(self.stream_name, article)
      self.log.debug(f"added article to stream, id {id}")
    except Exception as e:
      self.log.error(f"error when adding article to stream")
      raise e
