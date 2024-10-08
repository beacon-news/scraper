from article_store.article_store import ArticleStore
from article_store.file_store import *
from article_store.noop_store import *
from article_store.redis_stream_store import * 
from article_store.mongodb_store import *
import click
from cli_aware import ClickCliAware

store_factories = {
  "noop": NoOpArticleStoreFactory,
  "file": FileArticleStoreFactory,
  "redis_streams": RedisStreamArticleStoreFactory,
  "mongodb": MongoDBArticleStoreFactory,
}

class ArticleStoreFactory(ClickCliAware):

  config = {}

  def register_cli_options() -> list:
    opts = []
    
    store_opt = click.Option(
      param_decls=["--store"],
      type=click.Choice(store_factories.keys()),
      multiple=True,
      default=["noop"],
      show_default=True,
      envvar="STORE_TYPE",
      show_envvar=True,
      callback=lambda ctx, param, values: ArticleStoreFactory.config.update({'types': values})
    )
    opts.append(store_opt)
    for factory in store_factories.values():
      opts.extend(factory.register_cli_options())
    return opts

  @staticmethod
  def create() -> list[ArticleStore]:
    l = []
    for f in ArticleStoreFactory.config['types']:
      l.append(store_factories[f].create())

    return l