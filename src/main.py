from scraper.config import ConfigFactory
from scraper.scraper import ScrapeOptions, Scraper
from scraper_manager.notifier import *
import logging
from scraper_manager import ScraperManager
from article_cache import ArticleCacheFactory
from article_store import ArticleStoreFactory
from utils import log_utils

import click
import multiprocessing as mp

log = log_utils.create_console_logger("main")

def run_proc(**kwargs):
  
  proc_count = kwargs['processes']

  # create configs and scrape options
  config_paths = kwargs['config']
  options_list = []
  config_list = []
  for config_path in config_paths:

    config = ConfigFactory.from_file(config_path)
    config_list.append(config)
    
    options_kwargs = {
      "article_limit": kwargs['limit'],
      "log_level": kwargs['log_level'],
      "article_cache_factory": ArticleCacheFactory,
      "article_store_factory": ArticleStoreFactory,
    }
    options_list.append(options_kwargs)
  
  notifier = NotifierFactory.create()
  ScraperManager(notifier, proc_count).scrape(config_list, options_list)
  

def main():

  # multiple processes
  opts = [
    click.Option(
      param_decls=["-c", "--config"],
      required=True,
      envvar="SCRAPER_CONFIG_FILE",
      multiple=True,
      show_envvar=True,
      help="Path to the json or yaml config file.",
    ),
    click.Option(
      param_decls=["-p", "--processes"],
      type=click.INT,
      default=1,
      envvar="SCRAPER_PROCESSES",
      show_envvar=True,
      help="Number of scraper processes to start. Upper limit is the number of available cores.",
    ),
    click.Option(
      param_decls=["-l", "--limit"],
      type=click.INT,
      envvar="SCRAPER_ARTICLE_LIMIT",
      show_envvar=True,
      help="Limits the number of articles to scrape. By default all articles will be scraped.",
    ),
    click.Option(
      param_decls=["--log-level"],
      type=click.Choice([l for l in logging._nameToLevel.keys()]),
      default="INFO",
      show_default=True,
      envvar="SCRAPER_LOG_LEVEL",
      show_envvar=True,
      help="Sets the log level.",
    ),
  ] 

  # register any other cli options defined by the plugins, also configure the plugins
  opts.extend(ArticleCacheFactory.register_cli_options())
  opts.extend(ArticleStoreFactory.register_cli_options())
  opts.extend(NotifierFactory.register_cli_options())

  # create and run the command by using a callback
  cmd = click.Command(
    "",
    params=opts,
    callback=run_proc
  )
  cmd()


if __name__ == "__main__":
  main()
