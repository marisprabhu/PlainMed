"""Generate a self-signed certificate for testing on a phone.

Why this is needed
------------------
Browsers only expose the camera (getUserMedia) on a *secure context*.
localhost counts as one, which is why the live viewfinder works on the
development laptop. A phone reaching the laptop at http://192.168.x.x does
not, so the camera is blocked there and the app falls back to the file
input.

For a full mobile test - live viewfinder, installable app - the LAN address
has to be served over HTTPS. This mints a certificate covering this
machine's local addresses so that is possible without a public domain.

The browser will warn that the certificate is not trusted, because it is
self-signed. That is expected: tap through it. This is for testing on your
own network and nothing else.

    python scripts/make_dev_cert.py
    python -m uvicorn plainmed.api.app:app --app-dir src --host 0.0.0.0 \
        --port 8443 --ssl-keyfile certs/dev-key.pem --ssl-certfile certs/dev-cert.pem
"""

from __future__ import annotations

import datetime
import ipaddress
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CERT_DIR = ROOT / "certs"


def local_addresses() -> list[str]:
    """Every address a phone might use to reach this machine."""
    found = {"127.0.0.1"}
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe.connect(("10.255.255.255", 1))
        found.add(probe.getsockname()[0])
        probe.close()
    except Exception:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            found.add(info[4][0])
    except Exception:
        pass
    return sorted(found)


def main() -> int:
    try:
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID
    except ImportError:
        print("Install the generator first:  pip install cryptography")
        return 1

    addresses = local_addresses()
    print("Certificate will cover:")
    for address in addresses:
        print(f"  https://{address}:8443")
    print("  https://localhost:8443")

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "PlainMed dev")])

    alt_names: list[x509.GeneralName] = [
        x509.DNSName("localhost"),
        x509.DNSName(socket.gethostname()),
    ]
    for address in addresses:
        try:
            alt_names.append(x509.IPAddress(ipaddress.ip_address(address)))
        except ValueError:
            continue

    now = datetime.datetime.now(datetime.timezone.utc)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=5))
        # Short-lived on purpose: a development certificate should not
        # outlive the testing it was made for.
        .not_valid_after(now + datetime.timedelta(days=90))
        .add_extension(x509.SubjectAlternativeName(alt_names), critical=False)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .sign(key, hashes.SHA256())
    )

    CERT_DIR.mkdir(exist_ok=True)
    key_path = CERT_DIR / "dev-key.pem"
    cert_path = CERT_DIR / "dev-cert.pem"

    key_path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    cert_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))

    print(f"\nWrote {cert_path.relative_to(ROOT)} and {key_path.relative_to(ROOT)}")
    print("\nStart the server with:")
    print("  python -m uvicorn plainmed.api.app:app --app-dir src --host 0.0.0.0 \\")
    print("      --port 8443 --ssl-keyfile certs/dev-key.pem --ssl-certfile certs/dev-cert.pem")
    print("\nThe browser will warn that this certificate is untrusted. It is")
    print("self-signed, so that warning is correct - tap through it. Testing")
    print("on your own network only; never use this certificate in production.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
