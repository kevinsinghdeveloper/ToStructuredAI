"""Billing Resource Manager."""
from abstractions.IResourceManager import IResourceManager
from abstractions.models.ResponseModel import ResponseModel
from abstractions.models.RequestResourceModel import RequestResourceModel
from database.schemas.subscription_plan import SubscriptionPlanItem


class BillingResourceManager(IResourceManager):
    def get(self, req: RequestResourceModel) -> ResponseModel:
        action = req.data.get("action", "")
        if action == "list_plans":
            return self._list_plans(req)
        elif action == "current":
            return self._current(req)
        return ResponseModel(success=False, error="Invalid action", status_code=400)

    def post(self, req: RequestResourceModel) -> ResponseModel:
        action = req.data.get("action", "")
        if action == "checkout":
            return self._checkout(req)
        elif action == "portal":
            return self._portal(req)
        elif action == "webhook":
            return self._webhook(req)
        return ResponseModel(success=False, error="Invalid action", status_code=400)

    def put(self, req): return ResponseModel(success=False, error="Not implemented", status_code=405)
    def delete(self, req): return ResponseModel(success=False, error="Not implemented", status_code=405)

    def _list_plans(self, req):
        try:
            plans_list = self._db.subscription_plans.list_all()
            plans = [SubscriptionPlanItem.from_item(p).to_api_dict() for p in plans_list]
            return ResponseModel(success=True, data={"plans": plans})
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _current(self, req):
        try:
            user = self._db.users.get_by_id(str(req.user_id))
            org_id = user.org_id if user else None
            if not org_id:
                return ResponseModel(success=True, data={"subscription": None})
            org = self._db.organizations.get_by_id(org_id)
            org_dict = org if isinstance(org, dict) else (org.__dict__ if org else {})
            return ResponseModel(success=True, data={"subscription": {
                "planTier": org_dict.get("plan_tier", "free"),
                "stripeCustomerId": org_dict.get("stripe_customer_id"),
                "stripeSubscriptionId": org_dict.get("stripe_subscription_id"),
            }})
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _checkout(self, req):
        try:
            stripe_service = self._service_managers.get("stripe")
            if not stripe_service:
                return ResponseModel(success=False, error="Billing not configured", status_code=503)
            user = self._db.users.get_by_id(str(req.user_id))
            org_id = user.org_id if user else None
            org = self._db.organizations.get_by_id(org_id)
            org_dict = org if isinstance(org, dict) else (org.__dict__ if org else {})
            session = stripe_service.create_checkout_session(
                price_id=req.data.get("priceId"), customer_id=org_dict.get("stripe_customer_id"),
                org_id=org_id, success_url=req.data.get("successUrl"), cancel_url=req.data.get("cancelUrl"))
            return ResponseModel(success=True, data={"checkoutUrl": session.get("url")})
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _portal(self, req):
        try:
            stripe_service = self._service_managers.get("stripe")
            if not stripe_service:
                return ResponseModel(success=False, error="Billing not configured", status_code=503)
            user = self._db.users.get_by_id(str(req.user_id))
            org_id = user.org_id if user else None
            org = self._db.organizations.get_by_id(org_id)
            org_dict = org if isinstance(org, dict) else (org.__dict__ if org else {})
            portal = stripe_service.create_portal_session(
                customer_id=org_dict.get("stripe_customer_id"), return_url=req.data.get("returnUrl"))
            return ResponseModel(success=True, data={"portalUrl": portal.get("url")})
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _webhook(self, req):
        try:
            stripe_service = self._service_managers.get("stripe")
            if not stripe_service:
                return ResponseModel(success=False, error="Billing not configured", status_code=503)
            stripe_service.handle_webhook(req.data.get("payload"), req.data.get("signature"))
            return ResponseModel(success=True, message="Webhook processed")
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)
