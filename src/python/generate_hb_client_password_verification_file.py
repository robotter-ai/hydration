#!/usr/bin/env python3
# Usage: `python generate_hb_client_password_verification_file.py --password <password> --destination </path/to/the/destination>`

"""
Password Verification File Generator

This script creates an encrypted verification file that can be used to validate 
a user's password in the HummingBot client application. The verification is done
by encrypting a known value ("HummingBot") with the user's password and storing
the result in a file named ".password_verification".

The encryption uses the same method as Ethereum keyfiles (v3), which combines
scrypt or pbkdf2 for key derivation with AES-128-CTR for encryption.
"""

import os
import sys
import json
import binascii
import argparse
from typing import Dict, Optional, Union, Any, Tuple
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


def encrypt_value_with_password(password: str, value: str) -> str:
    """
    Encrypt a value using a password, returning the encrypted result as a hex string.
    
    Args:
        password: The password to use for encryption
        value: The value to encrypt
        
    Returns:
        A hexadecimal string containing the encrypted value in Ethereum keyfile v3 format
    """
    password_bytes = password.encode()
    value_bytes = value.encode()
    keyfile_json = _create_ethereum_v3_keyfile(value_bytes, password_bytes)
    json_str = json.dumps(keyfile_json)
    encrypted_value = binascii.hexlify(json_str.encode()).decode()
    return encrypted_value


def _create_ethereum_v3_keyfile(
    message_to_encrypt: bytes, 
    password: bytes, 
    kdf: str = "pbkdf2", 
    work_factor: Optional[int] = None
) -> Dict[str, Any]:
    """
    Create an Ethereum keyfile v3 compatible JSON structure.
    
    Args:
        message_to_encrypt: The data to be encrypted
        password: The password used for encryption
        kdf: Key derivation function to use ('pbkdf2' or 'scrypt')
        work_factor: Work factor for the KDF (determines computational difficulty)
        
    Returns:
        A dictionary containing the encrypted data in Ethereum keyfile v3 format
        
    Raises:
        NotImplementedError: If an unsupported KDF is specified
    """
    # Generate a random salt
    salt = Random.get_random_bytes(16)

    # Use default work factor if none provided
    if work_factor is None:
        work_factor = get_default_work_factor_for_kdf(kdf)

    # Derive encryption key using the specified KDF
    if kdf == 'pbkdf2':
        derived_key = _pbkdf2_hash(
            password,
            hash_name='sha256',
            salt=salt,
            iterations=work_factor,
            dklen=DKLEN,
        )
        kdf_params = {
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
        kdf_params = {
            'dklen': DKLEN,
            'n': work_factor,
            'r': SCRYPT_R,
            'p': SCRYPT_P,
            'salt': encode_hex_no_prefix(salt),
        }
    else:
        raise NotImplementedError(f"KDF not implemented: {kdf}")

    # Generate random initialization vector
    initialization_vector = big_endian_to_int(Random.get_random_bytes(16))
    
    # Split the derived key: first 16 bytes for encryption, last 16 bytes for MAC
    encryption_key = derived_key[:16]
    
    # Encrypt the message
    ciphertext = encrypt_aes_ctr(message_to_encrypt, encryption_key, initialization_vector)
    
    # Generate MAC (Message Authentication Code)
    mac = keccak(derived_key[16:32] + ciphertext)

    # Return the formatted keyfile structure
    return {
        'crypto': {
            'cipher': 'aes-128-ctr',
            'cipherparams': {
                'iv': encode_hex_no_prefix(int_to_big_endian(initialization_vector)),
            },
            'ciphertext': encode_hex_no_prefix(ciphertext),
            'kdf': kdf,
            'kdfparams': kdf_params,
            'mac': encode_hex_no_prefix(mac),
        },
        'version': 3,
        'alias': '',
    }


def store_password_verification(password: str, destination_file_path: str) -> None:
    """
    Create and store a password verification file.
    
    This function encrypts the word "HummingBot" with the provided password
    and stores the result in the specified file path.
    
    Args:
        password: The password to use for encryption
        destination_file_path: The path where the verification file will be stored
        
    Raises:
        IOError: If the file cannot be written
    """
    try:
        # Encrypt the verification word with the user's password
        encrypted_word = encrypt_value_with_password(password, "HummingBot")
        
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(destination_file_path)), exist_ok=True)
        
        # Write the encrypted value to the verification file
        with open(destination_file_path, "w") as verification_file:
            verification_file.write(encrypted_word)
    except IOError as error:
        print(f"Error writing to verification file: {error}", file=sys.stderr)
        raise


def validate_destination_path(destination: Optional[str]) -> str:
    """
    Validate and prepare the destination path.
    
    Args:
        destination: The provided destination path, or None to use current directory
        
    Returns:
        The absolute path to the destination directory
        
    Raises:
        ValueError: If the destination cannot be created or is not writable
    """
    if destination is None:
        # Use current working directory if no destination provided
        destination_dir = os.getcwd()
    else:
        destination_dir = os.path.abspath(destination)
        
        # Create the directory if it doesn't exist
        try:
            os.makedirs(destination_dir, exist_ok=True)
        except OSError as error:
            raise ValueError(f"Cannot create directory {destination_dir}: {error}")
        
        # Check if the directory is writable
        if not os.access(destination_dir, os.W_OK):
            raise ValueError(f"Destination directory {destination_dir} is not writable")
    
    return destination_dir


def create_password_verification_file(password: Optional[str], destination: Optional[str]) -> None:
    """
    Create a password verification file with the given password in the specified destination.
    
    Args:
        password: The password to use for encryption (prompts if None)
        destination: The directory where the verification file will be stored
        
    Raises:
        ValueError: If the destination is invalid
        IOError: If the file cannot be written
    """
    # Prompt for password if not provided
    if password is None:
        password = getpass("Enter your new password: ")
        
        # Validate password is not empty
        if not password:
            raise ValueError("Password cannot be empty")
    
    # Validate and prepare destination path
    destination_dir = validate_destination_path(destination)
    
    # Create full path for the verification file
    verification_file_path = os.path.join(destination_dir, ".password_verification")
    
    # Store the password verification file
    store_password_verification(password, verification_file_path)
    
    print(f"Password verification file created at: {verification_file_path}")


def parse_command_line_arguments() -> Tuple[str, str]:
    """
    Parse command line arguments for password and destination.
    
    Returns:
        Tuple containing the password and destination path
        
    Raises:
        SystemExit: If the arguments are invalid or help is requested
    """
    parser = argparse.ArgumentParser(
        description="Create an encrypted password verification file for HummingBot client."
    )
    
    parser.add_argument(
        "-p", "--password", 
        type=str, 
        help="Password to encrypt and store", 
        required=True
    )
    
    parser.add_argument(
        "-d", "--destination", 
        type=str, 
        help="Destination folder to store the verification file", 
        required=True
    )
    
    args = parser.parse_args()
    return args.password, args.destination


if __name__ == "__main__":
    try:
        password, destination = parse_command_line_arguments()
        create_password_verification_file(password, destination)
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
