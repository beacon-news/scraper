from abc import ABC, abstractmethod
import click

class ClickCliAware(ABC):

  @abstractmethod
  def register_cli_options(*args, **kwargs) -> list[click.Option]:
    """
    Should return a list of click.Option objects which will be registered as cli options.
    """
    raise NotImplementedError
    