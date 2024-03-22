from argparse import ArgumentParser
from scraper.config import ConfigFactory
from scraper.scraper import ScrapeOptions, Scraper
import logging
from article_cache import cache_factories
# from article_cache import NoOpArticleCache, FileArticleCache, RedisArticleCache
# from article_store import NoOpArticleStore, FileArticleStore, RedisStreamArticleStore


from article_cache import ArticleCacheFactory
from article_store import ArticleStoreFactory


import click


# def create_argument_parser() -> ArgumentParser:
#   parser = ArgumentParser(
#     description="tries to scrape news articles based on a config file",
#   )

#   # global args
#   parser.add_argument(
#     "-l", "--limit",
#     type=int,
#     default=None,
#     required=False,
#     dest="article_limit",
#     help="Limits the number of articles to scrape. By default all articles will be scraped.",
#   )
#   parser.add_argument(
#     "-d", "--debug",
#     action="store_true",
#     default=False,
#     required=False,
#     dest="debug",
#     help="Enables debug logging.",
#   )

#   parser.add_argument(
#     "-c", "--config-file",
#     type=str,
#     required=True,
#     dest="config",
#     help="Path to the json or yaml config file.",
#   )

#   # TODO: add proper plugin args for cache and store
#   # cache args
#   parser.add_argument(
#     "-c", "--cache",
#     type=str,
#     required=False,
#     default="noop",
#     dest="cache",
#     choices=caches.keys()
#   )
#   parser.add_argument(
#     "--cache-file",
#     type=str,
#     required=False,
#     dest="cache_file",
#     help="Cache file path.",
#   )

#   # store args
#   parser.add_argument(
#     "-s", "--store",
#     type=str,
#     required=False,
#     default="noop",
#     dest="store",
#     choices=stores.keys()
#   )
#   parser.add_argument(
#     "-o", "--output-dir",
#     type=str,
#     required=False,
#     dest="output_dir",
#     help="Output directory to save scraped content to.",
#   )
#   return parser


# @click.command
# @click.option(
#   "-c", "--config",
#   required=True,
#   envvar="SCRAPER_CONFIG_FILE",
#   show_envvar=True,
#   help="Path to the json or yaml config file.",
# )
# @click.option(
#   "-l", "--limit",
#   type=click.INT,
#   envvar="SCRAPER_ARTICLE_LIMIT",
#   show_envvar=True,
#   help="Limits the number of articles to scrape. By default all articles will be scraped.",
# )
# @click.option(
#   "--log-level",
#   type=click.Choice([l for l in logging._nameToLevel.keys()]),
#   default="INFO",
#   show_default=True,
#   envvar="SCRAPER_LOG_LEVEL",
#   show_envvar=True,
#   help="Limits the number of articles to scrape. By default all articles will be scraped.",
# )
# @click.option(
#   "--cache-type",
#   type=click.Choice(cache_factories.keys()),
#   default="noop",
#   show_default=True,
#   envvar="CACHE_TYPE",
#   show_envvar=True,
#   help="Type of cache to use"
# )
# @click.option(
#   type=click.Choice(cache_factories.keys()),
#   default="noop",
#   show_default=True,
#   envvar="CACHE_TYPE",
#   show_envvar=True,
#   help="Type of cache to use"
# )
# def cli(config, limit, log_level):



#   if limit is None:
#     limit = float("inf")

#   log_level = logging._nameToLevel[log_level]
  
#   if config.endswith(".json"):
#     config = ConfigFactory.from_json_file(config)
#   elif config.endswith(".yaml"):
#     config = ConfigFactory.from_yaml_file(config)
#   else:
#     raise Exception("config file must be json or yaml")

#   # created and configured based on env vars
#   # cache = create_article_cache()
#   # store = create_article_store()

#   options = ScrapeOptions(
#     article_limit=limit,
#     log_level=log_level,
#     article_cache=cache,
#     article_store=store
#   )
#   scraper = Scraper()
#   scraper.scrape_articles(config, options)

# this will be run when invoking the command
def run(**kwargs):
  config_path = kwargs['config']
  if config_path.endswith(".json"):
    config = ConfigFactory.from_json_file(config_path)
  elif config_path.endswith(".yaml"):
    config = ConfigFactory.from_yaml_file(config_path)
  else:
    raise Exception("config file must be json or yaml")
  
  options = ScrapeOptions(
    article_limit=kwargs['limit'],
    log_level=kwargs['log_level'],
    article_cache=ArticleCacheFactory.create(),
    article_stores=ArticleStoreFactory.create(),
  )
  scraper = Scraper()
  scraper.scrape_articles(config, options)


