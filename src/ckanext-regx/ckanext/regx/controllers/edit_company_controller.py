from flask import render_template, session, redirect, url_for, flash, request, jsonify
from ckan.plugins import toolkit as tk
from ckanext.regx.lib.database import connect_to_db, close_db_connection
from ckanext.regx.lib.otp_manager import OTPManager
import logging

log = logging.getLogger(__name__)


class EditCompanyController:

    @staticmethod
    def get_company(company_id):

        connection = connect_to_db()
        company = None
        if connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT id, company_name, website, email_address FROM regx_company WHERE id = %s", (company_id,))
                    company = cursor.fetchone()
            finally:
                close_db_connection(connection)
        return company

    @staticmethod
    def edit_company(company_id):
        if request.method == 'POST':
            if 'email' in request.form:  # Assuming sending OTP
                return EditCompanyController.send_otp()
            elif 'otp' in request.form:  # Assuming verifying OTP
                return EditCompanyController.verify_otp(company_id)
            # Proceed to update only if OTP is verified
            elif session.get('otp_verified'):
                return EditCompanyController.update_record(company_id)
        else:
            company = EditCompanyController.get_company(company_id)
            if company:
                return render_template('edit_company1.html', company=company, company_id=company_id)
            else:
                flash('No company found')
                return redirect(url_for('regx.edit_company', company_id=company_id))

    @staticmethod
    def send_otp():
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
                session['otp_verified'] = False  # Reset OTP verified status
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
                session['otp_verified'] = True
                log.info("Results bracket my aya hau.")
                return jsonify({"status": True, "message": "Message here", "update_needed": True})
            else:
                return jsonify({"status": False, "error": result['message']})
        except Exception as e:
            log.error(f"Error in verify_otp: {e}")
            return jsonify({"status": False, "error": "An unexpected error occurred during verification."})

    @staticmethod
    def update_record(company_id):
        if session.get('otp_verified'):
            company_name = request.form.get('company_name')
            website = request.form.get('website')
            company_email_address = request.form.get('address')
            status = False

            connection = connect_to_db()
            if connection:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "UPDATE regx_company SET company_name=%s, website=%s, email_address=%s, status=%s WHERE id=%s",
                            (company_name, website, company_email_address, status, company_id))
                        connection.commit()
                        return jsonify({"status": True, "message": "Record updated successfully"})
                finally:
                    close_db_connection(connection)
                    # Clear the OTP verified status
                    session.pop('otp_verified')
                    session.pop('email')  # Clear the email from session
                    session.clear()  # Clear session variables after update
            return jsonify({'status': False, 'message': 'Failed to update record'})
        return jsonify({'status': False, 'message': 'OTP verification required'})
