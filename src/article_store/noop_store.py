from article_store import ArticleStore

class NoOpArticleStore(ArticleStore):

  def store(self, *args, **kwargs) -> bool: pass