from abc import ABC, abstractmethod
from datetime import timedelta

class ArticleCache(ABC):
  """
  Stores the URLs of articles that have already been scraped.
  """

  @abstractmethod
  def contains(self, article_url: str) -> bool:
    """
    Returns true if article_url is in the cache,
    and its TTL has not expired
    """
    raise NotImplementedError
  

  @abstractmethod
  def store(self, article_url: str, ttl: timedelta = timedelta(weeks=1)) -> None:
    """
    Stores the "article_url" with a TTL indicating that 
    the article has been scraped, and the scraped information 
    is valid until datetime.now() + "ttl" timedelta
    """
    raise NotImplementedError
  
  # TODO: do we actually need remove functionality ?
  # ttl should be enough...
  @abstractmethod
  def remove(self, article_url: str) -> None:
    """
    Removes the "article_url" from the cache
    """
    raise NotImplementedError
