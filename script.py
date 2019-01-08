import csv
import logging
import requests
from crypto import decrypt_file
from multiprocessing import Process, Pipe
from helper import read_config, send_to_slack


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handle = logging.StreamHandler()
handle.setLevel(logging.INFO)
handle.setFormatter(logging.Formatter('%(asctime)s: %(message)s'))
logger.addHandler(handle)


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
            response = requests.post('http://' + ep.replace(
                'http://', '').replace('https://', ''), timeout=(1, 2))

            if not check_content(ep, str(response.content), config):
                downpoints.append((ep, 'content-mismatch'))
            elif response.status_code >= 500:
                downpoints.append((ep, response.status_code))

        except requests.exceptions.ConnectTimeout:
            downpoints.append((ep, 'conn-timeout'))
        except requests.exceptions.ReadTimeout:
            pass

    connection.send(downpoints)


def main(event, context):

    config = read_config()
    content = decrypt_file(config.get('endpoints_file'), False)

    endpoints = list()
    for line in csv.reader(content.split('\n')[1:]):
        if len(line) > 0 and 'sample.domain' not in line[0]:
            endpoints.append(line[0])

    processes = list()
    connections = list()
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

    send_to_slack({'total': len(endpoints), 'down': downpoints})
    for ep in downpoints:
        logger.info(ep)


if __name__ == "__main__":
    main({}, {})
