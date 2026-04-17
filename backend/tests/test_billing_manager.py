"""Unit tests for BillingResourceManager."""
import sys
import os
import pytest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from abstractions.models.RequestResourceModel import RequestResourceModel
from managers.billing.BillingResourceManager import BillingResourceManager
from tests.conftest import make_request, SAMPLE_USER_ITEM, SAMPLE_ORG_ITEM


# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

SAMPLE_PLAN_ITEM = {
    "id": "plan-1",
    "name": "Pro",
    "tier": "professional",
    "stripe_price_id": "price_abc123",
    "price_monthly": "29",
    "price_yearly": "290",
    "max_members": 0,
    "max_projects": 0,
    "features": '["time tracking","reports","integrations"]',
    "is_active": True,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00",
}

SAMPLE_ORG_WITH_STRIPE = {
    **SAMPLE_ORG_ITEM,
    "stripe_customer_id": "cus_abc123",
    "stripe_subscription_id": "sub_abc123",
}


def _build_mock_db(user_obj=None, plans_list=None, org_obj=None):
    """Build a mock db service with preconfigured repos."""
    mock_db = MagicMock()
    mock_db.users.get_by_id.return_value = user_obj
    mock_db.subscription_plans.list_all.return_value = plans_list or []
    mock_db.organizations.get_by_id.return_value = org_obj
    return mock_db


def _make_user_obj(item):
    """Create a mock user object from a dict."""
    if item is None:
        return None
    obj = MagicMock()
    for k, v in item.items():
        setattr(obj, k, v)
    return obj


# ---------------------------------------------------------------------------
# LIST plans
# ---------------------------------------------------------------------------

def test_list_plans_success():
    mock_db = _build_mock_db(plans_list=[SAMPLE_PLAN_ITEM])

    mgr = BillingResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "list_plans"}))

    assert resp.success is True
    assert "plans" in resp.data
    assert len(resp.data["plans"]) == 1
    assert resp.data["plans"][0]["name"] == "Pro"
    assert resp.data["plans"][0]["tier"] == "professional"


def test_list_plans_empty():
    mock_db = _build_mock_db(plans_list=[])

    mgr = BillingResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "list_plans"}))

    assert resp.success is True
    assert resp.data["plans"] == []


# ---------------------------------------------------------------------------
# CURRENT subscription
# ---------------------------------------------------------------------------

def test_current_subscription():
    mock_db = _build_mock_db(
        user_obj=_make_user_obj(SAMPLE_USER_ITEM),
        org_obj=SAMPLE_ORG_WITH_STRIPE,
    )

    mgr = BillingResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "current"}))

    assert resp.success is True
    assert "subscription" in resp.data
    assert resp.data["subscription"]["planTier"] == "professional"
    assert resp.data["subscription"]["stripeCustomerId"] == "cus_abc123"
    assert resp.data["subscription"]["stripeSubscriptionId"] == "sub_abc123"


def test_current_no_org():
    user_no_org = _make_user_obj({**SAMPLE_USER_ITEM})
    user_no_org.org_id = None

    mock_db = _build_mock_db(user_obj=user_no_org)

    mgr = BillingResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "current"}))

    assert resp.success is True
    assert resp.data["subscription"] is None


# ---------------------------------------------------------------------------
# CHECKOUT
# ---------------------------------------------------------------------------

def test_checkout_success():
    mock_db = _build_mock_db(
        user_obj=_make_user_obj(SAMPLE_USER_ITEM),
        org_obj=SAMPLE_ORG_WITH_STRIPE,
    )

    mock_stripe_service = MagicMock()
    mock_stripe_service.create_checkout_session.return_value = {"url": "https://checkout.stripe.com/session-123"}

    mgr = BillingResourceManager(service_managers={"db": mock_db, "stripe": mock_stripe_service})
    resp = mgr.post(make_request({
        "action": "checkout",
        "priceId": "price_abc123",
        "successUrl": "https://app.zerve.com/billing/success",
        "cancelUrl": "https://app.zerve.com/billing/cancel",
    }))

    assert resp.success is True
    assert "checkoutUrl" in resp.data
    assert resp.data["checkoutUrl"] == "https://checkout.stripe.com/session-123"
    mock_stripe_service.create_checkout_session.assert_called_once_with(
        price_id="price_abc123",
        customer_id="cus_abc123",
        org_id="org-456",
        success_url="https://app.zerve.com/billing/success",
        cancel_url="https://app.zerve.com/billing/cancel",
    )


