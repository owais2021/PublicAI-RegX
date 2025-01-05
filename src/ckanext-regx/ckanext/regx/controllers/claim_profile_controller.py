from flask import request, jsonify, redirect, url_for, flash, get_flashed_messages, session
from ckan.plugins import toolkit as tk
from ckanext.regx.lib.otp_manager import OTPManager
import logging

log = logging.getLogger(__name__)


class ClaimProfileController:
    @staticmethod
    def claim_profile():
        """
        Display the claim profile form and reset to the initial state on page load.
        """
        try:
            # Clear session variables for OTP or post-verification states
            session.pop('otp', None)
            session.pop('otp_expiry', None)
            session.pop('email', None)
            log.debug("Reset session to initial state for claim profile.")

            # Fetch flash messages for the page
            flash_messages = get_flashed_messages(with_categories=True)
            return tk.render('claim_profile.html', extra_vars={'flash_messages': flash_messages})
        except Exception as e:
            log.error(f"Error resetting session in claim_profile: {e}")
            flash("An unexpected error occurred. Please try again.", "error")
            return redirect(url_for('regx.claim_profile'))

    log = logging.getLogger(__name__)

    @staticmethod
    def submit_claim_profile():
        """
        Handle form submission to send OTP if the website and email domain match.
        """
        try:
            website = request.form.get('website', '').strip().lower()
            email = request.form.get('email', '').strip().lower()

            log.debug(f"Received website: {website}, email: {email}")

            if not website or not email:
                log.warning("Form submission missing required fields.")
                return jsonify({"status": False, "error": "Both website and email are required."}), 400

            # Extract domains
            website_domain = website.split(
                '//')[-1].split('/')[0].replace('www.', '')
            email_domain = email.split('@')[-1]

            log.debug(
                f"Extracted domains - Website: {website_domain}, Email: {email_domain}")

            # Check if domains match
            if website_domain != email_domain:
                log.warning(f"Domain mismatch: {website_domain} != {email_domain}")  # noqa
                return jsonify({"status": False, "error": "Website and email domains do not match."}), 400

            # Generate and send OTP
            if OTPManager.generate_and_send_otp(email):
                log.info(f"OTP sent to {email}.")
                return jsonify({"status": True, "message": "OTP sent successfully. Check your email."}), 200
            else:
                log.error(f"Failed to send OTP to {email}.")
                return jsonify({"status": False, "error": "Failed to send OTP. Please try again later."}), 500

        except Exception as e:
            log.error(f"Unexpected error in submit_claim_profile: {e}")
            return jsonify({"status": False, "error": "An unexpected error occurred."}), 500

    @staticmethod
    def verify_otp():
        """
        Handle OTP verification and transition to post-verification fields.
        """
        try:
            entered_otp = request.form.get('otp', '').strip()

            if not entered_otp:
                return jsonify({"status": False, "message": "OTP is required."}), 400

            result = OTPManager.verify_otp(entered_otp)
            if result['status']:
                session['otp_verified'] = True
                return jsonify({"status": True, "message": "OTP verified successfully."})
            else:
                return jsonify({"status": False, "message": result['message']}), 400

        except Exception as e:
            log.error(f"Error during OTP verification: {e}")
            return jsonify({"status": False, "message": "An error occurred during OTP verification."}), 500
