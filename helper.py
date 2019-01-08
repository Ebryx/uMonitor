import os
import csv
import json
import time
import base64
import logging
import requests

from crypto import decrypt_file


CONFIG_FILE = 'config.json'

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handle = logging.StreamHandler()
handle.setLevel(logging.INFO)
handle.setFormatter(logging.Formatter('%(asctime)s: %(message)s'))
logger.addHandler(handle)


def read_config():
    if not os.path.isfile(CONFIG_FILE):
        exit('No config file found: %s' % (CONFIG_FILE))

    config = json.load(open(CONFIG_FILE, 'r'))
    if not config.get('processes'):
        config['processes'] = 15

    if config.get('options'):
        options = decrypt_file(config['options'], False)
        load_options(config, options)

    return config


def load_options(config, options):

    if not config.get('options'):
        config['options'] = dict()

    try:
        config['options'] = json.loads(options)
    except json.JSONDecodeError:
        exit('JSON decode error occured while parsing options file.')


def display_endpoints():

    config = read_config()
    if not config.get('endpoints_file'):
        exit('No key `endpoints_file` exists in config.')

    endpoints = [x[0] for x in csv.reader(open(config.get(
        'endpoints_file'), 'r').readlines()[1:]) if len(x) > 0
        if 'sample.domain' not in x[0]]

    for ep in endpoints:
        print('"%s",' % (ep))


def get_slack_user_ids(tags, config):

    if not config['options'].get('slack_bot_access_token'):
        logger.info('`slack_bot_access_token` is required in ' +
                    'options to get user ids.')

        return list()

    response = requests.get(
        'https://slack.com/api/users.list?token=' +
        config['options']['slack_bot_access_token']).json()

    if not(response.get('ok') and response.get('members')):
        logger.info('Failed to get userIDs for link tags: %s' % (tags))

    user_ids = list()
    for uname in tags:
        for member in response['members']:
            if not(member.get('profile') and member[
                    'profile'].get('display_name')):
                continue
            if member['profile']['display_name'] == \
                    uname.replace('@', str()):
                user_ids.append(member['id'])

    logger.info('Detected user ids for slack are: %s' % (user_ids))
    return user_ids


def get_slack_team_ids(tags, config):

    if not config['options'].get('slack_workstation_access_token'):
        logger.info('`slack_workstation_access_token` is required in ' +
                    'options to get team ids.')
        return list()

    response = requests.get(
        'https://slack.com/api/usergroups.list?token=' +
        config['options']['slack_workstation_access_token']).json()

    if not(response.get('ok') and response.get('usergroups')):
        logger.info('Failed to get teamIDs for link tags: %s' % (tags))

    team_ids = list()
    for tname in tags:
        for group in response['usergroups']:
            if not(group.get('handle') and group.get('id')):
                continue

            if group['handle'] == tname.replace('@', str()):
                team_ids.append(group['id'])

    logger.info('Detected team ids for slack are: %s' % (team_ids))
    return team_ids


def send_to_slack(data):

    prepared_string = '*%d/%d* endpoints are up.\n' % (
        data['total'] - len(data['down']), data['total'])

    prepared_string += 'Following endpoints seem to be down.\n'

    for entry in data['down']:
        prepared_string += '> %s  `Status Code: %s`\n' % (entry[0], entry[1])

    config = read_config()
    if not(config.get('options') and config['options'].get('webhooks')):
        logger.info('No webhook is specified. Exiting program.')
        exit()

    for url, data in config['options']['webhooks'].items():

        users = get_slack_user_ids(data.get('tags', list()), config)
        teams = get_slack_team_ids(data.get('tags', list()), config)
        tag_string = ' '.join(['<@%s>' % x for x in users]) + ' '
        tag_string += ' '.join(['<!subteam^%s>' % x for x in teams]) + '\n'

        response, _count = (None, 0)
        while not response and _count < 5:
            try:
                response = requests.post(url, json={
                    'text': tag_string + prepared_string
                })
            except:
                logger.info('Could not send slack request. ' +
                            'Retrying after 10 secs...')
                time.sleep(10)
                _count += 1

        if not response:
            continue

        if response.status_code == 200:
            logger.info('Pushed message to slack successfully.')
        else:
            logger.info('Could not push message to slack: <(%s) %s>' % (
                response.status_code, response.content.decode('utf8')))


if __name__ == "__main__":
    display_endpoints()
