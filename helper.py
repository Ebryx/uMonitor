import os
import csv
import json
import time
import base64
import logging
import argparse
import requests


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handle = logging.StreamHandler()
handle.setLevel(logging.INFO)
handle.setFormatter(logging.Formatter('%(asctime)s: %(message)s'))
logger.addHandler(handle)


def define_params():
    parser = argparse.ArgumentParser()
    parser.add_argument('-config', default=os.environ.get('CONFIG_FILE'),
                        help='path to config file for program. ' +
                        '[default: CONFIG_FILE env variable]')
    parser.add_argument('--add', type=str, default='endpoints.csv',
                        help='path to endpoints file to add to config. ' +
                        '[default: endpoints.csv]')

    return parser.parse_args()


def read_config(filename, is_directtext=False):

    if not is_directtext:
        if not os.path.isfile(filename):
            exit('Config file doesn\'t exist: %s\n' % (filename))
        content = open(filename, 'r').read()
    else:
        content = filename

    try:
        config = json.loads(content)
    except json.JSONDecodeError:
        exit('JSON decode error occured while parsing config ' +
             'file: %s\n' % (filename)) if not is_directtext else \
             exit('JSON decode error while parsing config content.\n')

    if not config.get('processes'):
        config['processes'] = 15

    return config


def add_endpoints(config, params):

    endpoints_file = None
    if params.add and os.path.isfile(params.add):
        endpoints_file = params.add
        logger.info('Endpoints file detected from parameters: ' +
                    '%s' % (params.add))
    else:
        logger.info('Endpoints file was not provided in script params. ' +
                    'Fetching endpoints file from main config ' +
                    'file: %s' % (params.config))

        if not config.get('endpoints_file'):
            exit('No endpoints file is provided in config.')

        if not os.path.isfile(config['endpoints_file']):
            exit('File doesn\'t exists for endpoints: %s' % (
                config['endpoints_file']))

        endpoints_file = config['endpoints_file']

    endpoints = list()
    content = open(endpoints_file, 'r').read()
    for line in csv.reader(content.split('\n')[1:]):
        if len(line) > 0 and 'sample.domain' not in line[0]:
            endpoints.append(line[0])

    config['endpoints'] = endpoints
    json.dump(config, open(params.config, 'w'), sort_keys=True, indent=2)
    logger.info('Config file is unified with endpoints: %s' % (params.config))


def get_slack_user_ids(tags, config):

    if not config.get('slack_bot_access_token'):
        logger.info('`slack_bot_access_token` is required ' +
                    'for slack to get user ids.')

        return list()

    response = requests.get(
        'https://slack.com/api/users.list?token=' +
        config['slack_bot_access_token']).json()

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

    if not config.get('slack_workstation_access_token'):
        logger.info('`slack_workstation_access_token` is required ' +
                    'for slack to get team ids.')
        return list()

    response = requests.get(
        'https://slack.com/api/usergroups.list?token=' +
        config['slack_workstation_access_token']).json()

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


def send_to_slack(data, config):

    prepared_string = config.get('slack_prefix_message', str()) + '\n'
    prepared_string += '*%d/%d* endpoints are up.\n' % (
        data['total'] - len(data['down']), data['total'])
    prepared_string += 'Following endpoints seem to be down.\n'

    for entry in data['down']:
        prepared_string += '> %s  *`%s`*\n' % (entry[0], entry[1])

    if not config.get('webhooks'):
        logger.info('No webhook is specified. Skipping slack push.')
        return

    for url, data in config['webhooks'].items():

        users = get_slack_user_ids(data.get('tags', list()), config)
        teams = get_slack_team_ids(data.get('tags', list()), config)
        tag_string = '<!here>' if '@here' in \
                     data.get('tags', list()) else str()
        tag_string += ' '.join(['<@%s>' % x for x in users]) + ' '
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

    params = define_params()
    if params.add:
        config = read_config(params.config)
        add_endpoints(config, params)
