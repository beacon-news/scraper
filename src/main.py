from argparse import ArgumentParser
from scraper.config import ConfigFactory
from scraper.scraper import ScrapeOptions, Scraper
import logging
from article_cache import NoOpArticleCache, FileArticleCache
from article_store import NoOpArticleStore, FileArticleStore

def create_argument_parser() -> ArgumentParser:
  parser = ArgumentParser(
    description="tries to scrape news articles based on a config file",
  )
  parser.add_argument(
    "-c", "--config-file",
    type=str,
    required=True,
    dest="config",
    help="Path to the json or yaml config file.",
  )
  parser.add_argument(
    "-o", "--output-dir",
    type=str,
    required=False,
    dest="output_dir",
    help="Output directory to save scraped content to.",
  )
  parser.add_argument(
    "--cache-file",
    type=str,
    required=False,
    dest="cache_file",
    help="Cache file path.",
  )
  parser.add_argument(
    "-l", "--limit",
    type=int,
    default=None,
    required=False,
    dest="article_limit",
    help="Limits the number of articles to scrape. By default all articles will be scraped.",
  )
  parser.add_argument(
    "-d", "--debug",
    action="store_true",
    default=False,
    required=False,
    dest="debug",
    help="Enables debug logging.",
  )
  return parser


if __name__ == "__main__":

  args = create_argument_parser().parse_args()
  if args.config.endswith(".json"):
    config = ConfigFactory.fromJsonFile(args.config)
  elif args.config.endswith(".yaml"):
    config = ConfigFactory.fromYamlFile(args.config)
  else:
    raise Exception("config file must be json or yaml")
  
  if args.debug:
    loglevel = logging.DEBUG
  else:
    loglevel = logging.INFO

  if args.cache_file:
    cache = FileArticleCache(cache_file_path=args.cache_file)
  else:
    cache = NoOpArticleCache()
  
  if args.output_dir:
    store = FileArticleStore(output_dir=args.output_dir)
  else:
    store = NoOpArticleStore()
  
  if args.article_limit:
    limit = args.article_limit
  else:
    limit = float("inf")

  options = ScrapeOptions(
    article_limit=limit,
    article_cache=cache,
    article_store=store,
  )

  Scraper(loglevel).scrape_articles(
    config=config, 
    scrape_options=options
  )
  