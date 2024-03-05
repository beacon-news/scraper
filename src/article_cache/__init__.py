from article_cache.article_cache import ArticleCache
from article_cache.file_cache import FileArticleCache, FileArticleCacheFactory
from article_cache.noop_cache import NoOpArticleCache, NoOpArticleCacheFactory
from article_cache.redis_cache import RedisArticleCache, RedisArticleCacheFactory
import os
import click
from cli_aware import ClickCliAware


cache_factories = {
  "noop": NoOpArticleCacheFactory,
  "file": FileArticleCacheFactory,
  "redis": RedisArticleCacheFactory
}

# def create_article_cache() -> ArticleCache:
#   cache_type = os.getenv("CACHE_TYPE", "noop")
#   return cache_factories[cache_type].create()

class ArticleCacheFactory(ClickCliAware):

  config = {}

  def register_cli_options() -> list:
    opts = []
    
    cache_opt = click.Option(
      param_decls=["--cache"],
      type=click.Choice(cache_factories.keys()),
      default="noop",
      show_default=True,
      envvar="CACHE_TYPE",
      show_envvar=True,
      callback=lambda ctx, param, value: ArticleCacheFactory.config.update({'type': value})
    )
    opts.append(cache_opt)
    for factory in cache_factories.values():
      opts.extend(factory.register_cli_options())
    return opts

  @staticmethod
  def create() -> ArticleCache:
    return cache_factories[ArticleCacheFactory.config['type']].create()