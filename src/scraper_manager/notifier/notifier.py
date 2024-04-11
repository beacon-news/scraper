from abc import ABC, abstractmethod

class Notifier(ABC):

  @abstractmethod
  def send_done_notification(self, ids: list[dict]):
    raise NotImplementedError
