import logging
import os
import time
import redis
from article_store import ArticleStore
from utils import log_utils
import click
from cli_aware import ClickCliAware
import json

class RedisStreamArticleStore(ArticleStore):

  @classmethod
  def configure_logging(cls, level: int):
    cls.loglevel = level
    cls.log = log_utils.create_console_logger(
      name=cls.__name__,
      level=level
    )

  def __init__(self, redis_host: str, redis_port: int, stream_name: str, log_level: int = logging.INFO):
    self.configure_logging(log_level)
    self.stream_name = stream_name

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


  def store(self, article_url: str, article: dict) -> bool:
    if article is None:
      return False

    try:
      data = {
        "url": article_url,
        "article": json.dumps(article)
      }
      id = self.__redis.xadd(self.stream_name, data)
      self.log.debug(f"added article to stream, id {id}")
    except Exception as e:
      self.log.error(f"error when adding article to stream")
      raise e


class RedisStreamArticleStoreFactory(ClickCliAware):

  config = {}

  @staticmethod
  def register_cli_options(**kwargs) -> list[click.Option]:
    return [
      click.Option(
        param_decls=["--redis-streams-store-host"],
        help="Redis streams article store hostname",
        default="localhost",
        envvar="STORE_REDIS_STREAM_HOST",
        show_default=True,
        show_envvar=True,
        callback=lambda ctx, param, value: RedisStreamArticleStoreFactory.config.update({'host': value})
      ),
      click.Option(
        param_decls=["--redis-streams-store-port"],
        help="Redis streams article store port",
        default=6379,
        envvar="STORE_REDIS_STREAM_PORT",
        type=click.INT,
        show_default=True,
        show_envvar=True,
        callback=lambda ctx, param, value: RedisStreamArticleStoreFactory.config.update({'port': value})
      ),
      click.Option(
        param_decls=["--redis-streams-stream-name"],
        help="Redis streams article store stream name",
        default="scraped_articles",
        envvar="STORE_REDIS_STREAM_NAME",
        show_default=True,
        show_envvar=True,
        callback=lambda ctx, param, value: RedisStreamArticleStoreFactory.config.update({'stream_name': value})
      ),
    ]

  @staticmethod
  def create() -> RedisStreamArticleStore:

    config = RedisStreamArticleStoreFactory.config

    print(f"using redis stream article store with host {config['host']}, port {config['port']}, stream name {config['stream_name']}")

    return RedisStreamArticleStore(
      config["host"],
      config["port"],
      config["stream_name"],
    )


# class RedisStreamArticleStoreFactory:

#   @staticmethod
#   def create() -> RedisStreamArticleStore:

#     host = os.getenv("REDIS_STREAM_STORE_HOST", "localhost")
#     port = os.getenv("REDIS_STREAM_STORE_PORT", 6379)
#     stream_name = os.getenv("REDIS_STREAM_STORE_STREAM", "scraped_articles")
#     log_level = os.getenv("REDIS_STREAM_STORE_LOG_LEVEL", "INFO")
#     log_level = logging._nameToLevel[log_level]

#     logging.info(f"using redis stream article store with host {host}, port {port}, stream name {stream_name}")

#     return RedisStreamArticleStore(host, port, stream_name, log_level)

