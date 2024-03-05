import logging
import os
import time
import redis
from datetime import timedelta
from article_cache import ArticleCache
from utils import log_utils
import click
from cli_aware import ClickCliAware


class RedisArticleCache(ArticleCache):

  @classmethod
  def configure_logging(cls, level: int):
    cls.loglevel = level
    cls.log = log_utils.create_console_logger(
      name=cls.__name__,
      level=level
    )

  def __init__(self, redis_host: str, redis_port: int, log_level: int = logging.INFO):
    self.configure_logging(log_level)

    try:
      self.__redis = redis.Redis(host=redis_host, port=redis_port)
      backoff = 1
      while not self.__redis.ping():
        print(f"redis not ready, waiting {backoff} seconds")
        time.sleep(backoff)
        backoff *= 2

    except Exception as e:
      self.log.exception("failed to connect to redis")
      raise e


  def contains(self, article_url: str) -> bool:
    return bool(self.__redis.exists(article_url))

  def store(self, article_url: str, ttl: timedelta = timedelta(weeks=1)) -> None:
    key = f"article:{article_url}"
    self.__redis.set(key, "", ex=ttl)
  
  def remove(self, article_url: str) -> None:
    key = f"article:{article_url}"
    self.__redis.delete(key)


class RedisArticleCacheFactory(ClickCliAware):

  config = {}

  @staticmethod
  def register_cli_options(**kwargs) -> list[click.Option]:
    return [
      click.Option(
        param_decls=["--redis-cache-host"],
        help="Redis article cache hostname",
        default="localhost",
        envvar="CACHE_REDIS_HOST",
        show_default=True,
        show_envvar=True,
        callback=lambda ctx, param, value: RedisArticleCacheFactory.config.update({'host': value})
      ),
      click.Option(
        param_decls=["--redis-cache-port"],
        help="Redis article cache port",
        default=6379,
        envvar="CACHE_REDIS_PORT",
        type=click.INT,
        show_default=True,
        show_envvar=True,
        callback=lambda ctx, param, value: RedisArticleCacheFactory.config.update({'port': value})
      ),
    ]

  @staticmethod
  def create() -> RedisArticleCache:

    config = RedisArticleCacheFactory.config

    print(f"using redis article cache with host {config['host']}, port {config['port']}")

    return RedisArticleCache(
      config["host"],
      config["port"],
    )

# class RedisArticleCacheFactory:

#   @staticmethod
#   def create() -> RedisArticleCache:

#     host = os.getenv("REDIS_CACHE_HOST", "localhost")
#     port = os.getenv("REDIS_CACHE_PORT", 6379)
#     log_level = os.getenv("REDIS_CACHE_LOG_LEVEL", "INFO")
#     log_level = logging._nameToLevel[log_level]

#     logging.info(f"using redis article cache with host {host}, port {port}")

#     return RedisArticleCache(host, port, log_level)
