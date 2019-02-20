import os
import logging
import requests
from ebryx.crypto import decrypt_file
from multiprocessing import Process, Pipe
from helper import read_config, send_to_slack
from http.client import responses as http_responses


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handle = logging.StreamHandler()
handle.setLevel(logging.INFO)
handle.setFormatter(logging.Formatter('%(asctime)s: %(message)s'))
logger.addHandler(handle)


HEADERS = {
    'User-Agent': os.environ.get('CUSTOM_USER_AGENT')
    if os.environ.get('CUSTOM_USER_AGENT') else 'requests-py3-lambda'}


def chunk_list(endpoints_list, chunk_size):

    for i in range(0, len(endpoints_list), chunk_size):
        yield endpoints_list[i:i+chunk_size]


def check_content(endpoint, content, config):

    if not config.get('options'):
        return True

    if not config['options'].get('endpoints'):
        return True

    for ep_name, ep_options in config['options']['endpoints'].items():
        if ep_name != endpoint:
            continue

        if not ep_options.get('strings'):
            return True

        for str_token in ep_options['strings']:
            if str_token not in content:
                return False

    return True


def check_endpoints_status(endpoints_list, connection, config):

    downpoints = list()
    for ep in endpoints_list:
        try:
            auth = config['options']['endpoints'][ep]['auth'] \
                if config.get('options') and config['options'] \
                .get('endpoints') and config['options']['endpoints'] \
                .get(ep) and config['options']['endpoints'][ep].get('auth') \
                else dict()

            if 'user' in auth and 'pass' in auth:

                logger.info(str())
                logger.info('Basic Auth for: %s', ep)

                response = requests.get('http://' + ep.replace(
                    'http://', '').replace('https://', ''),
                    headers=HEADERS, auth=(auth['user'], auth['pass']),
                    timeout=(1, 2))
            else:
                response = requests.get('http://' + ep.replace(
                    'http://', '').replace('https://', ''),
                    headers=HEADERS, timeout=(1, 2))

            if not check_content(ep, str(response.content), config):
                downpoints.append((ep, '<reason: str-mismatch>'))
                continue

            if response.status_code >= 500:
                try:
                    code_desc = http_responses[response.status_code]
                except KeyError:
                    code_desc = None

                downpoints.append((ep, '<status-code: %s (%s)>' % (
                    response.status_code, code_desc)))

        except requests.exceptions.ConnectTimeout:
            downpoints.append((ep, '<reason: conn-timeout>'))
        except requests.exceptions.ReadTimeout:
            pass

    connection.send(downpoints)


def main(event, context):

    if not os.environ.get('CONFIG_FILE'):
        exit('No CONFIG_FILE environment variable exists.\n')

    config_file = os.environ['CONFIG_FILE']
    if config_file.startswith(('http', 'https', 'ftp')):
        logger.info('Config file prefix tells program to fetch it online.')
        logger.info('Fetching config file: %s' % (config_file))
        response = requests.get(config_file)
        if response.status_code < 400:
            ciphertext = response.content
        else:
            logger.info('Could not fetch config file: %s' % (response))
            exit('Exiting program.\n')

    else:
        logger.info('Config file prefix tells program to search ' +
                    'for it on filesystem.')

        if not os.path.isfile(config_file):
            exit('Config file doesn\'t exist on ' +
                 'filesystem: %s\n' % (config_file))

        ciphertext = open(config_file, 'rb').read()

    content = decrypt_file(ciphertext, write_to_file=False, is_ciphertext=True)
    config = read_config(content, is_directtext=True)

    if not config.get('endpoints'):
        exit('No endpoints detected in config file.\n')

    processes, connections = list(), list()
    endpoints = config['endpoints']

    if config['processes'] > len(endpoints):
        config['processes'] = len(endpoints)

    for elist in chunk_list(endpoints, len(endpoints) // config['processes']):

        parent, child = Pipe()
        connections.append(parent)

        process = Process(target=check_endpoints_status,
                          args=(elist, child, config,))

        processes.append(process)

    for process in processes:
        process.start()

    for process in processes:
        process.join()

    downpoints = list()
    for connection in connections:
        downpoints.extend(connection.recv())

    if downpoints:
        send_to_slack({'total': len(endpoints), 'down': downpoints}, config)
        for ep in downpoints:
            logger.info(ep)


if __name__ == "__main__":

    # I see an emoji, what do you see?
    main({}, {})
