from urllib.request import urlopen
from urllib.parse import urlparse
from urllib.parse import urljoin
import logging
from pathlib import Path
import json
from datetime import datetime

from config import Config, ScrapeConfig, ComponentSelectorConfig
import log_utils
from selector_processor import SelectorProcessor, setLogLevels
from article_cache import ArticleCache, NoOpArticleCache
from datetime import timedelta

class ScrapeOptions:

  def __init__(
      self, 
      output_dir: str, 
      article_limit: int | float = float("inf"),
      ttl: timedelta = timedelta(weeks=1),
      article_cache: ArticleCache = NoOpArticleCache(),
  ):
    self.output_dir = output_dir
    self.article_limit = article_limit
    self.ttl = ttl
    self.article_cache = article_cache

class Scraper:

  def __init__(self, loglevel: int = logging.INFO):
    self.log = log_utils.createConsoleLogger(
      name=self.__class__.__name__,
      level=loglevel,
    )
    setLogLevels(loglevel)

  def scrape_articles(
      self, 
      config: Config, 
      scrape_options: ScrapeOptions = ScrapeOptions(output_dir="scraper_output"),
  ) -> None:

    scrape_config_to_article_urls: dict[ScrapeConfig, list[str]] = {}
    for scrape_config in config.scrape_configs:
      scrape_config_to_article_urls[scrape_config] = self._find_article_urls(
        scrape_config, 
        scrape_options,
      )

    # at this point all urls are valid and can be scraped

    # for testing 

    # scrape_config_to_articles = {
    #   config.scrape_configs[0]: ["https://www.bbc.com/news/world-europe-67529571"]
    # }

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
        article_result |= {
          "url": article_url,
          "scrape_time": datetime.now().isoformat(),
          "components": scrape_result
        }

        # TODO: call an interface which stores the results
        parsed_url = urlparse(article_url)
        article_file = f"{parsed_url.netloc}{parsed_url.path.replace('/','_')}.json"

        dir = Path(scrape_options.output_dir)
        dir.mkdir(parents=True, exist_ok=True)

        article_path = str(dir.joinpath(Path(article_file)))

        with open(article_path, "w") as f:
          json.dump(article_result, f)

        self.log.info(f"finished scraping {article_url}, saved to {article_path}")
    
  def _scrape_article(self, selector: ComponentSelectorConfig, article_url: str) -> dict | None:
    if not self._is_url_valid(article_url):
      self.log.warning(f"url {article_url} is not valid, not scraping it")
      return None

    page = urlopen(article_url)
    html = page.read().decode("utf-8")

    self.log.debug("trying to select article components")
    return SelectorProcessor.process_html(selector, html)


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

      # TODO: catch errors here
      page = urlopen(url)

      html = page.read().decode("utf-8")

      # select all urls using the specified selectors
      url_dict = SelectorProcessor.process_html(scrape_config.url_selectors, html)
      url_list = self._flatten_dict_to_list(url_dict)

      self.log.debug(f"using article limit {scrape_options.article_limit}")
      
      for scraped_url in url_list:
        absolute_url = self._create_absolute_link(scraped_url, url)

        if scrape_options.article_cache.contains(absolute_url):
          self.log.info(f"url {absolute_url} already in cache, skipping")
          continue

        scrape_options.article_cache.store(absolute_url, scrape_options.ttl)
        scraped_urls.add(absolute_url)

        if len(scraped_urls) >= scrape_options.article_limit:
          return list(scraped_urls)

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
      return urljoin(base_url, link_parsed.path)

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
