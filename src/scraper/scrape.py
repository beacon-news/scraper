from bs4 import BeautifulSoup
from urllib.request import urlopen
from urllib.parse import urlparse, ParseResult
from urllib.parse import urljoin
import logging
import re
from pathlib import Path
import json
from datetime import datetime
from argparse import ArgumentParser

from process_selectors import process_from_root
from config import Config, ScrapeConfig, ConfigFactory

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

def url_path_matches_patterns(url_parsed: ParseResult, scrape_config: ScrapeConfig):
  path = url_parsed.path
  url = url_parsed.geturl()

  for p in scrape_config.path_patterns:
    if not re.match(p, path):
      log.debug(f"url {url} not matching path pattern {p}")
      return False
  
  log.debug(f"url {url} matches path pattern {p}")
  return True

def append_relative_link(url_parsed: ParseResult, scrape_config: ScrapeConfig) -> str:
  http_scheme = "http|https"
  scheme = url_parsed.scheme
  url = url_parsed.geturl()

  if not re.match(http_scheme, scheme):
    log.debug(f"url {url} not matching scheme {http_scheme}, joining")
    url = urljoin(scrape_config.url, url_parsed.path)

  return url

def find_articles(config: Config) -> dict:
  scrape_config_to_urls = {}
  for scrape_config in config.scrape_configs:
    urls = []
    log.info(f"finding article urls for {scrape_config.url}")
    
    url = scrape_config.url

    page = urlopen(url)
    html = page.read().decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")

    links = soup.find_all("a", href=True)

    for link in links:
      href = link.get("href")
      url_parsed: ParseResult = urlparse(href)

      if not url_path_matches_patterns(url_parsed, scrape_config):
        continue

      href = append_relative_link(url_parsed, scrape_config)
      urls.append(href)

    scrape_config_to_urls[scrape_config] = urls

    for href in urls:
      log.debug(f"scrape config with url {scrape_config.url} matching ", href)
  
  return scrape_config_to_urls


def is_url_valid(url: str) -> bool:
  """checks if url has a scheme and a location"""
  parsed = urlparse(url)
  return all([parsed.scheme, parsed.netloc])
  
article_url = "https://www.bbc.com/news/world-europe-67529571"

if not is_url_valid(article_url):
  log.error(f"url {article_url} is not valid")
  exit(1)


page = urlopen(article_url)
html = page.read().decode("utf-8")
soup = BeautifulSoup(html, "html.parser")

def scrape_articles(config: Config, article_dir: str):

  scrape_config_to_articles: dict[ScrapeConfig, list[str]] = find_articles(config)

  # for testing 

  # scrape_config_to_articles = {
  #   config.scrape_configs[0]: ["https://www.bbc.com/news/world-europe-67529571"]
  # }

  for scrape_config, urls in scrape_config_to_articles.items():
    log.info(f"scraping from {scrape_config.url}")

    for article_url in urls:
      log.info(f"trying to scrape {article_url}")

      if not is_url_valid(article_url):
        log.error(f"url {article_url} is not valid")
        continue

      page = urlopen(article_url)
      html = page.read().decode("utf-8")
      soup = BeautifulSoup(html, "html.parser")

      log.debug("trying to select article components")

      selectors_result = process_from_root(scrape_config, soup)
      if selectors_result is None:
        log.warning(f"no article components found for {article_url}")
        continue
        
      result = {
        "url": article_url,
        "scrape_time": datetime.now().isoformat(),
        "components": selectors_result
      }

      parsed_url = urlparse(article_url)
      article_file = f"article_{parsed_url.netloc}{parsed_url.path.replace('/','_')}.json"

      dir = Path(article_dir)
      dir.mkdir(parents=True, exist_ok=True)

      article_path = str(dir.joinpath(Path(article_file)))

      with open(article_path, "w") as f:
        json.dump(result, f)

      log.info(f"finished scraping {article_url}, saved to {article_path}")

def create_argument_parser() -> ArgumentParser:
  parser = ArgumentParser(
    description="tries to scrape news articles based on a config file",
  )

  parser.add_argument(
    "-c", "--config-file",
    type=str,
    required=True,
    dest="config",
    help="path to config file",
  )
  parser.add_argument(
    "-o", "--output",
    type=str,
    required=True,
    dest="output_dir",
    help="output directory to save scraped content to",
  )
  return parser


if __name__ == "__main__":

  args = create_argument_parser().parse_args()
  
  config = ConfigFactory().fromJsonFile(args.config)
  scrape_articles(config, args.output_dir)