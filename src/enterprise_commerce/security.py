import hashlib
import hmac


def sign_webhook(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def verify_webhook(secret: str, body: bytes, signature: str) -> bool:
    return hmac.compare_digest(sign_webhook(secret, body), signature)

