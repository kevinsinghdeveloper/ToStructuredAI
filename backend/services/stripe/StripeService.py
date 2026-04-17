"""Stripe billing service."""
import os
from abstractions.IServiceManagerBase import IServiceManagerBase


class StripeService(IServiceManagerBase):
    def __init__(self, config=None):
        super().__init__(config)
        self.secret_key = os.getenv("STRIPE_SECRET_KEY", "")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
        self._db = None

    def initialize(self):
        if not self.secret_key:
            print("Warning: STRIPE_SECRET_KEY not set. Billing disabled.")

    def set_db(self, db_service):
        self._db = db_service

    def create_checkout_session(self, price_id, customer_id, org_id, success_url, cancel_url):
        if not self.secret_key:
            raise Exception("Stripe not configured")
        import stripe
        stripe.api_key = self.secret_key
        params = {"mode": "subscription", "line_items": [{"price": price_id, "quantity": 1}],
                  "success_url": success_url, "cancel_url": cancel_url, "metadata": {"org_id": org_id}}
        if customer_id:
            params["customer"] = customer_id
        session = stripe.checkout.Session.create(**params)
        return {"url": session.url, "id": session.id}

    def create_portal_session(self, customer_id, return_url):
        if not self.secret_key:
            raise Exception("Stripe not configured")
        import stripe
        stripe.api_key = self.secret_key
        session = stripe.billing_portal.Session.create(customer=customer_id, return_url=return_url)
        return {"url": session.url}

    def handle_webhook(self, payload, signature):
        if not self.secret_key:
            raise Exception("Stripe not configured")
        import stripe
        stripe.api_key = self.secret_key
        event = stripe.Webhook.construct_event(payload, signature, self.webhook_secret)
        if event.type == "checkout.session.completed":
            session = event.data.object
            org_id = session.metadata.get("org_id")
            if org_id and self._db:
                from datetime import datetime
                self._db.organizations.raw_update_item(
                    Key={"id": org_id},
                    UpdateExpression="SET stripe_customer_id = :c, stripe_subscription_id = :s, plan_tier = :p, updated_at = :u",
                    ExpressionAttributeValues={":c": session.customer, ":s": session.subscription,
                                               ":p": "professional", ":u": datetime.utcnow().isoformat()})
        return True
