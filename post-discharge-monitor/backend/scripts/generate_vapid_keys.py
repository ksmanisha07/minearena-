import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


def main() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    private_der = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_point = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )
    public_key = base64.urlsafe_b64encode(public_point).rstrip(b"=").decode("ascii")
    private_key_base64 = base64.urlsafe_b64encode(private_der).rstrip(b"=").decode("ascii")
    print(f"MINEARENA_VAPID_PUBLIC_KEY={public_key}")
    print(f"MINEARENA_VAPID_PRIVATE_KEY_B64={private_key_base64}")


if __name__ == "__main__":
    main()
