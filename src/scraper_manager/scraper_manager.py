from abc import ABC, abstractmethod
import json
import time
import redis
import logging
from scraper.config import Config
from scraper.scraper import ScrapeOptions, Scraper
import multiprocessing as mp
from utils import log_utils


class Notifier(ABC):

  @abstractmethod
  def send_done_notification(self, ids: list[str]):
    raise NotImplementedError


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


  def send_done_notification(self, ids: list[str]) -> bool:
    try:
      notification = {
        "done_meta": json.dumps(ids)
      }
      r_id = self.__redis.xadd(self.stream_name, notification)
      self.log.debug(f"added ids to stream, redis message id {r_id}")
    except Exception as e:
      self.log.error(f"error when adding ids to redis stream")
      raise e



class ScraperManager:

  proc_limit = 100

  def __init__(self, notifier: Notifier = None, *args, **kwargs):
    self.log = log_utils.create_console_logger(__name__)

    self.notifier = notifier
    if self.notifier is None:
      self.notifier: Notifier = RedisStreamsNotifier(*args, **kwargs)

  # TODO: unify config and scrape options
  def scrape(self, configs: list[Config], scrape_options: list[ScrapeOptions]):
    
    if len(configs) > self.proc_limit:
      raise ValueError(f"max number of config files and processes is {self.proc_limit}")

    # start processes
    proc = [] 
    q = mp.Queue(maxsize=self.proc_limit)
    for i in range(len(configs)):
      scraper = Scraper(id=i)
      name = f"Scraper-{i}"
      p = mp.Process(
        name=name, 
        target=scraper.scrape_articles, 
        args=(configs[i], scrape_options[i], q)
      )
      p.start()
      proc.append(p)
      self.log.info(f"started process {name} with config {configs[i].file_path}")

    # wait for process responses
    scraped_meta = []
    for i in range(len(proc)):
      # TODO: could hang indefinitely
      scraped_meta.extend(q.get())

    # wait for processes
    for i in range(len(proc)):
      p.join()
      self.log.info(f"process {name} with config {configs[i].file_path} finished")
    self.log.info(f"all scraper processes have finished")

    # send a "done" notification
    self.log.info(f"scraped articles: {scraped_meta}")
    if len(scraped_meta) == 0:
      self.log.warning("no scraped article ids found, no notification sent")
      return 

    self.notifier.send_done_notification(scraped_meta)