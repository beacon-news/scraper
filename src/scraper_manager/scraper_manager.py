from scraper.config import Config
from scraper.scraper import Scraper
import multiprocessing as mp
from utils import log_utils
from scraper_manager.notifier import *


class ScraperManager:

  def __init__(self, notifier: Notifier, proc_count: int = 1):
    self.log = log_utils.create_console_logger(__name__)

    self.proc_count = proc_count
    if self.proc_count > mp.cpu_count():
      self.proc_count = mp.cpu_count()
      self.log.info(f"limiting number of processes to {self.proc_count} (number of cpu cores)")

    self.notifier = notifier

  # TODO: unify config and scrape options
  def scrape(self, configs: list[Config], scrape_options_kwargs_list: list[dict]):
    
    proc_count = self.proc_count
    if len(configs) < self.proc_count:
      proc_count = len(configs)
      self.log.info(f"limiting number of processes to {len(configs)} (number of configs)")
    
    # start processes
    proc = [] 
    input_queue = mp.Queue(maxsize=proc_count)
    output_queue = mp.Queue(maxsize=len(configs))
    for i in range(proc_count):
      scraper = Scraper(id=i)
      name = f"Scraper-{i}"
      p = mp.Process(
        name=name, 
        target=scraper.scrape_articles_from_queue, 
        args=(input_queue, output_queue)
      )
      p.start()
      proc.append(p)
      self.log.info(f"started process {name}")
    
    # put the work into the queue
    # scrape options will be constructed in the child process to avoid unpicklable objects
    for i in range(len(configs)):
      input_queue.put((configs[i], scrape_options_kwargs_list[i]))

    # wait for process responses, only store the unique ones
    ids = set()
    scraped_meta = []
    for i in range(len(configs)):
      # TODO: could hang indefinitely
      meta = output_queue.get()
      for item in meta:
        if item["id"] in ids:
          continue

        ids.add(item["id"])
        scraped_meta.append(item)
    
    # send 'done' messages
    for i in range(proc_count):
      input_queue.put((None, None))
    
    input_queue.close()
    output_queue.close()

    # wait for processes
    for i in range(proc_count):
      p.join()
      self.log.info(f"process {name} finished")
    self.log.info(f"all scraper processes have finished")

    if len(scraped_meta) == 0:
      self.log.warning("no scraped article ids found, no notification sent")
      return 

    self.notifier.send_done_notification(scraped_meta)
    self.log.info(f"sent a 'done' notification for {len(scraped_meta)} articles")