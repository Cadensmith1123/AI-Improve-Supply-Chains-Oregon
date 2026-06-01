"""
Authentication & Session Security:
  "password reset tokens must be ... expiring."
"""

import time

import pytest
from flask import Flask

from auth.tokens import sign_reset_token, verify_reset_token


pytestmark = pytest.mark.unit


@pytest.fixture
def app_ctx():
    app = Flask("reset_token_test")
    app.config["SECRET_KEY"] = "unit-test-secret"
    with app.app_context():
        yield


def test_reset_token_expires_after_max_age(app_ctx):
    """A reset token older than max_age is rejected."""
    tok = sign_reset_token(123)
    assert verify_reset_token(tok) == 123          # valid now
    time.sleep(2.2)
    assert verify_reset_token(tok, max_age=1) is None   # expired
