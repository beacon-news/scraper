import hashlib
from urllib import request
from urllib.parse import urlparse
from urllib.parse import urljoin
import logging
from datetime import datetime
from datetime import timedelta
import multiprocessing as mp

from scraper.config import Config, ScrapeConfig, ComponentSelectorConfig
from utils import log_utils
from utils import http_utils
from scraper.selector_processor import SelectorProcessor, set_log_levels
from article_cache import ArticleCache, NoOpArticleCache
from article_store import ArticleStore, NoOpArticleStore

class ScrapeOptions:

  def __init__(
      self, 
      article_limit: int | float = float("inf"),
      ttl: timedelta = timedelta(weeks=1),
      article_cache: ArticleCache = NoOpArticleCache(),
      article_stores: ArticleStore = [NoOpArticleStore()],
      log_level: int = logging.INFO,
  ): 
    if article_limit is None:
      self.article_limit = float("inf")
    else:
      self.article_limit = article_limit

    self.ttl = ttl
    self.article_cache = article_cache
    self.article_stores = article_stores
    self.log_level = log_level

class Scraper:

  def __init_logging(self, log_level: int):
    name = self.__class__.__name__
    if self.id is not None:
      name = name + '-' + self.id
    self.log = log_utils.create_console_logger(
      name=name,
      level=log_level
    )
    set_log_levels(log_level)
  
  def __init__(self, id: str):
    self.id = str(id) # just to make sure
    self.__init_logging(logging.INFO)
  
  def scrape_articles_from_queue(self, input_queue: mp.Queue, output_queue: mp.Queue):
    self.log.info("listening for work")
    config, scrape_options_kwargs = input_queue.get()
    while config is not None and scrape_options_kwargs is not None:
      scrape_options = ScrapeOptions(
        article_limit=scrape_options_kwargs['article_limit'],
        log_level=scrape_options_kwargs['log_level'],
        article_cache=scrape_options_kwargs['article_cache_factory'].create(),
        article_stores=scrape_options_kwargs['article_store_factory'].create(),
      )
      self.scrape_articles(config, scrape_options, output_queue)
      self.log.info("listening for work")
      config, scrape_options_kwargs = input_queue.get()
    self.log.info("got None work, exiting")

  def scrape_articles(
      self, 
      config: Config, 
      scrape_options: ScrapeOptions,
      queue: mp.Queue,
  ) -> None:

    self.log.setLevel(scrape_options.log_level)

    scrape_config_to_article_urls: dict[ScrapeConfig, list[str]] = {}
    for scrape_config in config.scrape_configs:
      scrape_config_to_article_urls[scrape_config] = self._find_article_urls(
        scrape_config, 
        scrape_options,
      )

    # at this point all urls are valid and can be scraped
    scraped_meta = []
    for scrape_config, urls in scrape_config_to_article_urls.items():
      for article_url in urls:
        self.log.info(f"trying to scrape {article_url}")

        scrape_result = self._scrape_article(scrape_config.selectors, article_url)
        if scrape_result is None:
          self.log.warning(f"no article components found for {article_url}")
          continue
          
        # add metadata as the first key, if it existed
        article_result = {}
        if scrape_config.metadata is not None:
          article_result |= {
            "metadata": scrape_config.metadata
          }
        
        # add other keys and the result
        # article id is a hash of the url and the content
        article_id = hashlib.sha1(f"{article_url}-{scrape_result}".encode()).hexdigest() 
        article_result |= {
          "id":  article_id,
          "url": article_url,
          "scrape_time": datetime.now().isoformat(),
          "components": scrape_result,
        }

        # store in every article store
        for s in scrape_options.article_stores:
          try: 
            s.store(article_url, article_result)
            
            # TODO: change this dict to be a data class
            scraped_meta.append({
              "id": article_id,
              "url": article_url,
              "scrape_time": article_result["scrape_time"],
            })
          except Exception:
            self.log.exception(f"error while trying to store article {article_url}")
            continue

        self.log.info(f"finished scraping {article_url}, id {article_id}")  
    
    # return the ids to parent process if there is one
    if queue is not None:
      # TODO: could hang indefinitely
      # TODO: why do we have every item duplicated sometimes??? 
      self.log.info(f"adding {len(scraped_meta)} items to parent's queue")
      queue.put(scraped_meta)
    
  def _scrape_article(self, selector: ComponentSelectorConfig, article_url: str) -> dict | None:
    try:
      req = http_utils.create_request(article_url)
      page = request.urlopen(req, timeout=15)
      html = page.read().decode("utf-8")
      self.log.debug("trying to select article components")
      return SelectorProcessor.process_html(selector, html)
    except Exception:
      self.log.exception(f"error while trying to scrape {article_url}")
      return None


  def _find_article_urls(
      self, 
      scrape_config: ScrapeConfig, 
      scrape_options: ScrapeOptions,
  ) -> list:
    urls = scrape_config.urls
    scraped_urls = set()

    for url in urls:
      self.log.info(f"finding article urls for {url}")

      if not self._is_url_valid(url):
        self.log.warning(f"url {url} is invalid, not finding any links for it")
        continue

      try:
        req = http_utils.create_request(url)
        page = request.urlopen(req, timeout=15)
        html = page.read().decode("utf-8")

        # select all urls using the specified selectors
        url_dict = SelectorProcessor.process_html(scrape_config.url_selectors, html)
        if url_dict is None:
          self.log.warning(f"url_selectors found no urls for {url}")
          continue

        url_list = self._flatten_dict_to_list(url_dict)

        self.log.debug(f"using article limit {scrape_options.article_limit}")
        
        for scraped_url in url_list:

          absolute_url = self._create_absolute_link(scraped_url, url)
          if not self._is_url_valid(absolute_url):
            self.log.warning(f"created absolute url {absolute_url} is invalid, skipping")
            continue

          # check the cache
          if scrape_options.article_cache.contains(absolute_url):
            self.log.info(f"url {absolute_url} already in cache, skipping")
            continue

          scrape_options.article_cache.store(absolute_url, scrape_options.ttl)
          scraped_urls.add(absolute_url)

          if len(scraped_urls) >= scrape_options.article_limit:
            self.log.debug(f"reached article limit {scrape_options.article_limit} when finding urls")
            return list(scraped_urls)
    
      except Exception as e:
        self.log.exception(f"error while finding article urls for {url}") 

    return list(scraped_urls)

  
  def _flatten_dict_to_list(self, d: dict | None) -> dict:
    if d is None:
      return []

    result = []
    for k, v in d.items():
      if isinstance(v, dict):
        result = [*result, *self._flatten_dict_to_list(v)]
      elif isinstance(v, list):
        result = [*result, *v]
      else:
        result.append(v)

    return result
  
    
  def _create_absolute_link(self, absolute_or_relative_url: str, base_url: str) -> str:
    link_parsed = urlparse(absolute_or_relative_url)
    scheme = link_parsed.scheme
    path = link_parsed.path

    if scheme != "http" and scheme != "https" and path:
      self.log.debug(f"url {absolute_or_relative_url} not matching scheme http or https, joining path to root url")
      return urljoin(base_url, path)

    return absolute_or_relative_url


  def _is_url_valid(self, url: str) -> bool:
    """checks if url has a scheme and a host"""
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    if not scheme:
      self.log.warning(f"no scheme found for url {url}")
      return False
    elif scheme != "http" and scheme != "https":
      self.log.warning(f"url {url} is not of http or https type")
      return False
    
    # see https://github.com/swisskyrepo/PayloadsAllTheThings/blob/master/Server%20Side%20Request%20Forgery/README.md
    # see https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html
    netloc = parsed.netloc.lower()
    netloc_blacklist = [
      'localhost', 
      '127.0.0.1', 
      '0.0.0.0',
      '0', 
      '::',
      '[::]',
      '[0000::1]',
    ]

    if not netloc:
      self.log.warning(f"no host found for url {url}")
      return False
    else:
      for host in netloc_blacklist:
        if host in netloc:
          self.log.warning(f"blacklisted host {host} found in url {url}")
          return False

    return True
