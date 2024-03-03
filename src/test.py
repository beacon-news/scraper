import argparse


def task_a(alpha):
    print('task a', alpha)


def task_b(beta, gamma):
    print('task b', beta, gamma)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='subparsers')

    parser_a = subparsers.add_parser('task_a')
    parser_a.add_argument(
        '-a', '--alpha', dest='alpha', help='Alpha description')

    parser_b = subparsers.add_parser('task_b')
    parser_b.add_argument(
        '-b', '--beta', dest='beta', help='Beta description')
    parser_b.add_argument(
        '-g', '--gamma', dest='gamma', default=42, help='Gamma description')

    kwargs = vars(parser.parse_args())
    print(kwargs)
    print(kwargs.pop('subparsers'))
    print(globals())
    # globals()[kwargs.pop('subparser')](**kwargs)



# {
#     '__name__': '__main__', 
#     '__doc__': None, 
#     '__package__': None, 
#     '__loader__': <_frozen_importlib_external.SourceFileLoader object at 0x7eff2af19ae0>, 
#     '__spec__': None,
#     '__annotations__': {}, 
#     '__builtins__': <module 'builtins' (built-in)>,
#     '__file__': '/home/adam/UBB/master_pdae/dissertation/beacon-news/scraper/src/test.py', 
#     '__cached__': None, 
#     'argparse': <module 'argparse' from '/usr/lib/python3.10/argparse.py'>,
#     'task_a': <function task_a at 0x7eff2b0bfd90>, 
#     'task_b': <function task_b at 0x7eff2af868c0>, 
#     'parser': ArgumentParser(prog='test.py', usage=None, description=None, formatter_class=<class 'argparse.HelpFormatter'>, conflict_handler='error', add_help=True),
#     'subparsers': _SubParsersAction(option_strings=[], dest='subparser', nargs='A...', const=None, default=None, type=None, choices={'task_a': ArgumentParser(prog='test.py task_a', usage=None, description=None, formatter_class=<class 'argparse.HelpFormatter'>, conflict_handler='error', add_help=True), 'task_b': ArgumentParser(prog='test.py task_b', usage=None, description=None, formatter_class=<class 'argparse.HelpFormatter'>, conflict_handler='error', add_help=True)}, required=False, help=None, metavar=None), 
#     'parser_a': ArgumentParser(prog='test.py task_a', usage=None, description=None, formatter_class=<class 'argparse.HelpFormatter'>, conflict_handler='error', add_help=True), 
#     'parser_b': ArgumentParser(prog='test.py task_b', usage=None, description=None, formatter_class=<class 'argparse.HelpFormatter'>, conflict_handler='error', add_help=True), 'kwargs': {'alpha': None}}