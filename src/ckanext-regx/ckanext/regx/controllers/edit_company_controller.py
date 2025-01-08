from flask import render_template, session, redirect, url_for, flash
from ckan.plugins import toolkit as tk
import logging

log = logging.getLogger(__name__)


class EditCompanyController:

    @staticmethod
    def edit_company1():
        log.error(f"edit_company1:")
        return render_template('edit_company.html')

    @staticmethod
    def edit_company():
        """
        Render the edit company page after OTP verification.
        """
        try:
            email = session.get('email', None)

            if not email:
                log.warning(
                    "No email in session. Redirecting to claim profile.")
                flash("Session expired. Please start again.", "error")
                return redirect(url_for('regx.claim_profile'))

            return tk.render('edit_company.html', extra_vars={'email': email})
        except Exception as e:
            log.error(f"Error in edit_company: {e}")
            flash("An unexpected error occurred.", "error")
            return redirect(url_for('regx.claim_profile'))
