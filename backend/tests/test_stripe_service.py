"""Unit tests for StripeService (DB-related methods)."""
import sys
import os
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.stripe.StripeService import StripeService


def _build_service():
    mock_db = MagicMock()
    svc = StripeService()
    svc.set_db(mock_db)
    return svc, mock_db


class TestStripeServiceInit:
    def test_initializes_without_key(self):
        svc = StripeService()
        svc.initialize()
        assert svc.secret_key == ""

    def test_set_db(self):
        svc, mock_db = _build_service()
        assert svc._db is mock_db


class TestStripeServiceCheckout:
    def test_raises_without_key(self):
        svc, _ = _build_service()
        svc.secret_key = ""
        with pytest.raises(Exception, match="Stripe not configured"):
            svc.create_checkout_session("price_1", "cust_1", "org-1", "/success", "/cancel")

    def test_raises_portal_without_key(self):
        svc, _ = _build_service()
        svc.secret_key = ""
        with pytest.raises(Exception, match="Stripe not configured"):
            svc.create_portal_session("cust_1", "/return")


class TestStripeServiceWebhook:
    def test_raises_without_key(self):
        svc, _ = _build_service()
        svc.secret_key = ""
        with pytest.raises(Exception, match="Stripe not configured"):
            svc.handle_webhook(b"payload", "sig")
