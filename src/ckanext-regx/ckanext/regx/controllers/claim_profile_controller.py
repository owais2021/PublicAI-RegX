from flask import request, redirect, url_for, flash, jsonify, session, get_flashed_messages
from ckan.plugins import toolkit as tk
from ckanext.regx.lib.otp_manager import OTPManager
import logging

log = logging.getLogger(__name__)


class ClaimProfileController:
    @staticmethod
    def claim_profile():
        """
        Display the claim profile form and reset the initial state on page load.
        """
        try:
            # Reset OTP-related session variables
            session.pop('otp', None)
            session.pop('otp_expiry', None)
            session.pop('otp_verified', None)
            log.debug("Session reset for claim profile.")

            flash_messages = get_flashed_messages(with_categories=True)
            return tk.render('claim_profile.html', extra_vars={'flash_messages': flash_messages})
        except Exception as e:
            log.error(f"Error in claim_profile: {e}")
            flash("An unexpected error occurred. Please try again.", "error")
            return redirect(url_for('regx.claim_profile'))

    @staticmethod
    def submit_claim_profile():
        """
        Handle form submission for OTP generation.
        """
        try:
            website = request.form.get('website', '').strip().lower()
            email = request.form.get('email', '').strip().lower()

            if not website or not email:
                return jsonify({"status": False, "message": "Website and email are required."})

            website_domain = website.split(
                '//')[-1].split('/')[0].replace('www.', '')
            email_domain = email.split('@')[-1]

            if website_domain != email_domain:
                return jsonify({"status": False, "message": "Website and email domains do not match."})

            otp_sent = OTPManager.generate_and_send_otp(email)
            if otp_sent:
                session['email'] = email
                return jsonify({"status": True, "message": "OTP sent successfully. Check your email."})
            else:
                return jsonify({"status": False, "message": "Failed to send OTP. Please try again later."})
        except Exception as e:
            log.error(f"Error in submit_claim_profile: {e}")
            return jsonify({"status": False, "message": "An unexpected error occurred. Please try again."})

    @staticmethod
    def verify_otp():
        """
        Handle OTP verification and redirect to edit_company page on success.
        """
        try:
            entered_otp = request.form.get('otp', '').strip()

            if not entered_otp:
                return jsonify({"status": False, "error": "OTP is required."})

            result = OTPManager.verify_otp(entered_otp)
            if result['status']:
                session.pop('otp', None)
                session.pop('otp_expiry', None)
                session['otp_verified'] = True
                return jsonify({"redirect_url": url_for('regx.edit_company')})
            else:
                return jsonify({"status": False, "error": result['message']})
        except Exception as e:
            log.error(f"Error in verify_otp: {e}")
            return jsonify({"status": False, "error": "An unexpected error occurred during verification."})
