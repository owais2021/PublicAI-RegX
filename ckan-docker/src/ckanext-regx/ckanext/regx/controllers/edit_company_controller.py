from flask import render_template, session, redirect, url_for, flash, request, jsonify
from ckan.plugins import toolkit as tk
from ckanext.regx.lib.database import connect_to_db, close_db_connection
from ckanext.regx.lib.otp_manager import OTPManager
import logging

log = logging.getLogger(__name__)


class EditCompanyController:

    @staticmethod
    def get_company(company_id):

        # connection = connect_to_db()
        # company = None
        # if connection:
        #     try:
        #         with connection.cursor() as cursor:
        #             cursor.execute(
        #                 "SELECT id, company_name, website, email_address, claimant, claimant_role FROM regx_company WHERE id = %s", (company_id,))
        #             company = cursor.fetchone()
        #     finally:
        #         close_db_connection(connection)
        # return company

        connection = connect_to_db()
        company = None
        if connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                    SELECT c.id, c.company_name, c.website, c.email_address, c.vat_number, c.tax_id, c.company_address,
                        array_agg(a.alternative_name) FILTER (WHERE a.alternative_name IS NOT NULL) AS alternative_names
                    FROM regx_company c
                    LEFT JOIN regx_alternative_names a ON c.id = a.company_id
                    WHERE c.id = %s
                    GROUP BY c.id
                    ORDER BY c.created DESC
                    """, (company_id,))

                    company = cursor.fetchone()
            finally:
                close_db_connection(connection)
        return company

    @staticmethod
    def edit_company(company_id):
        if request.method == 'POST':
            log.info(f"'otp_verified' in session: {session.get('otp_verified')}")  # noqa
            if 'email' in request.form:
                if session.get('otp_verified', False):
                    return EditCompanyController.update_record(company_id)
                return EditCompanyController.send_otp(company_id)
            if 'otp' in request.form:  # Assuming verifying OTP
                return EditCompanyController.verify_otp(company_id)
        else:
            company = EditCompanyController.get_company(company_id)
            if company:
                return render_template('edit_company1.html', company=company, company_id=company_id)
            else:
                flash('No company found')
                return redirect(url_for('regx.edit_company', company_id=company_id))

    @staticmethod
    def send_otp(company_id):
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

            connection = connect_to_db()
            if connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT claimant from regx_claimants  WHERE  c_id=%s AND claimant=%s AND status=true",
                        (company_id, email))
                    result = cursor.fetchone()
                    if not result:
                        return jsonify({"status": False, "message": "No Claimant Found with this email"})

                    otp_sent = OTPManager.generate_and_send_otp(email)
                    if otp_sent:
                        # Reset OTP verified status
                        session['otp_verified'] = False
                        session['email'] = email
                        return jsonify({"status": True, "message": "OTP sent successfully. Check your email."})
                    else:
                        return jsonify({"status": False, "message": "Failed to send OTP. Please try again later."})

        except Exception as e:
            log.error(f"Error in edit_profile_Controller: {e}")
            return jsonify({"status": False, "message": "An unexpected error occurred. Please try again."})

    @staticmethod
    def verify_otp():
        """
        Handle OTP verification and redirect to edit_company page on success.
        """
        try:
            entered_otp = request.form.get('otp', '').strip()
            result = None

            if not entered_otp:
                return jsonify({"status": False, "error": "OTP is required."})

            result = OTPManager.verify_otp(entered_otp)
            log.info(f"verify_otp result is: {result}")
            if result['status']:
                # session['otp_verified'] = True
                log.info(f"'otp_verified' in session: {session.get('otp_verified')}")  # noqa
                log.info("Results bracket my aya hau.")
                return jsonify({"status": True, "message": "OTP Verified Successfully"})
            else:
                log.info("Results bracket my nni aya hau.")
                return jsonify({"status": False, "error": result['message']})
        except Exception as e:
            log.error(f"Error in verify_otp: {e}")
            return jsonify({"status": False, "error": "An unexpected error occurred during verification."})

    @staticmethod
    def update_record(company_id):
        if session.get('otp_verified'):
            company_address = request.form.get('company_address')
            vat = request.form.get('vat')
            tax_id = request.form.get('tax_id')
            alternative_names = request.form.getlist('alt_names[]')
            status = False

            connection = connect_to_db()
            if connection:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "UPDATE regx_company SET company_address=%s, status=%s, vat_number=%s, tax_id=%s WHERE id=%s",
                            (company_address, status, vat, tax_id, company_id))

                        # Insert alternative names
                        for alt_name in alternative_names:
                            if alt_name:
                                cursor.execute(
                                    """
                                    INSERT INTO regx_alternative_names (alternative_name, company_id)
                                    VALUES (%s, %s)
                                    """,
                                    (alt_name, company_id)
                                )
                        connection.commit()

                        return jsonify({"status": True, "message": "Record updated successfully", "redirect_url": url_for('regx.search_company')})
                finally:
                    close_db_connection(connection)
                    # Clear the OTP verified status
                    session.pop('otp_verified')
                    session.pop('email')
                    # c_id b pop krni
            return jsonify({'status': False, 'message': 'Failed to update record'})
        return jsonify({'status': False, 'message': 'OTP verification required'})
