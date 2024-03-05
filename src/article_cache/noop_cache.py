from article_cache import ArticleCache
import click
from cli_aware import ClickCliAware

class NoOpArticleCache(ArticleCache):
  def contains(self, *args, **kwargs) -> bool: 
    return False

  def store(self, *args, **kwargs) -> None:
    pass

  def remove(self, *args, **kwargs) -> None:
    pass

class NoOpArticleCacheFactory(ClickCliAware):

  def register_cli_options(*args, **kwargs) -> list: 
    return []

  @ staticmethod
  def create() -> ArticleCache: 
    return NoOpArticleCache()

# class NoOpArticleCacheFactory:

#   @ staticmethod
#   def create() -> ArticleCache: 
#     return NoOpArticleCache()