#!/usr/bin/env python3
# Usage: `python generate_ssl_certificates.py --password <password> --destination </path/to/store/the/certificates>`

"""
SSL Certificate Generation Utility

This script generates a set of SSL certificates for secure communication:
- Certificate Authority (CA) key and certificate
- Server key, certificate, and certificate signing request (CSR)
- Client key, certificate, and certificate signing request (CSR)

All keys are RSA 2048-bit keys. The CA private key is encrypted with a password,
while the client key is unencrypted to support libraries that don't handle encrypted keys.
"""
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
import click

# Certificate configuration
CERTIFICATE_SUBJECT = [
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, 'localhost'),
    x509.NameAttribute(NameOID.COMMON_NAME, 'localhost'),
]
# Subject Alternative Name DNS entries
SUBJECT_ALTERNATIVE_NAME_DNS = [x509.DNSName('localhost')]
# Certificate validity in days
VALIDITY_DURATION_DAYS = 365

# Certificate filenames (keeping these as per requirements)
ca_key_filename = 'ca_key.pem'
ca_cert_filename = 'ca_cert.pem'
server_key_filename = 'server_key.pem'
server_cert_filename = 'server_cert.pem'
server_csr_filename = 'server_csr.pem'
client_key_filename = 'client_key.pem'
client_cert_filename = 'client_cert.pem'
client_csr_filename = 'client_csr.pem'


def generate_private_key(password: Optional[str], output_filepath: str) -> rsa.RSAPrivateKey:
    """
    Generate a new RSA private key and save it to a file.
    
    Args:
        password: Optional password to encrypt the private key. If None, the key is unencrypted.
        output_filepath: Path where the private key will be saved.
        
    Returns:
        The generated RSA private key object.
    """
    # Generate a new RSA private key with standard parameters
    private_key = rsa.generate_private_key(
        public_exponent=65537,  # Standard value for RSA
        key_size=2048,          # 2048 bits is currently recommended minimum
        backend=default_backend()
    )

    # Determine encryption algorithm based on password
    encryption_algorithm = serialization.NoEncryption()
    if password:
        encryption_algorithm = serialization.BestAvailableEncryption(password.encode("utf-8"))

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(output_filepath)), exist_ok=True)
    
    # Write private key to file
    with open(output_filepath, "wb") as key_file:
        key_file.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=encryption_algorithm,
            )
        )

    return private_key


def generate_certificate(private_key: rsa.RSAPrivateKey, output_filepath: str) -> x509.Certificate:
    """
    Generate a self-signed certificate using the provided private key.
    
    Args:
        private_key: The RSA private key to use for signing the certificate.
        output_filepath: Path where the certificate will be saved.
        
    Returns:
        The generated X.509 certificate object.
    """
    # Create subject for certificate
    subject = x509.Name(CERTIFICATE_SUBJECT)

    # For self-signed certificates, issuer equals subject
    certificate_issuer = subject

    # Set certificate validity period
    current_datetime = datetime.now(timezone.utc)
    expiration_datetime = current_datetime + timedelta(days=VALIDITY_DURATION_DAYS)

    # Create certificate builder
    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(certificate_issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(current_datetime)
        .not_valid_after(expiration_datetime)
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
    )

    # Sign the certificate with the private key
    certificate = builder.sign(
        private_key,
        hashes.SHA256(),
        default_backend()
    )

    # Write certificate to file
    with open(output_filepath, "wb") as cert_file:
        cert_file.write(certificate.public_bytes(serialization.Encoding.PEM))

    return certificate


def generate_certificate_signing_request(
    private_key: rsa.RSAPrivateKey, 
    output_filepath: str
) -> x509.CertificateSigningRequest:
    """
    Generate a Certificate Signing Request (CSR) using the provided private key.
    
    Args:
        private_key: The RSA private key to use for signing the CSR.
        output_filepath: Path where the CSR will be saved.
        
    Returns:
        The generated X.509 CSR object.
    """
    # CSR subject - using simpler subject than the certificate
    subject = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, 'localhost'),
    ])

    # Create CSR builder with subject alternative names
    builder = (
        x509.CertificateSigningRequestBuilder()
        .subject_name(subject)
        .add_extension(x509.SubjectAlternativeName(SUBJECT_ALTERNATIVE_NAME_DNS), critical=False)
    )

    # Sign the CSR with the private key
    certificate_signing_request = builder.sign(private_key, hashes.SHA256(), default_backend())

    # Write CSR to file
    with open(output_filepath, "wb") as csr_file:
        csr_file.write(certificate_signing_request.public_bytes(serialization.Encoding.PEM))

    return certificate_signing_request