def test_checkout_no_stripe():
    mock_db = _build_mock_db(user_obj=_make_user_obj(SAMPLE_USER_ITEM))

    mgr = BillingResourceManager(service_managers={"db": mock_db})  # no stripe service
    resp = mgr.post(make_request({"action": "checkout", "priceId": "price_abc123"}))

    assert resp.success is False
    assert resp.status_code == 503
    assert "Billing not configured" in resp.error


# ---------------------------------------------------------------------------
# PORTAL
# ---------------------------------------------------------------------------

def test_portal_success():
    mock_db = _build_mock_db(
        user_obj=_make_user_obj(SAMPLE_USER_ITEM),
        org_obj=SAMPLE_ORG_WITH_STRIPE,
    )

    mock_stripe_service = MagicMock()
    mock_stripe_service.create_portal_session.return_value = {"url": "https://billing.stripe.com/portal-456"}

    mgr = BillingResourceManager(service_managers={"db": mock_db, "stripe": mock_stripe_service})
    resp = mgr.post(make_request({
        "action": "portal",
        "returnUrl": "https://app.zerve.com/billing",
    }))

    assert resp.success is True
    assert "portalUrl" in resp.data
    assert resp.data["portalUrl"] == "https://billing.stripe.com/portal-456"
    mock_stripe_service.create_portal_session.assert_called_once_with(
        customer_id="cus_abc123",
        return_url="https://app.zerve.com/billing",
    )


def test_portal_no_stripe():
    mock_db = _build_mock_db(user_obj=_make_user_obj(SAMPLE_USER_ITEM))

    mgr = BillingResourceManager(service_managers={"db": mock_db})  # no stripe service
    resp = mgr.post(make_request({"action": "portal", "returnUrl": "https://app.zerve.com"}))

    assert resp.success is False
    assert resp.status_code == 503
    assert "Billing not configured" in resp.error


# ---------------------------------------------------------------------------
# WEBHOOK
# ---------------------------------------------------------------------------

def test_webhook_success():
    mock_db = MagicMock()
    mock_stripe_service = MagicMock()
    mock_stripe_service.handle_webhook.return_value = None

    mgr = BillingResourceManager(service_managers={"db": mock_db, "stripe": mock_stripe_service})
    resp = mgr.post(make_request({
        "action": "webhook",
        "payload": '{"type":"checkout.session.completed"}',
        "signature": "sig_abc123",
    }))

    assert resp.success is True
    assert resp.message == "Webhook processed"
    mock_stripe_service.handle_webhook.assert_called_once_with(
        '{"type":"checkout.session.completed"}',
        "sig_abc123",
    )


def test_webhook_no_stripe():
    mock_db = MagicMock()

    mgr = BillingResourceManager(service_managers={"db": mock_db})  # no stripe service
    resp = mgr.post(make_request({"action": "webhook", "payload": "{}", "signature": "sig"}))

    assert resp.success is False
    assert resp.status_code == 503
    assert "Billing not configured" in resp.error


# ---------------------------------------------------------------------------
# PUT not implemented
# ---------------------------------------------------------------------------

def test_put_not_implemented():
    mgr = BillingResourceManager()
    resp = mgr.put(make_request({"action": "update"}))

    assert resp.success is False
    assert resp.status_code == 405


# ---------------------------------------------------------------------------
# DELETE not implemented
# ---------------------------------------------------------------------------

def test_delete_not_implemented():
    mgr = BillingResourceManager()
    resp = mgr.delete(make_request({"action": "remove"}))

    assert resp.success is False
    assert resp.status_code == 405


# ---------------------------------------------------------------------------
# Invalid actions
# ---------------------------------------------------------------------------

def test_get_invalid_action():
    mgr = BillingResourceManager()
    resp = mgr.get(make_request({"action": "nonexistent_action"}))

    assert resp.success is False
    assert resp.status_code == 400


def test_post_invalid_action():
    mgr = BillingResourceManager()
    resp = mgr.post(make_request({"action": "nonexistent_action"}))

    assert resp.success is False
    assert resp.status_code == 400
