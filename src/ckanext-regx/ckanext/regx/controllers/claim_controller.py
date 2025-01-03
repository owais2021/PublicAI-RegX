import logging
from flask import request, jsonify, render_template
from ckan.plugins import toolkit as tk

log = logging.getLogger(__name__)


class ClaimController:
    @staticmethod
    def claim_profile():
        """
        Render the Claim Form page.
        """
        return tk.render("claim_profile.html")

    @staticmethod
    def send_otp():
        """
        Handle the submission of the Claim Form and send OTP.
        """
        website = request.form.get('website')
        email = request.form.get('email')

        if not website or not email:
            return jsonify({"error": "Both website and email are required."}), 400

        # Placeholder logic for sending OTP
        log.info(f"Sending OTP to {email} for website {website}")
        return jsonify({"message": f"OTP sent to {email}"}), 200
