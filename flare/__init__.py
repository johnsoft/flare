__version__ = '0.1'

import sys

from .commandline import CommandLine
from .config import Config, Account, Zone
from .utils import APIError, APIRequest, QuitApp, SECURITY_LEVELS


config = None
cmdline = None


def main():
    global config, cmdline

    try:
        config = Config.load()
        cmdline = CommandLine.parse(sys.argv)
        globals()['action_' + cmdline.action]()
    except APIError as ex:
        print(ex.message)
    except QuitApp as ex:
        print(ex.message)


def request(account, action, data):
    data.update({
        'tkn':   account.api_key,
        'email': account.email,
        'a':     action,
    })

    req = APIRequest(data)
    req.dump = cmdline.dump

    ret = req.send()
    if ret['result'] != 'success':
        raise APIError(ret.get('msg', ''))

    return ret


def get_account_and_zone(zone_name):
    zone = config.find_zone(zone_name)
    for account in config.accounts:
        if zone in account.zones:
            return account, zone
    raise QuitApp('Zone {!r} not found in any account.'.format(zone_name))


#
#  ACTIONS START HERE
#


def action_list_accounts():
    if not config.accounts:
        print('No accounts have been added. You can add one with `flare -a ...`.')

    for account in config.accounts:
        print(account.pretty_format())


def action_add_account():
    if config.find_account(cmdline.account_alias, None):
        raise QuitApp('Account alias {0!r} already exists. You can:\n'
            ' - Choose a different alias\n'
            ' - Run `flare -u {0}` to update its metadata'.format(cmdline.account_alias))

    account = Account(cmdline.account_alias, cmdline.email, cmdline.api_key)
    config.accounts.append(account)

    action_update_account()


def action_delete_account():
    account = config.find_account(cmdline.account_alias)
    config.accounts.remove(account)

    config.save()
    print('Deleted account {} ({}).'.format(account.alias, account.email))


def action_update_account():
    account = config.find_account(cmdline.account_alias)

    data = request(account, 'zone_load_multi', {})
    objs = data['response']['zones']['objs']

    del account.zones[:]
    for z in objs:
        zone = Zone(z['zone_name'])
        config.zones.append(zone)
        account.zones.append(zone)

    print(account.pretty_format())

    config.save()
    print('Stored!')


def action_zone_command():
    account, zone = get_account_and_zone(cmdline.zone)
    globals()['zone_command_' + cmdline.zone_command](account, zone)


#
#  ZONE COMMANDS START HERE
#


def zone_command_level(account, zone):
    data = request(account, 'stats', {'z': zone.domain, 'interval': 40})
    stats = data['response']['result']['objs'][0]
    print('Current level: {}'.format(stats['userSecuritySetting']))

    if cmdline.new_level:
        data = request(account, 'sec_lvl', {'z': zone.domain, 'v': cmdline.new_level})
        print('New level: {}'.format(SECURITY_LEVELS[cmdline.new_level]))
