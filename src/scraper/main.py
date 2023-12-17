from argparse import ArgumentParser
from config import ConfigFactory
from scraper import Scraper
import logging

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
    "-o", "--output",
    type=str,
    required=True,
    dest="output_dir",
    help="Output directory to save scraped content to.",
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
    config = ConfigFactory().fromJsonFile(args.config)
  elif args.config.endswith(".yaml"):
    config = ConfigFactory().fromYamlFile(args.config)
  else:
    raise Exception("config file must be json or yaml")
  
  if args.debug:
    loglevel = logging.DEBUG
  else:
    loglevel = logging.INFO

  Scraper(loglevel).scrape_articles(
    config=config, 
    output_dir=args.output_dir, 
    article_limit=args.article_limit
  )
  