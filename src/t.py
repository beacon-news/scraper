from argparse import ArgumentParser
from scraper.config import ConfigFactory
from scraper.scraper import ScrapeOptions, Scraper
import logging
from article_cache import NoOpArticleCache, FileArticleCache, RedisArticleCache
from article_store import NoOpArticleStore, FileArticleStore, RedisStreamArticleStore

import click

caches = {
  "noop": NoOpArticleCache,
  "file": FileArticleCache,
  "redis": RedisArticleCache,
}

stores = {
  "noop": NoOpArticleStore,
  "file": FileArticleStore,
  "redis_streams": RedisStreamArticleStore,
}

def create_argument_parser() -> ArgumentParser:
  parser = ArgumentParser(
    description="tries to scrape news articles based on a config file",
  )

  # global args
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

  parser.add_argument(
    "-c", "--config-file",
    type=str,
    required=True,
    dest="config",
    help="Path to the json or yaml config file.",
  )

  # TODO: add proper plugin args for cache and store
  # cache args
  parser.add_argument(
    "-c", "--cache",
    type=str,
    required=False,
    default="noop",
    dest="cache",
    choices=caches.keys()
  )
  parser.add_argument(
    "--cache-file",
    type=str,
    required=False,
    dest="cache_file",
    help="Cache file path.",
  )

  # store args
  parser.add_argument(
    "-s", "--store",
    type=str,
    required=False,
    default="noop",
    dest="store",
    choices=stores.keys()
  )
  parser.add_argument(
    "-o", "--output-dir",
    type=str,
    required=False,
    dest="output_dir",
    help="Output directory to save scraped content to.",
  )
  return parser


@click.command()
# general options
@click.option(
  "-c", "--config-file",
  required=True,
  help="Path to the json or yaml config file.",
)
@click.option(
  "-l", "--limit",
  type=click.INT,
  help="Limits the number of articles to scrape. By default all articles will be scraped.",
)
@click.option(
  "--log-level",
  type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
  default="INFO",
  show_default=True,
  help="Sets the log level.",
)
# cache options
@click.option(
  "--cache",
  type=click.Choice(caches.keys()),
  default="noop",
  show_default=True,
  help="Sets the cache type.",
)
@click.option(
  "--cache-file",
  help="In case of 'file' cache, set the cache file path.",
)
@click.option(
  "--cache-redis-host",
  default="localhost",
  envvar="CACHE_REDIS_HOST",
  show_default=True,
  help="In case of 'redis' cache, set the redis host.",
)
@click.option(
  "--cache-redis-port",
  default=6379,
  help="In case of 'redis' cache, set the redis port.",
)
@click.option(
  "--store",
  type=click.Choice(stores.keys()),
  default="noop",
  show_default=True,
  help="Sets the article storage type.",
)
@click.option(
  "--store-file-output-dir",
  help="In case of 'file' article store, set the output directory.",
)
@click.option(
  "--store-redis-host",
  default="localhost",
  envvar="STORE_REDIS_HOST",
  show_default=True,
  help="In case of 'redis' article store, set the redis host.",
)
@click.option(
  "--store-redis-port",
  default=6379,
  show_default=True,
  help="In case of 'redis' article store, set the redis port.",
)
@click.pass_context
def cli(ctx, config_file, limit, log_level, 
        cache, 
        cache_file, 
        cache_redis_host, cache_redis_port,
        store,
        store_file_output_dir,
        store_redis_host, store_redis_port,
        ) -> dict:

  click.echo("called root cli group")

  click.echo("config file: " + config_file)

  # set default value for article limit
  if limit is None:
    limit = float("inf")


  click.echo(f"limit: {limit}")
  click.echo(f"log: {log_level}")

  click.echo(f"cache: {cache}")
  click.echo(f"cache file: {cache_file}")
  click.echo(f"cache redis host: {cache_redis_host}")
  click.echo(f"cache redis port: {cache_redis_port}")

  click.echo(f"store: {store}")
  click.echo(f"store output dir: {store_file_output_dir}")
  click.echo(f"store redis host: {store_redis_host}")
  click.echo(f"store redis port: {store_redis_port}")

  # click.echo(ctx.scrape_options)


@click.option(
  "-c", "--cache",
  type=click.Choice(caches.keys()),
  default="noop",
  help="Sets the cache type.",
)
@click.pass_context
def cache_options(ctx, cache) -> dict:

  click.echo(f"cache: {cache}")
  ctx.scrape_options["cache"] = cache


if __name__ == "__main__":

  cli()
  # cache_options()

  
  exit(0)


if __name__ == "__main__":

  # store args
  parser = ArgumentParser()
  parser.add_argument(
    "-s", "--store",
    type=str,
    required=False,
    default="noop",
    dest="store",
    choices=stores.keys()
  )
  parser.add_argument(
    "-o", "--output-dir",
    type=str,
    required=False,
    dest="output_dir",
    help="Output directory to save scraped content to.",
  )

  (args, rest) = parser.parse_known_args()
  print(args)
  print(rest)

  # subp = parser.add_subparsers(help="store help")

  # p = subp.add_parser("noop", help="noop store help")

  # g = p.add_argument_group()
  # p.add_argument('-a', type=str, dest='a', help='-a subcommand of "noop store"')
  # p.add_argument('-b', type=str, dest='b', help='-b subcommand of "noop store"')

  # (args, rest) = parser.parse_known_args()
  # print(args)
  # print(rest)

  # (pargs, prest) = p.parse_known_args(rest)
  # print(pargs)
  # print(prest)

  # exit(0)


  if args.store == "noop":
    print("creating new argument parser for 'store'")
    p = ArgumentParser(prog=args)
    # subp = parser.add_subparsers(help="noop store BIG help")

    # p = subp.add_parser("noop", help="noop store help")

    g = p.add_argument_group()
    p.add_argument('-a', type=str, dest='a', help='-a subcommand of "noop store"', required=True)
    p.add_argument('-b', type=str, dest='b', help='-b subcommand of "noop store"')


    (pargs, prest) = p.parse_known_args(rest)
    print(pargs)
    print(prest)
