from bs4 import BeautifulSoup
from urllib.request import urlopen
from urllib.parse import urlparse
from urllib.parse import urljoin
import logging
import re
from pathlib import Path
import json
from datetime import datetime

from config import Config, ScrapeConfig, ComponentSelector
import log_utils
from selector_processor import SelectorProcessor
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
    self.selector_processor = SelectorProcessor(loglevel)

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
          
        article_result = {
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
    
  def _scrape_article(self, selector: ComponentSelector, article_url: str) -> dict | None:
    if not self._is_url_valid(article_url):
      self.log.warning(f"url {article_url} is not valid, not scraping it")
      return None

    page = urlopen(article_url)
    html = page.read().decode("utf-8")

    self.log.debug("trying to select article components")
    return self.selector_processor.process(selector, html)


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
      soup = BeautifulSoup(html, "html.parser")

      self.log.debug(f"using article limit {scrape_options.article_limit}")

      anchor_tags = soup.find_all("a", href=True)
      for link in anchor_tags:
        href_attr = link.get("href")
        absolute_url = self._create_absolute_link(href_attr, url)

        if not self._url_matches_any_pattern(absolute_url, scrape_config.url_patterns):
          continue
        
        self.log.debug(f"scrape config with url {scrape_config.urls} matching {absolute_url}")

        # TODO: call a cache interface to see if this url has already been scraped
        if scrape_options.article_cache.contains(absolute_url):
          self.log.debug(f"url {absolute_url} already in cache, skipping")
          continue
        
        scrape_options.article_cache.store(absolute_url, scrape_options.ttl)
        scraped_urls.add(absolute_url)

        if len(scraped_urls) >= scrape_options.article_limit:
          return list(scraped_urls)

    return list(scraped_urls)
  
  def _url_matches_any_pattern(self, url: str, regex_url_patterns: list[str]):

    # TODO: optimize by compiling patterns first
    for p in regex_url_patterns:
      self.log.debug(f"trying to match {p} to url {url}")
      if re.match(p, url):
        self.log.debug(f"pattern {p} matches url {url}")
        return True
    
    self.log.debug(f"url {url} not matching any url pattern from {';'.join(regex_url_patterns)}")
    return False
    
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
