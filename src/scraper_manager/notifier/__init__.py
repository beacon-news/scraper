import click
from cli_aware import ClickCliAware
from scraper_manager.notifier.notifier import Notifier
from scraper_manager.notifier.noop_notifier import NoOpNotifierFactory
from scraper_manager.notifier.redis_streams_notifier import *

notifier_factories = {
  "noop": NoOpNotifierFactory,
  "redis_streams": RedisStreamsNotifierFactory,
}

class NotifierFactory(ClickCliAware):

  config = {}

  def register_cli_options() -> list:
    opts = []
    
    store_opt = click.Option(
      param_decls=["--notifier"],
      type=click.Choice(notifier_factories.keys()),
      default="noop",
      show_default=True,
      envvar="NOTIFIER_TYPE",
      show_envvar=True,
      callback=lambda ctx, param, value: NotifierFactory.config.update({'type': value})
    )
    opts.append(store_opt)
    for factory in notifier_factories.values():
      opts.extend(factory.register_cli_options())
    return opts

  @staticmethod
  def create() -> Notifier:
    return notifier_factories[NotifierFactory.config['type']].create()