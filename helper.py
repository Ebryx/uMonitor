import os
import csv
import json
import time
import base64
import logging
import requests


CONFIG_FILE = '.config.json'

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

    if not config.get('webhooks'):
        config['webhooks'] = list()

    return config


def load_options(config, options, subkey):

    if not config.get('options'):
        config['options'] = dict()

    try:
        config['options'][subkey] = json.loads(options)
    except json.JSONDecodeError:
        config['options'][subkey] = options


def display_endpoints():

    config = read_config()
    if not config.get('endpoints_file'):
        exit('No key `endpoints_file` exists in config.')

    endpoints = [x[0] for x in csv.reader(open(config.get(
        'endpoints_file'), 'r').readlines()[1:]) if len(x) > 0
        if 'sample.domain' not in x[0]]

    for ep in endpoints:
        print('"%s",' % (ep))


def send_to_slack(data):

    prepared_string = '\n*%d/%d* endpoints are up.\n' % (
        data['total'] - len(data['down']), data['total'])

    prepared_string += 'Following endpoints seem to be down.\n'

    for entry in data['down']:
        prepared_string += '> %s  `Status Code: %s`\n' % (entry[0], entry[1])

    config = read_config()
    for hook in config.get('webhooks'):

        response, _count = (None, 0)
        while not response and _count < 5:
            try:
                response = requests.post(hook, json={'text': prepared_string})
            except:
                logger.info('Could not send slack request. ' +
                            'Retrying after 10 secs...')
                time.sleep(10)
                _count += 1

        if not response:
            continue

        if response.status_code == 200:
            logger.info('Pushed successfully.')
        else:
            logger.info('Could not push message: <(%s) %s>' % (
                response.status_code, response.content.decode('utf8')))


if __name__ == "__main__":
    display_endpoints()
