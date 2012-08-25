from . import __version__
from .utils import QuitApp, SECURITY_LEVELS


USAGE = 'flare ' + __version__ + """

Local config management:
  flare -a <account> <email> <api-key>
    Add an account to the local config

  flare -d <account>
    Delete an account from the local config

  flare -l
    List all accounts in the local config

  flare -u <account>
    Update locally-stored account metedata

Zone commands:
  flare <zone> level [<new-level>]
    Displays, and optionally changes, a zone's current security level.
      <new-level> - one of """ + ', '.join(SECURITY_LEVELS) + """
"""


class CommandLine:
    def __init__(self):
        self.dump = False

    def _next(self, error=None):
        try:
            while 1:
                arg = next(self._iargs)
                if not self._glob_arg(arg):
                    return arg
        except StopIteration:
            if error:
                raise QuitApp(error)
            return None

    def _glob_arg(self, arg):
        is_glob = True
        if arg == '--dump':
            self.dump = True
        else:
            is_glob = False
        return is_glob

    @classmethod
    def parse(cls, argv):
        ret = cls()
        ret._iargs = iter(argv)

        binary = ret._next('missing argv[0]?')
        arg = ret._next(USAGE)

        if arg in ('-a', '--add'):
            ret.action = 'add_account'
            ret.account_alias = ret._next('Need account alias.')
            ret.email = ret._next('Need email address.')
            ret.api_key = ret._next('Need api key.')
        elif arg in ('-d', '--delete'):
            ret.action = 'delete_account'
            ret.account_alias = ret._next('Need account alias.')
        elif arg in ('-u', '--update'):
            ret.action = 'update_account'
            ret.account_alias = ret._next('Need account alias.')
        elif arg in ('-l', '--list'):
            ret.action = 'list_accounts'
        elif arg[0] == '-':
            raise QuitApp('Unexpected argument {!r}.'.format(arg))
        else:
            ret.action = 'zone_command'
            ret.zone = arg
            ret.zone_command = ret._next('Need command name.')
            if ret.zone_command == 'level':
                ret.new_level = ret._next()
                if ret.new_level is not None and ret.new_level not in SECURITY_LEVELS:
                    raise QuitApp('Invalid security level. Possible choices are {}.'.format(', '.join(SECURITY_LEVELS)))
            else:
                raise QuitApp('Unknown command {!r}.'.format(ret.zone_command))

        arg = ret._next()
        if arg:
            raise QuitApp('Unexpected argument {!r}.'.format(arg))

        return ret
