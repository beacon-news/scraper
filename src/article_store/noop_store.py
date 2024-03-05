from article_store import ArticleStore
import click
from cli_aware import ClickCliAware

class NoOpArticleStore(ArticleStore):

  def store(self, *args, **kwargs) -> bool: pass

class NoOpArticleStoreFactory(ClickCliAware):

  def register_cli_options(*args, **kwargs) -> list:
    return []

  @staticmethod
  def create() -> NoOpArticleStore:
    return NoOpArticleStore()

# class NoOpArticleStoreFactory:

#   @staticmethod
#   def create() -> NoOpArticleStore:
#     return NoOpArticleStore()