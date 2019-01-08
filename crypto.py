import os
import string
import logging
import random
import argparse
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

KEY_LENGTH = 32
IV_LENGTH = 16


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handle = logging.StreamHandler()
handle.setLevel(logging.INFO)
handle.setFormatter(logging.Formatter('%(asctime)s: %(message)s'))
logger.addHandler(handle)


def define_params():
    parser = argparse.ArgumentParser()
    parser.add_argument('endpoints', help='path to csv file for endpoints.')
    parser.add_argument('--new', action='store_true', help='creates new ' +
                        'random keys if you are doing encryption.')
    parser.add_argument('-E', action='store_true',
                        help='encrypts the endpoints file.')
    parser.add_argument('-D', action='store_true',
                        help='decrypts the endpoints file.')

    return parser.parse_args()


# use this to generate new random keys.
def get_random_string(size):
    return ''.join(random.SystemRandom().choice(
        string.ascii_uppercase + string.digits)
        for _ in range(size)).encode('utf8')


def adjust_padding(data, block_size, unpad=False):

    if not unpad:
        padder = padding.PKCS7(block_size * 8).padder()
        padded_data = padder.update(data.encode('utf8'))
        padded_data += padder.finalize()
        return padded_data

    unpadder = padding.PKCS7(block_size * 8).unpadder()
    data = unpadder.update(data)
    data += unpadder.finalize()
    return data.decode('utf8')


def encrypt_file(params):

    csvfile = params.endpoints
    if not os.path.isfile(csvfile):
        exit('No file exists: %s' % (csvfile))

    if params.new:
        aes_key = get_random_string(KEY_LENGTH)
        aes_iv = get_random_string(IV_LENGTH)

    else:
        if not (os.environ.get('AES_KEY') and os.environ.get('AES_IV')):
            exit('`AES_KEY`, `AES_IV` don\'t exist in environment variables.')

        aes_key = os.environ.get('AES_KEY').encode('utf8')
        aes_iv = os.environ.get('AES_IV').encode('utf8')

    content = open(csvfile, 'r').read()
    content = adjust_padding(content, len(aes_key))
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(aes_iv),
                    backend=default_backend())

    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(content) + encryptor.finalize()

    open('_' + csvfile, 'wb').write(ciphertext)
    open('_keys', 'wb').writelines([
        b'export AES_KEY=%s\n' % (aes_key),
        b'export AES_IV=%s\n' % (aes_iv)
    ])

    logger.info('Successfully encrypted endpoints ' +
                'in: %s' % ('_' + csvfile))
    logger.info('Encryption keys can be found in: %s' % ('_keys'))


def decrypt_file(csvfile, write_to_file=True):
    if not os.path.isfile:
        exit('No file exists: %s' % (csvfile))

    # aes_key = open('_keys', 'rb').readlines()[0].strip(b'\n')
    # aes_iv = open('_keys', 'rb').readlines()[1].strip(b'\n')
    if not (os.environ.get('AES_KEY') and os.environ.get('AES_IV')):
        exit('`AES_KEY`, `AES_IV` don\'t exist in environment variables.')

    aes_key = os.environ.get('AES_KEY').encode('utf8')
    aes_iv = os.environ.get('AES_IV').encode('utf8')

    ciphertext = open(csvfile, 'rb').read()
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(aes_iv),
                    backend=default_backend())

    decryptor = cipher.decryptor()
    content = decryptor.update(ciphertext) + decryptor.finalize()
    content = adjust_padding(content, len(aes_key), unpad=True)

    if write_to_file:
        open('_decrypted_' + csvfile, 'w').write(content)
        logger.info('Successfully decrypted endpoints in: %s' % (
            '_decrypted_' + csvfile))

    else:
        return content


if __name__ == "__main__":
    params = define_params()

    if params.E:
        encrypt_file(params)
    elif params.D:
        decrypt_file(params.endpoints)
