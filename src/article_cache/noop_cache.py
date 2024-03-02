from article_cache import ArticleCache

class NoOpArticleCache(ArticleCache):
  def contains(self, *args, **kwargs) -> bool: 
    return False

  def store(self, *args, **kwargs) -> None:
    pass

  def remove(self, *args, **kwargs) -> None:
    pass
