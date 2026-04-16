import pyotp


def generate_secret():
    return pyotp.random_base32()


def verify_code(secret, code):
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)