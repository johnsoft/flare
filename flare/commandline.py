from . import __version__
from .utils import QuitApp, DNS_RECORD_TYPES, SECURITY_LEVELS


USAGE = 'flare ' + __version__ + r"""

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
  flare <zone> dns -l [<record-filter>]
  flare <zone> dns -a <record-values>
  flare <zone> dns -e [<record-filter>] <record-values>
  flare <zone> dns -d <record-filter>
    List/add/edit/delete DNS records for the given zone.
      <record-filter> - A set of criteria identifying the records to modify.
        syntax - [<name>][:<location>]
      <record-values> - The record's new values.
        syntax - [--type (A | CNAME | MX)] [--name <name>] \
                 [--location <location>] [--ttl (auto | <seconds>)] \
                 [--cloud (on | off)] [--prio <prio>]

  flare <zone> level [<new-level>]
    Displays, and optionally changes, a zone's current security level.
      <new-level> - one of """ + ', '.join(SECURITY_LEVELS) + """
"""


class CommandLine:
    def __init__(self):
        self.dump = False
        self._args = None
        self._pos = 0

    def _error(self, message, choices=None):
        if choices is not None:
            message += ' Choices are {}.'.format(', '.join(choices))
        raise QuitApp(message)

    def _prev(self):
        self._pos -= 1

    def _next(self, *, missing=None, choices=None, globs=False):
        while 1:
            if self._pos >= len(self._args):
                if missing is not None:
                    self._error(missing, choices)
                return None

            arg = self._args[self._pos]
            self._pos += 1

            if globs and self._glob_arg(arg):
                continue
            if choices is not None and arg not in choices:
                self._error(missing, choices)
            return arg

    def _next_bool(self, **kwargs):
        text = self._next(choices=('on', 'off'), **kwargs)
        return text == 'on'

    def _glob_arg(self, arg):
        is_glob = True
        if arg == '--dump':
            self.dump = True
        else:
            is_glob = False
        return is_glob

    def _to_int(self, name, num, *, min=None, max=None):
        try:
            num = int(num)
            if (min is not None and num < min) or (max is not None and num > max):
                raise ValueError
        except ValueError:
            self._error('TTL must be a number from {} and {}'.format(min, max))
        return num

    @classmethod
    def parse(cls, argv):
        return cls()._parse(argv)

    def _parse(self, argv):
        self._args = list(argv)

        binary = self._next(missing='missing argv[0]?')
        arg = self._next(missing=USAGE, globs=True)

        if arg in ('-a', '--add'):
            self.action = 'add_account'
            self.account_alias = self._next(missing='Need account alias.')
            self.email = self._next(missing='Need email address.')
            self.api_key = self._next(missing='Need api key.')
        elif arg in ('-d', '--delete'):
            self.action = 'delete_account'
            self.account_alias = self._next(missing='Need account alias.')
        elif arg in ('-u', '--update'):
            self.action = 'update_account'
            self.account_alias = self._next(missing='Need account alias.')
        elif arg in ('-l', '--list'):
            self.action = 'list_accounts'
        elif arg[0] == '-':
            self._error('Unexpected argument {!r}.'.format(arg))
        else:
            self.action = 'zone_command'
            self.zone = arg
            self._parse_zone_command()

        arg = self._next(globs=True)
        if arg:
            self._error('Unexpected argument {!r}.'.format(arg))

        return self

    def _parse_zone_command(self):
        self.zone_command = self._next(missing='Need command name.', globs=True)
        if self.zone_command == 'dns':
            dns_command = self._next(missing='Need DNS command.', choices=['-l', '-a', '-e', '-d'])
            if dns_command == '-l':
                self.zone_command = 'dns_list'
                self.dns_filter = self._next()
            elif dns_command == '-a':
                self.zone_command = 'dns_add'
                self._parse_record_values()
            elif dns_command == '-e':
                self.zone_command = 'dns_edit'
                arg = self._next(missing='Need record filter.')
                if arg[0] == '-':
                    self.dns_filter = None
                    self._prev()
                else:
                    self.dns_filter = arg
                self._parse_record_values()
            elif dns_command == '-d':
                self.zone_command = 'dns_delete'
                self.dns_filter = self._next(missing='Need record filter.')
        elif self.zone_command == 'level':
            self.new_level = self._next()
            if self.new_level is not None and self.new_level not in SECURITY_LEVELS:
                self._error('Invalid security level {!r}. Choices are {}.'.format(
                    self.new_level, ', '.join(SECURITY_LEVELS)))
        else:
            self._error('Unknown command {!r}.'.format(self.zone_command))

    def _parse_record_values(self):
        self.dns_type = None
        self.dns_name = None
        self.dns_location = None
        self.dns_ttl = None
        self.dns_cloud_on = None
        self.dns_prio = None

        while 1:
            arg = self._next(globs=True)
            if arg is None:
                break
            if arg == '--type':
                self.dns_type = self._next(missing='Need type after {!r}'.format(arg), choices=DNS_RECORD_TYPES)
            elif arg == '--name':
                self.dns_name = self._next(missing='Need name after {!r}'.format(arg))
            elif arg == '--location':
                self.dns_location = self._next(missing='Need location after {!r}'.format(arg))
            elif arg == '--ttl':
                arg = self._next(missing='Need TTL after {!r}'.format(arg))
                self.dns_ttl = self._to_int('TTL', arg, min=120, max=4294967295)
            elif arg == '--cloud':
                self.dns_cloud_on = self._next_bool(missing='Invalid option after {!r}.'.format(arg))
            elif arg == '--prio':
                arg = self._next(missing='Need priority after {!r}'.format(arg))
                self.dns_prio = self._to_int('Priority', arg, min=1, max=255)
            else:
                self._prev()
                break
