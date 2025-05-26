# Usage: `python generate_hb_client_password_verification_file.py --password <password> --destination </path/to/the/destination>`

import os
import json
import binascii
import argparse
from typing import Optional
from getpass import getpass

from eth_keyfile.keyfile import (
    DKLEN,
    SCRYPT_P,
    SCRYPT_R,
    Random,
    _pbkdf2_hash,
    _scrypt_hash,
    big_endian_to_int,
    encode_hex_no_prefix,
    encrypt_aes_ctr,
    get_default_work_factor_for_kdf,
    int_to_big_endian,
    keccak,
)


def encrypt_secret_value(password, value: str):
    password_bytes = password.encode()
    value_bytes = value.encode()
    keyfile_json = _create_v3_keyfile_json(value_bytes, password_bytes)
    json_str = json.dumps(keyfile_json)
    encrypted_value = binascii.hexlify(json_str.encode()).decode()
    return encrypted_value


def _create_v3_keyfile_json(message_to_encrypt, password, kdf="pbkdf2", work_factor=None):
    salt = Random.get_random_bytes(16)

    if work_factor is None:
        work_factor = get_default_work_factor_for_kdf(kdf)

    if kdf == 'pbkdf2':
        derived_key = _pbkdf2_hash(
            password,
            hash_name='sha256',
            salt=salt,
            iterations=work_factor,
            dklen=DKLEN,
        )
        kdfparams = {
            'c': work_factor,
            'dklen': DKLEN,
            'prf': 'hmac-sha256',
            'salt': encode_hex_no_prefix(salt),
        }
    elif kdf == 'scrypt':
        derived_key = _scrypt_hash(
            password,
            salt=salt,
            buflen=DKLEN,
            r=SCRYPT_R,
            p=SCRYPT_P,
            n=work_factor,
        )
        kdfparams = {
            'dklen': DKLEN,
            'n': work_factor,
            'r': SCRYPT_R,
            'p': SCRYPT_P,
            'salt': encode_hex_no_prefix(salt),
        }
    else:
        raise NotImplementedError("KDF not implemented: {0}".format(kdf))

    iv = big_endian_to_int(Random.get_random_bytes(16))
    encrypt_key = derived_key[:16]
    ciphertext = encrypt_aes_ctr(message_to_encrypt, encrypt_key, iv)
    mac = keccak(derived_key[16:32] + ciphertext)

    return {
        'crypto': {
            'cipher': 'aes-128-ctr',
            'cipherparams': {
                'iv': encode_hex_no_prefix(int_to_big_endian(iv)),
            },
            'ciphertext': encode_hex_no_prefix(ciphertext),
            'kdf': kdf,
            'kdfparams': kdfparams,
            'mac': encode_hex_no_prefix(mac),
        },
        'version': 3,
        'alias': '',
    }


def store_password_verification(password: str, destination_path: str):
    encrypted_word = encrypt_secret_value(password, "HummingBot")
    with open(destination_path, "w") as f:
        f.write(encrypted_word)


def main(password: Optional[str], destination: Optional[str]):
    if password is None:
        password = getpass("Enter your new password: ")

    if destination is None:
        destination = os.getcwd()
    else:
        os.makedirs(destination, exist_ok=True)

    destination_path = os.path.join(destination, ".password_verification")
    store_password_verification(password, destination_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Store an encrypted password.")
    parser.add_argument("-p", "--password", prompt="1", type=str, help="Password to encrypt and store.", required=True)
    parser.add_argument("-d", "--destination", prompt="2", type=str, help="Destination folder to store the encrypted password file.", required=True)
    args = parser.parse_args()

    main(args.password, args.destination)
