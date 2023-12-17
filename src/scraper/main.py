from argparse import ArgumentParser
from config import ConfigFactory
from scraper import Scraper

def create_argument_parser() -> ArgumentParser:
  parser = ArgumentParser(
    description="tries to scrape news articles based on a config file",
  )
  parser.add_argument(
    "-c", "--config-file",
    type=str,
    required=True,
    dest="config",
    help="path to the json or yaml config file",
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
  if args.config.endswith(".json"):
    config = ConfigFactory().fromJsonFile(args.config)
  elif args.config.endswith(".yaml"):
    config = ConfigFactory().fromYamlFile(args.config)
  else:
    raise Exception("config file must be json or yaml")
  
  Scraper().scrape_articles(config, args.output_dir)
  