from datetime import timedelta
from article_cache import ArticleCache

class NoOpArticleCache(ArticleCache):
  def contains(self, article_url: str) -> bool: 
    return False

  def store(self, article_url: str, ttl: timedelta = timedelta(weeks=1)) -> None:
    pass

  def remove(self, article_urL: str) -> None:
    pass
