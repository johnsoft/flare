from configparser import ConfigParser
import os

from .utils import QuitApp


NOT_GIVEN = object()

CONFIG_FILE = os.path.expanduser('~/.flare')


def intmap_to_list(intmap):
    if not intmap:
        return []
    maxnum = max(intmap) + 1
    ret = [intmap.get(i) for i in range(maxnum)]
    return list(filter(None, ret))


class Config:
    def __init__(self):
        self.accounts = []
        self.zones = []

    def find_account(self, alias, default=NOT_GIVEN):
        for account in self.accounts:
            if account.alias == alias or account.email == alias:
                return account
        if default is NOT_GIVEN:
            raise QuitApp('Account {!r} not found.'.format(alias))
        return None

    def find_zone(self, alias, default=NOT_GIVEN):
        for zone in self.zones:
            if zone.domain == alias:
                return zone
        if default is NOT_GIVEN:
            raise QuitApp('Zone {!r} not found.'.format(alias))
        return None

    @classmethod
    def load(cls):
        ini = ConfigParser(interpolation=None)
        if not os.path.exists(CONFIG_FILE):
            return cls()  # first run - just use a fresh config

        try:
            with open(CONFIG_FILE) as file:
                ini.read_file(file)
            return cls.ini_to_config(ini)
        except Exception:
            print('Warning - corrupt or unreadable config file, reverting to defaults.')
            return cls()

    @classmethod
    def ini_to_config(cls, ini):
        ret = cls()
        accounts = {}
        zones = {}

        for sname, section in ini.items():
            if sname == ini.default_section:
                continue
            if sname[:8] == 'account:':
                accounts[int(sname[8:])] = account = Account(section['alias'], section['email'], section['api-key'])
                if 'zones' in section:
                    account.zones = [int(n) for n in section['zones'].split(',')]
            elif sname[:5] == 'zone:':
                zones[int(sname[5:])] = zone = Zone(section['domain'])

        for account in accounts.values():
            account.zones = [zones[z] for z in account.zones]

        ret.accounts = intmap_to_list(accounts)
        ret.zones = intmap_to_list(zones)

        return ret

    def save(self):
        ini = ConfigParser(interpolation=None)

        # cleanup unreferenced items
        self.zones = [z for z in self.zones if any(z in a.zones for a in self.accounts)]

        for a, account in enumerate(self.accounts):
            ini['account:{}'.format(a)] = {
                'alias':   account.alias,
                'email':   account.email,
                'api-key': account.api_key,
                'zones':   ','.join(str(self.zones.index(z)) for z in account.zones),
            }
        for z, zone in enumerate(self.zones):
            ini['zone:{}'.format(z)] = {
                'domain': zone.domain,
            }
        with open(CONFIG_FILE, 'w') as file:
            ini.write(file)


class Account:
    def __init__(self, alias, email, api_key):
        self.alias = alias
        self.email = email
        self.api_key = api_key
        self.zones = []

    def pretty_format(self):
        ret = 'Account {}, email={}\nZones:'.format(self.alias, self.email)
        for zone in self.zones:
            ret += '\n - {}'.format(zone.domain)
        return ret


class Zone:
    def __init__(self, domain):
        self.domain = domain