import multiprocessing as mp
from utils import log_utils

log = log_utils.create_console_logger("main")

def run_proc(**kwargs):
  proc_limit = 100
  config_paths = kwargs['config']
  if len(config_paths) > proc_limit:
    raise Exception(f"max number of config files and processes is {proc_limit}")

  options_list = []
  config_list = []
  for config_path in config_paths:

    if config_path.endswith(".json"):
      config = ConfigFactory.from_json_file(config_path)
    elif config_path.endswith(".yaml"):
      config = ConfigFactory.from_yaml_file(config_path)
    else:
      raise Exception(f"config file must be json or yaml, provided: '{config_path}'")
    
    config_list.append(config)
    
    options = ScrapeOptions(
      article_limit=kwargs['limit'],
      log_level=kwargs['log_level'],
      article_cache=ArticleCacheFactory.create(),
      article_stores=ArticleStoreFactory.create(),
    )
    options_list.append(options)
  
  # start processes
  proc = [] 
  q = mp.Queue(maxsize=proc_limit)
  for i in range(len(options_list)):
    options = options_list[i]
    config = config_list[i]
    scraper = Scraper(id=i)
    name = f"Scraper-{i}"
    p = mp.Process(name=name, target=scraper.scrape_articles, args=(config, options, q))
    p.start()
    proc.append(p)
    log.info(f"started process {name} with config {config_paths[i]}")

  # wait for responses
  scraped_ids = []
  for i in range(len(proc)):
    # TODO: could hang indefinitely
    scraped_ids.extend(q.get())

  # wait for processes
  for i in range(len(proc)):
    p.join()
    log.info(f"process {name} with config {config_paths[i]} finished")
  log.info(f"all scraper processes have finished")

  log.info(f"scraped ids: {scraped_ids}")


if __name__ == "__main__":

  # # single process
  # opts = [
  #   click.Option(
  #     param_decls=["-c", "--config"],
  #     required=True,
  #     envvar="SCRAPER_CONFIG_FILE",
  #     show_envvar=True,
  #     help="Path to the json or yaml config file.",
  #   ),
  #   click.Option(
  #     param_decls=["-l", "--limit"],
  #     type=click.INT,
  #     envvar="SCRAPER_ARTICLE_LIMIT",
  #     show_envvar=True,
  #     help="Limits the number of articles to scrape. By default all articles will be scraped.",
  #   ),
  #   click.Option(
  #     param_decls=["--log-level"],
  #     type=click.Choice([l for l in logging._nameToLevel.keys()]),
  #     default="INFO",
  #     show_default=True,
  #     envvar="SCRAPER_LOG_LEVEL",
  #     show_envvar=True,
  #     help="Sets the log level.",
  #   ),
  # ] 

  # # register any other cli options defined by the plugins, also configure the plugins
  # opts.extend(ArticleCacheFactory.register_cli_options())
  # opts.extend(ArticleStoreFactory.register_cli_options())

  # # create and run the command by using a callback
  # cmd = click.Command(
  #   "",
  #   params=opts,
  #   callback=run
  # )

  # cmd()

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

  # create and run the command by using a callback
  cmd = click.Command(
    "",
    params=opts,
    callback=run_proc
  )

  cmd()

  # register any other cli options defined by the plugins


  # cli = click.Command(
  #   params=[

  #   ]
  # )



  # args = create_argument_parser().parse_args()
  # if args.config.endswith(".json"):
  #   config = ConfigFactory.fromJsonFile(args.config)
  # elif args.config.endswith(".yaml"):
  #   config = ConfigFactory.fromYamlFile(args.config)
  # else:
  #   raise Exception("config file must be json or yaml")
  
  # if args.debug:
  #   loglevel = logging.DEBUG
  # else:
  #   loglevel = logging.INFO

  # if args.cache_file:
  #   cache = FileArticleCache(cache_file_path=args.cache_file)
  # else:
  #   cache = NoOpArticleCache()
  
  # if args.output_dir:
  #   store = FileArticleStore(output_dir=args.output_dir)
  # else:
  #   store = NoOpArticleStore()
  
  # if args.article_limit:
  #   limit = args.article_limit
  # else:
  #   limit = float("inf")

  # options = ScrapeOptions(
  #   article_limit=limit,
  #   article_cache=cache,
  #   article_store=store,
  # )

  # Scraper().scrape_articles(
  #   config=config, 
  #   scrape_options=options
  # )
  