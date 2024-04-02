from scraper_manager.notifier import Notifier
from cli_aware import ClickCliAware

class NoOpNotifier(Notifier):
  def send_done_notification(self, ids: list[str]):
    print("no-op notifier sending notification")

class NoOpNotifierFactory(ClickCliAware):

  def register_cli_options(*args, **kwargs) -> list:
    return []

  @staticmethod
  def create() -> NoOpNotifier:
    return NoOpNotifier()
