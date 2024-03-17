import logging
from pymongo import MongoClient
from article_store import ArticleStore
from utils import log_utils
import click
from cli_aware import ClickCliAware

class MongoDBArticleStore(ArticleStore):

  @classmethod
  def configure_logging(cls, level: int):
    cls.loglevel = level
    cls.log = log_utils.create_console_logger(
      name=cls.__name__,
      level=level
    )

  def __init__(
      self, 
      host: str, 
      port: int = None, 
      db_name: str = "scraper", 
      collection_name: str = "scraped_articles", 
      log_level: int = logging.INFO
  ):
    self.configure_logging(log_level)
    self.collection_name = collection_name
    self.db_name = db_name

    try:
      self.__mc = MongoClient(host=host, port=port)
      info = self.__mc.server_info()
      self.log.info(f"connected to mongodb, host {host}, port {port}, server info {info}")

      # assert database
      self.__db = self.__mc.get_database(db_name)
      self.log.info(f"using database {db_name}")

      # assert collection
      self.__col = self.__db.get_collection(collection_name)
      self.log.info(f"using collection {collection_name}")
  

    except Exception as e:
      self.log.exception("failed to connect to mongodb")
      raise e

  def store(self, article_url: str, article: dict) -> bool:
    if article is None:
      return False
    try:      
      # set the MongoDB _id
      doc = article.copy()
      doc["_id"] = doc["id"]
      id = self.__col.insert_one(doc)
      self.log.debug(f"inserted article into collection {self.collection_name}, id {id}")
      return True
    except Exception as e:
      self.log.error(f"error when inserting article into mongodb collection {self.collection_name}")
      raise e


class MongoDBArticleStoreFactory(ClickCliAware):

  config = {}

  @staticmethod
  def register_cli_options(**kwargs) -> list[click.Option]:
    return [
      click.Option(
        param_decls=["--mongodb-store-host"],
        help="MongoDB host",
        default="localhost",
        envvar="STORE_MONGODB_HOST",
        show_default=True,
        show_envvar=True,
        callback=lambda ctx, param, value: MongoDBArticleStoreFactory.config.update({'host': value})
      ),
      click.Option(
        param_decls=["--mongodb-store-port"],
        help="MongoDB port",
        default=27017,
        envvar="STORE_MONGODB_PORT",
        type=click.INT,
        show_default=True,
        show_envvar=True,
        callback=lambda ctx, param, value: MongoDBArticleStoreFactory.config.update({'port': value})
      ),
      click.Option(
        param_decls=["--mongodb-store-db"],
        help="MongoDB database name",
        default="scraper",
        envvar="STORE_MONGODB_DB",
        show_default=True,
        show_envvar=True,
        callback=lambda ctx, param, value: MongoDBArticleStoreFactory.config.update({'db': value})
      ),
      click.Option(
        param_decls=["--mongodb-store-collection"],
        help="MongoDB collection name",
        default="scraped_articles",
        envvar="STORE_MONGODB_COLLECTION",
        show_default=True,
        show_envvar=True,
        callback=lambda ctx, param, value: MongoDBArticleStoreFactory.config.update({'collection': value})
      ),
    ]

  @staticmethod
  def create() -> MongoDBArticleStore:

    config = MongoDBArticleStoreFactory.config

    print(f"using mongodb article store with config {config}")

    return MongoDBArticleStore(
      config["host"],
      config["port"],
      config["db"],
      config["collection"],
    )
