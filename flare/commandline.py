from . import __version__
from .utils import QuitApp, DNS_RECORD_TYPES, SECURITY_LEVELS


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
  flare <zone> dns -l
  flare <zone> dns -a <type> <name> <location> [--cloud (on | off)]
  flare <zone> dns -e <name> <location>
  flare <zone> dns -d <name> [<location>]
    View or modify DNS records for the given zone.

  flare <zone> level [<new-level>]
    Displays, and optionally changes, a zone's current security level.
      <new-level> - one of """ + ', '.join(SECURITY_LEVELS) + """
"""


class CommandLine:
    def __init__(self):
        self.dump = False

    def _error(self, message, choices=None):
        if choices is not None:
            message += ' Choices are {}.'.format(', '.join(choices))
        raise QuitApp(message)

    def _next(self, *, missing=None, choices=None, globs=False):
        try:
            while 1:
                arg = next(self._iargs)
                if globs and self._glob_arg(arg):
                    continue
                if choices is not None and arg not in choices:
                    self._error(missing, choices)
                return arg
        except StopIteration:
            if missing is not None:
                self._error(missing, choices)
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

        binary = ret._next(missing='missing argv[0]?')
        arg = ret._next(missing=USAGE, globs=True)

        if arg in ('-a', '--add'):
            ret.action = 'add_account'
            ret.account_alias = ret._next(missing='Need account alias.')
            ret.email = ret._next(missing='Need email address.')
            ret.api_key = ret._next(missing='Need api key.')
        elif arg in ('-d', '--delete'):
            ret.action = 'delete_account'
            ret.account_alias = ret._next(missing='Need account alias.')
        elif arg in ('-u', '--update'):
            ret.action = 'update_account'
            ret.account_alias = ret._next(missing='Need account alias.')
        elif arg in ('-l', '--list'):
            ret.action = 'list_accounts'
        elif arg[0] == '-':
            ret._error('Unexpected argument {!r}.'.format(arg))
        else:
            ret.action = 'zone_command'
            ret.zone = arg
            ret.zone_command = ret._next(missing='Need command name.', globs=True)
            if ret.zone_command == 'dns':
                dns_command = ret._next(missing='Need DNS command.', choices=['-l', '-a', '-e', '-d'])
                if dns_command == '-l':
                    ret.zone_command = 'dns_list'
                elif dns_command == '-a':
                    ret.zone_command = 'dns_add'
                    ret.dns_type = ret._next(missing='Need record type.', choices=DNS_RECORD_TYPES)
                    ret.dns_name = ret._next(missing='Need record name.')
                    ret.dns_location = ret._next(missing='Need record location.')
                    ret.dns_cloud_on = True  # default
                    while 1:
                        arg = ret._next()
                        if not arg:
                            break
                        elif arg == '--cloud':
                            arg = ret._next(missing='Expected on or off after {}.'.format(arg), choices=['on', 'off'])
                            ret.dns_cloud_on = arg == 'on'
                        else:
                            ret._error('Unexpected argument {!r}.'.format(arg))
                elif dns_command == '-e':
                    ret.zone_command = 'dns_edit'
                    ret.dns_name = ret._next(missing='Need record name.')
                    ret.dns_location = ret._next(missing='Need record location.')
                elif dns_command == '-d':
                    ret.zone_command = 'dns_delete'
                    ret.dns_name = ret._next(missing='Need record name.')
                    ret.dns_location = ret._next()
            elif ret.zone_command == 'level':
                ret.new_level = ret._next()
                if ret.new_level is not None and ret.new_level not in SECURITY_LEVELS:
                    ret._error('Invalid security level {!r}. Choices are {}.'.format(
                        ret.new_level, ', '.join(SECURITY_LEVELS)))
            else:
                ret._error('Unknown command {!r}.'.format(ret.zone_command))

        arg = ret._next()
        if arg:
            ret._error('Unexpected argument {!r}.'.format(arg))

        return ret
