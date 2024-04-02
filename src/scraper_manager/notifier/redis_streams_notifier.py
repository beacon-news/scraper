from scraper_manager.notifier import Notifier
from utils import log_utils
import logging
import redis
import time
import json
from cli_aware import ClickCliAware
import click

class RedisStreamsNotifier(Notifier):

  def __init__(
      self, 
      redis_host: str = "localhost", 
      redis_port: int = 6379, 
      stream_name: str = "scraper_articles", 
      log_level: int = logging.INFO
  ):
    self.log = log_utils.create_console_logger(__name__, level=log_level)
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


  def send_done_notification(self, results: list[dict]) -> bool:
    try:
      notification = {
        "done": json.dumps(results)
      }
      r_id = self.__redis.xadd(self.stream_name, notification)
      self.log.debug(f"added ids to stream, redis message id {r_id}")
    except Exception as e:
      self.log.error(f"error when adding ids to redis stream")
      raise e


class RedisStreamsNotifierFactory(ClickCliAware):

  config = {}

  @staticmethod
  def register_cli_options(**kwargs) -> list[click.Option]:
    return [
      click.Option(
        param_decls=["--redis-streams-notifier-host"],
        help="Redis streams notifier hostname",
        default="localhost",
        envvar="NOTIFIER_REDIS_STREAM_HOST",
        show_default=True,
        show_envvar=True,
        callback=lambda ctx, param, value: RedisStreamsNotifierFactory.config.update({'host': value})
      ),
      click.Option(
        param_decls=["--redis-streams-notifier-port"],
        help="Redis streams notifier port",
        default=6379,
        envvar="NOTIFIER_REDIS_STREAM_PORT",
        type=click.INT,
        show_default=True,
        show_envvar=True,
        callback=lambda ctx, param, value: RedisStreamsNotifierFactory.config.update({'port': value})
      ),
      click.Option(
        param_decls=["--redis-streams-notfier-stream"],
        help="Redis streams notifier stream name",
        default="scraped_articles",
        envvar="NOTIFIER_REDIS_STREAM_NAME",
        show_default=True,
        show_envvar=True,
        callback=lambda ctx, param, value: RedisStreamsNotifierFactory.config.update({'stream_name': value})
      ),
    ]

  @staticmethod
  def create() -> RedisStreamsNotifier:

    config = RedisStreamsNotifierFactory.config

    print(f"using redis stream notifier with host {config['host']}, port {config['port']}, stream name {config['stream_name']}")

    return RedisStreamsNotifier(
      config["host"],
      config["port"],
      config["stream_name"],
    )