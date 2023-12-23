from bs4 import BeautifulSoup, ResultSet
from urllib.request import urlopen
from urllib.parse import urlparse, ParseResult
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
      ttl: timedelta = timedelta.max,
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
      self.log.info(f"scraping from {scrape_config.url}")

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
      self.log.error(f"url {article_url} is not valid")
      return None

    page = urlopen(article_url)
    html = page.read().decode("utf-8")

    self.log.debug("trying to select article components")
    return self.selector_processor.process(selector, html)


  def _find_article_urls(
      self, 
      scrape_config: ScrapeConfig, 
      scrape_options: ScrapeOptions,
  ) -> dict:
    url = scrape_config.url
    self.log.info(f"finding article urls for {url}")

    page = urlopen(url)
    html = page.read().decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")

    self.log.debug(f"using article limit {scrape_options.article_limit}")

    anchor_tags = soup.find_all("a", href=True)
    urls = set()
    for link in anchor_tags:
      href_attr = link.get("href")
      article_url_parsed: ParseResult = urlparse(href_attr)

      if not self._url_path_matches_any_pattern(article_url_parsed, scrape_config.path_patterns):
        continue
      
      absolute_link = self._create_absolute_link(article_url_parsed, scrape_config)
      self.log.debug(f"scrape config with url {scrape_config.url} matching {absolute_link}")

      # TODO: call a cache interface to see if this url has already been scraped
      if scrape_options.article_cache.contains(absolute_link):
        self.log.debug(f"url {absolute_link} already in cache, skipping")
        continue
      
      scrape_options.article_cache.store(absolute_link, scrape_options.ttl)
      urls.add(absolute_link)

      if len(urls) >= scrape_options.article_limit:
        break

    return list(urls)
  
  def _url_path_matches_any_pattern(self, url_parsed: ParseResult, regex_path_patterns: list[str]):
    path = url_parsed.path
    url = url_parsed.geturl()

    for p in regex_path_patterns:
      if re.match(p, path):
        self.log.debug(f"url {url} matches path pattern {p}")
        return True

    self.log.debug(f"url {url} not matching any path pattern from {regex_path_patterns}")
    return False
    
  def _create_absolute_link(self, url_parsed: ParseResult, scrape_config: ScrapeConfig) -> str:
    scheme = url_parsed.scheme
    url = url_parsed.geturl()

    if scheme != "http" and scheme != "https":
      self.log.debug(f"url {url} not matching scheme http or https, joining path to root url")
      url = urljoin(scrape_config.url, url_parsed.path)

    return url
  
  def _is_url_valid(self, url: str) -> bool:
    """checks if url has a scheme and a location"""
    parsed = urlparse(url)
    return all([parsed.scheme, parsed.netloc])
