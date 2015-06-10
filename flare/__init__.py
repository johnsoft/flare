__version__ = '0.1'

import sys

from .commandline import CommandLine
from .config import Config, Account, Zone
from .utils import APIError, APIRequest, format_table, QuitApp, SECURITY_LEVELS


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


def record_name_human_readable(zone, record_name):
    if record_name == zone.domain:
        return '@'
    if record_name.endswith('.' + zone.domain):
        return record_name[: -len(zone.domain) - 1]
    return record_name


def record_name_api_readable(zone, record_name):
    if record_name == '*':
        return '*.' + zone.domain
    return record_name_human_readable(zone, record_name)


def match_record_pattern(zone, records, pattern):
    name, sep, rest = pattern.partition(':')
    location = None
    if sep:
        location = rest

    ret = []
    for rec in records:
        rec_name = record_name_api_readable(zone, rec['name'])
        if name and name.lower() != rec_name.lower():
            continue
        if location and location.lower() != rec['content'].lower():
            continue
        ret.append(rec)
    return ret


def make_record_table(zone, records):
    output = [('Type', 'Name', 'Location', 'SSL', 'TTL', 'Pri', 'Cloud')]
    for rec in records:
        output.append((
            rec['type'],
            record_name_human_readable(zone, rec['name']),
            rec['content'],
            'on' if rec['props']['ssl'] else 'off',
            'auto' if rec['auto_ttl'] else rec['ttl'],
            '' if rec['prio'] is None else rec['prio'],
            'on' if rec['props']['cloud_on'] else 'off' if rec['props']['proxiable'] else "can't"
        ))
    return format_table(output)


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


def zone_command_dns_list(account, zone):
    data = request(account, 'rec_load_all', {'z': zone.domain})
    recs = data['response']['recs']['objs']
    if cmdline.dns_filter is not None:
        recs = match_record_pattern(zone, recs, cmdline.dns_filter)

    print(make_record_table(zone, recs))


def _update_params_with_cmdline_record_values(params):
    if cmdline.dns_type is not None:
        params['type'] = cmdline.dns_type
    if cmdline.dns_name is not None:
        params['name'] = cmdline.dns_name
    if cmdline.dns_location is not None:
        params['content'] = cmdline.dns_location
    if cmdline.dns_ttl is not None:
        params['ttl'] = cmdline.dns_ttl
    if cmdline.dns_cloud_on is not None:
        params['service_mode'] = int(cmdline.dns_cloud_on)
    if cmdline.dns_prio is not None:
        params['prio'] = cmdline.dns_prio


def _update_params_with_record_values(params, zone, record):
    # The API requires you to specify these, even if they're just set to their current values.
    params['type'] = record['type']
    params['name'] = record_name_api_readable(zone, record['name'])
    params['content'] = record['content']
    params['ttl'] = record['ttl']


def zone_command_dns_add(account, zone):
    params = {'z': zone.domain}
    _update_params_with_cmdline_record_values(params)

    data = request(account, 'rec_new', params)
    obj = data['response']['rec']['obj']
    print('Added record.')
    print(make_record_table(zone, [obj]))


def zone_command_dns_edit(account, zone):
    data = request(account, 'rec_load_all', {'z': zone.domain})
    recs = data['response']['recs']['objs']
    if cmdline.dns_filter is not None:
        recs = match_record_pattern(zone, recs, cmdline.dns_filter)

    objs = []

    for rec in recs:
        params = {'z': zone.domain, 'id': rec['rec_id']}
        _update_params_with_record_values(params, zone, rec)
        _update_params_with_cmdline_record_values(params)
        data = request(account, 'rec_edit', params)
        objs.append(data['response']['rec']['obj'])

    print('Updated {} records.'.format(len(objs)))
    if objs:
        print(make_record_table(zone, objs))


def zone_command_dns_delete(account, zone):
    data = request(account, 'rec_load_all', {'z': zone.domain})
    recs = data['response']['recs']['objs']
    recs = match_record_pattern(zone, recs, cmdline.dns_filter)

    for rec in recs:
        params = {'z': zone.domain, 'id': rec['rec_id']}
        data = request(account, 'rec_delete', params)

    print('Deleted {} records.'.format(len(recs)))
    if recs:
        print(make_record_table(zone, recs))


def zone_command_level(account, zone):
    data = request(account, 'stats', {'z': zone.domain, 'interval': 40})
    stats = data['response']['result']['objs'][0]

    level = stats['userSecuritySetting']
    level = level.replace('\u2019', "'")  # fix unicode bug on some terminals
    print('Current level: {}'.format(level))

    if cmdline.new_level is not None:
        data = request(account, 'sec_lvl', {'z': zone.domain, 'v': cmdline.new_level})
        print('New level: {}'.format(SECURITY_LEVELS[cmdline.new_level]))