def sign_certificate_request(
    certificate_signing_request: x509.CertificateSigningRequest,
    ca_certificate: x509.Certificate,
    ca_private_key: rsa.RSAPrivateKey,
    output_filepath: str
) -> str:
    """
    Sign a Certificate Signing Request with a CA certificate and private key.
    
    Args:
        certificate_signing_request: The CSR to sign.
        ca_certificate: The CA certificate to use as issuer.
        ca_private_key: The CA private key to sign with.
        output_filepath: Path where the signed certificate will be saved.
        
    Returns:
        The path to the signed certificate.
    """
    # Set certificate validity period
    current_datetime = datetime.now(timezone.utc)
    expiration_datetime = current_datetime + timedelta(days=VALIDITY_DURATION_DAYS)

    try:
        # Create certificate builder
        builder = (
            x509.CertificateBuilder()
            .subject_name(certificate_signing_request.subject)
            .issuer_name(ca_certificate.subject)
            .public_key(certificate_signing_request.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(current_datetime)
            .not_valid_after(expiration_datetime)
            .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        )

        # Copy extensions from CSR to certificate
        for extension in certificate_signing_request.extensions:
            builder = builder.add_extension(extension.value, extension.critical)

        # Sign the certificate with the CA private key
        signed_certificate = builder.sign(
            private_key=ca_private_key,
            algorithm=hashes.SHA256(),
            backend=default_backend(),
        )

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_filepath)), exist_ok=True)

        # Write signed certificate to file
        with open(output_filepath, "wb") as cert_file:
            cert_file.write(signed_certificate.public_bytes(serialization.Encoding.PEM))

        return output_filepath
    except Exception as error:
        print(f"Error signing certificate: {error}", file=sys.stderr)
        raise


def validate_destination_path(ctx, param, value):
    """
    Validate that the destination path exists and is writable.
    
    Args:
        ctx: Click context
        param: Click parameter
        value: Parameter value (destination path)
        
    Returns:
        Validated path if valid, raises an exception otherwise
    """
    if not value:
        raise click.BadParameter("Destination path is required")
    
    destination = os.path.abspath(value)
    
    # Create the directory if it doesn't exist
    try:
        os.makedirs(destination, exist_ok=True)
    except OSError as error:
        raise click.BadParameter(f"Cannot create directory {destination}: {error}")
    
    # Check if the directory is writable
    if not os.access(destination, os.W_OK):
        raise click.BadParameter(f"Destination path {destination} is not writable")
    
    return destination


@click.command()
@click.option(
    "-p", "--password", 
    help="Password to encrypt the CA private key", 
    type=str, 
    required=True,
    prompt="Enter password for CA private key encryption"
)
@click.option(
    "-d", "--destination", 
    help="Path where the certificates will be stored", 
    type=str, 
    required=True,
    callback=validate_destination_path,
    prompt="Enter destination path for certificates"
)
def create_self_signed_certificates(password: str, destination: str):
    """
    Create a complete set of self-signed certificates:
    
    1. Generate CA private key and certificate
    2. Generate server private key, CSR, and certificate (signed by CA)
    3. Generate client private key, CSR, and certificate (signed by CA)
    
    The certificates are stored in the specified destination directory.
    """
    # Create full paths for all certificate files
    certificate_paths = {
        'ca_key': os.path.join(destination, ca_key_filename),
        'ca_cert': os.path.join(destination, ca_cert_filename),
        'server_key': os.path.join(destination, server_key_filename),
        'server_cert': os.path.join(destination, server_cert_filename),
        'server_csr': os.path.join(destination, server_csr_filename),
        'client_key': os.path.join(destination, client_key_filename),
        'client_cert': os.path.join(destination, client_cert_filename),
        'client_csr': os.path.join(destination, client_csr_filename)
    }

    print(f"Generating certificates in {destination}...")

    # Create CA private key and certificate
    print("Generating CA private key and certificate...")
    ca_private_key = generate_private_key(password, certificate_paths['ca_key'])
    generate_certificate(ca_private_key, certificate_paths['ca_cert'])

    # Create server private key and CSR
    print("Generating server private key and CSR...")
    server_private_key = generate_private_key(password, certificate_paths['server_key'])
    generate_certificate_signing_request(server_private_key, certificate_paths['server_csr'])
    
    # Load server CSR
    with open(certificate_paths['server_csr'], 'rb') as server_csr_file:
        server_csr = x509.load_pem_x509_csr(server_csr_file.read(), default_backend())

    # Create client private key and CSR (unencrypted for compatibility)
    print("Generating client private key and CSR...")
    client_private_key = generate_private_key(None, certificate_paths['client_key'])
    generate_certificate_signing_request(client_private_key, certificate_paths['client_csr'])
    
    # Load client CSR
    with open(certificate_paths['client_csr'], 'rb') as client_csr_file:
        client_csr = x509.load_pem_x509_csr(client_csr_file.read(), default_backend())

    # Load CA certificate and private key for signing
    with open(certificate_paths['ca_cert'], 'rb') as ca_cert_file:
        ca_cert = x509.load_pem_x509_certificate(ca_cert_file.read(), default_backend())
    
    with open(certificate_paths['ca_key'], 'rb') as ca_key_file:
        ca_key = serialization.load_pem_private_key(
            ca_key_file.read(),
            password.encode('utf-8'),
            default_backend(),
        )

    # Sign server and client certificates with CA
    print("Signing server certificate...")
    sign_certificate_request(server_csr, ca_cert, ca_key, certificate_paths['server_cert'])
    
    print("Signing client certificate...")
    sign_certificate_request(client_csr, ca_cert, ca_key, certificate_paths['client_cert'])

    print("Certificate generation complete!")
    print(f"Files generated in {destination}:")
    for cert_name, cert_path in certificate_paths.items():
        print(f"  - {os.path.basename(cert_path)}")


if __name__ == '__main__':
    create_self_signed_certificates()
