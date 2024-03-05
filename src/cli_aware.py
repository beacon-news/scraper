from abc import ABC, abstractmethod
import click

class ClickCliAware(ABC):

  @abstractmethod
  def register_cli_options(*args, **kwargs) -> list[click.Option]:
    """
    Should return a list of click.Option objects which will be registered as cli options.
    """
    raise NotImplementedError


# class Something(CliAware):

#   def register_cli_options(self) -> list[click.Option]:

#     opt = click.Option(
#       param_decls=["-r", "--random"],
#       help="random text here",
#       default="foo",
#       show_default=True,
#       show_envvar=True,
#       callback=lambda ctx, param, value: self.__config_self(ctx, param, value),
#     )
#     opt = click.Option(
#       param_decls=["-r", "--random"],
#       help="random text here",
#       default="foo",
#       show_default=True,
#       show_envvar=True,
#     )
#     return [opt]
  
#   def __config_self(self, ctx, param, value):
#     print("configuring with self !!!")
  

# def run(**kwargs):
#   print("running command!")
#   print(kwargs)

# s = Something()
# opts = s.register_cli_options()
# print(opts)

# cli = click.Command(
#   "cli",
#   # None,
#   params=opts,
#   callback=run
# )


# print(cli.make_context("cli", sys.argv[1:]))