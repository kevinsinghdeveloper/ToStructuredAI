from flask import request, jsonify
from abstractions.IController import IController
from abstractions.models.RequestResourceModel import RequestResourceModel
from utils.auth_utils import token_required


class BillingController(IController):
    def register_all_routes(self):
        self.register_route("/api/billing/plans", "billing_plans", self.get_plans, "GET")
        self.register_route("/api/billing/current", "billing_current", self.get_current, "GET")
        self.register_route("/api/billing/checkout", "billing_checkout", self.create_checkout, "POST")
        self.register_route("/api/billing/portal", "billing_portal", self.create_portal, "POST")
        self.register_route("/api/billing/webhook", "billing_webhook", self.handle_webhook, "POST")

    def get_resource_manager(self):
        return self._resource_manager

    @token_required
    def get_plans(self):
        result = self._resource_manager.get(RequestResourceModel(data={"action": "list_plans"}))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def get_current(self):
        result = self._resource_manager.get(RequestResourceModel(
            data={"action": "current"}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def create_checkout(self):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.post(RequestResourceModel(
            data={"action": "checkout", **data}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def create_portal(self):
        result = self._resource_manager.post(RequestResourceModel(
            data={"action": "portal"}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    def handle_webhook(self):
        payload = request.get_data(as_text=True)
        sig_header = request.headers.get("Stripe-Signature", "")
        result = self._resource_manager.post(RequestResourceModel(
            data={"action": "webhook", "payload": payload, "signature": sig_header}))
        return jsonify(result.to_dict()), result.status_code
