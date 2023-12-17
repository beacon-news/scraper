from bs4 import BeautifulSoup
from urllib.request import urlopen
from urllib.parse import urlparse, ParseResult
from urllib.parse import urljoin
import logging
import re
from pathlib import Path
import json
from datetime import datetime

from config import Config, ScrapeConfig
import log_utils
from selector_processor import SelectorProcessor


class Scraper:

  def __init__(self, loglevel: int = logging.INFO):
    self.log = log_utils.createConsoleLogger(
      name=self.__class__.__name__,
      level=loglevel,
    )
    self.selector_processor = SelectorProcessor(loglevel)

  def scrape_articles(self, config: Config, article_dir: str):
    scrape_config_to_articles: dict[ScrapeConfig, list[str]] = self._find_articles(config)

    # for testing 

    scrape_config_to_articles = {
      config.scrape_configs[0]: ["https://www.bbc.com/news/world-europe-67529571"]
    }

    for scrape_config, urls in scrape_config_to_articles.items():
      self.log.info(f"scraping from {scrape_config.url}")

      for article_url in urls:
        self.log.info(f"trying to scrape {article_url}")

        if not self._is_url_valid(article_url):
          self.log.error(f"url {article_url} is not valid")
          continue

        page = urlopen(article_url)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")

        self.log.debug("trying to select article components")

        selectors_result = self.selector_processor.process(scrape_config, soup)
        if selectors_result is None:
          self.log.warning(f"no article components found for {article_url}")
          continue
          
        result = {
          "url": article_url,
          "scrape_time": datetime.now().isoformat(),
          "components": selectors_result
        }

        # TODO: call an interface which stores the results
        parsed_url = urlparse(article_url)
        article_file = f"article_{parsed_url.netloc}{parsed_url.path.replace('/','_')}.json"

        dir = Path(article_dir)
        dir.mkdir(parents=True, exist_ok=True)

        article_path = str(dir.joinpath(Path(article_file)))

        with open(article_path, "w") as f:
          json.dump(result, f)

        self.log.info(f"finished scraping {article_url}, saved to {article_path}")

  def _find_articles(self, config: Config) -> dict:
    scrape_config_to_urls = {}

    for scrape_config in config.scrape_configs:
      urls = []
      url = scrape_config.url
      self.log.info(f"finding article urls for {url}")

      page = urlopen(url)
      html = page.read().decode("utf-8")
      soup = BeautifulSoup(html, "html.parser")

      links = soup.find_all("a", href=True)

      for link in links:
        href = link.get("href")
        article_url_parsed: ParseResult = urlparse(href)

        if not self._url_path_matches_any_pattern(article_url_parsed, scrape_config):
          continue

        href = self._create_full_link(article_url_parsed, scrape_config)
        urls.append(href)

        self.log.debug(f"scrape config with url {url} matching {href}")

      scrape_config_to_urls[scrape_config] = urls

    return scrape_config_to_urls

  def _url_path_matches_any_pattern(self, url_parsed: ParseResult, scrape_config: ScrapeConfig):
    path = url_parsed.path
    url = url_parsed.geturl()

    for p in scrape_config.path_patterns:
      if re.match(p, path):
        self.log.debug(f"url {url} matches path pattern {p}")
        return True

    self.log.debug(f"url {url} not matching any path pattern from {scrape_config.path_patterns}")
    return False
    
  def _create_full_link(self, url_parsed: ParseResult, scrape_config: ScrapeConfig) -> str:
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
