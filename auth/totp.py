import pyotp
import qrcode
import io
import base64


def generate_secret():
    return pyotp.random_base32()


def verify_code(secret, code):
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)


def get_totp_uri(secret, username):
    """Generate the otpauth:// URI for QR code scanning."""
    totp = pyotp.TOTP(secret)
    issuer = f"{username} @ Oregon Food Supply Chain"
    return totp.provisioning_uri(name=username, issuer_name=issuer)


def generate_qr_base64(uri):
    """Generate a QR code PNG as a base64 string for embedding in an <img> tag."""
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")