from flask import request, redirect, url_for, flash, jsonify, session, get_flashed_messages, render_template
from ckan.plugins import toolkit as tk
from ckanext.regx.lib.otp_manager import OTPManager
from ckanext.regx.lib.database import connect_to_db, close_db_connection
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')
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

    # @staticmethod
    # def submit_claim_profile():
    #     """
    #     Handle form submission for OTP generation.
    #     """
    #     try:
    #         website = request.form.get('website', '').strip().lower()
    #         email = request.form.get('email', '').strip().lower()

    #         if not website or not email:
    #             return jsonify({"status": False, "message": "Website and email are required."})

    #         website_domain = website.split(
    #             '//')[-1].split('/')[0].replace('www.', '')
    #         email_domain = email.split('@')[-1]

    #         if website_domain != email_domain:
    #             return jsonify({"status": False, "message": "Website and email domains do not match."})

    #         otp_sent = OTPManager.generate_and_send_otp(email)
    #         if otp_sent:
    #             session['email'] = email
    #             return jsonify({"status": True, "message": "OTP sent successfully. Check your email."})
    #         else:
    #             return jsonify({"status": False, "message": "Failed to send OTP. Please try again later."})
    #     except Exception as e:
    #         log.error(f"Error in submit_claim_profile: {e}")
    #         return jsonify({"status": False, "message": "An unexpected error occurred. Please try again."})

    @staticmethod
    def submit_claim_profile():
        """
        Handle form submission for OTP generation with pre-validation against the database.
        """
        try:
            website = request.form.get('website', '').strip().lower()
            email = request.form.get('email', '').strip().lower()

            if not website or not email:
                log.warning(
                    "Website and email fields are required but were not provided.")
                return jsonify({"status": False, "message": "Website and email are required."})

            # Connect to the database to check if the website already exists
            conn = connect_to_db()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, company_name, website, email_address, status FROM regx_company WHERE website = %s", (website,))
            company = cursor.fetchone()

            if not company:
                log.info(f"Website {website} not found in database.")
                return jsonify({"status": False, "message": "Website not registered."})

            # Check if the status is false
            if not company[4]:
                log.info(f"Website {website} is inactive. Cannot proceed.")
                return jsonify({"status": False, "message": "The company record is inactive and cannot be processed."})

            # Store the company ID in the session
            session['company_id'] = company[0]
            log.debug(f"Website {website} found with details: {company}.")
            close_db_connection(conn)

            # Continue with domain validation if the website is found
            website_domain = website.split(
                '//')[-1].split('/')[0].replace('www.', '')
            email_domain = email.split('@')[-1]

            if website_domain != email_domain:
                log.warning(f"Website domain {website_domain} does not match email domain {email_domain}.")  # noqa
                return jsonify({"status": False, "message": "Website and email domains do not match."})

            # Generate and send OTP
            otp_sent = OTPManager.generate_and_send_otp(email)
            if otp_sent:
                # Store email in session for later verification
                session['email'] = email
                log.info(f"OTP sent successfully to {email}.")
                return jsonify({"status": True, "message": "OTP sent successfully. Check your email."})
            else:
                log.error("Failed to send OTP.")
                return jsonify({"status": False, "message": "Failed to send OTP. Please try again later."})
        except Exception as e:
            log.error(f"Error in submit_claim_profile: {e}", exc_info=True)
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
                company_id = session.get('company_id')
                if not company_id:
                    return jsonify({"status": False, "error": "Session expired or invalid."})
                session.pop('otp', None)
                session.pop('otp_expiry', None)
                session['otp_verified'] = True
                log.info("Results bracket my aya hau.")
                log.info(company_id)
                return jsonify({"status": True, "message": "OTP Verified Successfully", "redirect_url": url_for('regx.update_claim_form', company_id=company_id)})
            else:
                return jsonify({"status": False, "error": result['message']})
        except Exception as e:
            log.error(f"Error in verify_otp: {e}")
            return jsonify({"status": False, "error": "An unexpected error occurred during verification."})

    @staticmethod
    def fetch_record(company_id):
        """Fetches company details from the database."""
        conn = connect_to_db()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT id, company_name, website, email_address FROM regx_company WHERE id = %s", (company_id,))
            company = cursor.fetchone()
            if not company:
                flash('Company not found.')
                # Redirect or handle as needed
                return jsonify({"status": False, "error": "No Record Found"})
            log.info(company)
            return render_template('update_claim_form.html', company_obj=company)
        finally:
            close_db_connection(conn)

    @staticmethod
    def update_record(company_id):

        conn = None
        cursor = None
        try:
            if request.method == 'POST':
                company_name = request.form['company_name']
                website = request.form['website']
                email_address = request.form['email_address']
                # Continue with domain validation if the website is found
                website_domain = website.split(
                    '//')[-1].split('/')[0].replace('www.', '')
                email_domain = email_address.split('@')[-1]

                if website_domain != email_domain:
                    log.warning(f"Website domain {website_domain} does not match email domain {email_domain}.")  # noqa
                    return jsonify({"status": False, "message": "Website and email domains do not match."})

                conn = connect_to_db()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE regx_company
                    SET company_name = %s, email_address = %s, status = False
                    WHERE id = %s
                """, (company_name, email_address, company_id))

                # Commit changes and handle exceptions
                conn.commit()
                session.pop('otp_verified', None)
                session.pop('company_id', None)
                session.modified = True
                return jsonify({"status": True, "message": "Update Request Submitted Successfully", "redirect_url": url_for('regx.search_company')})

        except Exception as e:
            if conn:
                conn.rollback()
            flash('Failed to update company details.')
            print(e)  # Log the error for debugging
            return redirect(url_for('regx.update_claim_form', company_id=company_id))

        finally:
            if cursor:
                cursor.close()
            if conn:
                close_db_connection(conn)
