from flask import request, redirect, url_for, flash, jsonify, session, get_flashed_messages, render_template
from ckan.plugins import toolkit as tk
from ckan.common import c
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

    @staticmethod
    def submit_claim_profile():
        try:
            website = request.form.get('website')
            claimant_email = request.form.get('email', '').strip().lower()
            role = request.form.get('role')

            if not website or not claimant_email:
                log.warning(
                    "Website and email fields are required but were not provided.")
                return jsonify({"status": False, "message": "Website and email are required."})

            # Connect to the database
            conn = connect_to_db()
            cursor = conn.cursor()

            # Fetch company details based on the website
            cursor.execute(
                "SELECT id, website, status, company_name FROM regx_company WHERE website = %s", (website,))
            company = cursor.fetchone()

            if not company:
                log.info(f"Website {website} not found in database.")
                return jsonify({"status": False, "message": "Website not registered."})

            # Check if the company status is inactive
            if not company[2]:
                log.info(f"Company {website} is inactive. Cannot proceed.")
                return jsonify({"status": False, "message": "This company record is inactive and cannot be processed."})

            # Fetch the company ID
            company_id = company[0]

            # Check if the claimant email already exists for this company in the claimants table
            cursor.execute(
                "SELECT claimant FROM regx_claimants WHERE c_id = %s AND claimant = %s", (company_id, claimant_email))
            existing_claimant = cursor.fetchone()

            if existing_claimant:
                log.info(
                    f"Claimant email {claimant_email} already exists for company ID {company_id}.")
                return jsonify({"status": False, "message": "This email already exists as a claimant for this company."})

            # Store company ID in session for later use
            session['company_id'] = company_id
            log.debug(f"Website {website} found with details: {company}.")
            log.debug(f"Role: {role}")

            # Continue with domain validation
            website_url = company[1]
            website_domain = website_url.split(
                '//')[-1].split('/')[0].replace('www.', '')
            email_domain = claimant_email.split('@')[-1]

            if website_domain != email_domain:
                log.warning(
                    f"Website domain {website_domain} does not match email domain {email_domain}.")
                return jsonify({"status": False, "message": "Website and email domains do not match."})

            # Generate and send OTP
            otp_sent = OTPManager.generate_and_send_otp(claimant_email)
            if otp_sent["status"]:
                # Store email and role in session for later verification
                session['c_email'] = claimant_email
                session['role'] = role
                session['company_name'] = company[3]
                log.info(f"OTP sent successfully to {claimant_email}.")
                return jsonify({"status": True, "message": "OTP sent successfully. Check your email."})
            else:
                log.error("Failed to send OTP.")
                return jsonify({"status": False, "message": otp_sent['message']})

        except Exception as e:
            log.error(f"Error in submit_claim_profile: {e}", exc_info=True)
            return jsonify({"status": False, "message": "An unexpected error occurred. Please try again."})

        finally:
            if cursor:
                cursor.close()
            if conn:
                close_db_connection(conn)

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

# updateclaim form py call ho ra hai aur yahan abhi VAt wali fields dalni hain
    @staticmethod
    def fetch_record(company_id):
        conn = connect_to_db()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT id, company_name, website, email_address, company_address FROM regx_company WHERE id = %s", (company_id,))
            company = cursor.fetchone()
            if not company:
                flash('Company not found.')
                return jsonify({"status": False, "error": "No Record Found"})
            log.info(company)
            return render_template('update_claim_form.html', company_obj=company)
        finally:
            close_db_connection(conn)

    @staticmethod
    def update_record(company_id):
        if request.method != 'POST':
            return jsonify({"status": False, "message": "Invalid request method."})

        profile_created_by = c.userobj.email  # Logged-in user's email

        try:
            claimant_email = session.get('c_email')
            claimant_role = session.get('role')
            company_name = session.get('company_name')

            with connect_to_db() as conn, conn.cursor() as cursor:
                # Check if the company already has a profile_created_by value
                cursor.execute("""
                    SELECT profile_created_by
                    FROM regx_company
                    WHERE id = %s
                    LIMIT 1
                """, (company_id,))
                result = cursor.fetchone()

                if not result or not result[0]:
                    # If no profile_created_by, insert the first claimant and update the company
                    cursor.execute("""
                        INSERT INTO regx_claimants (claimant, claimant_role, status, c_id)
                        VALUES (%s, %s, %s, %s)
                    """, (claimant_email, claimant_role, True, company_id))
                    cursor.execute("""
                        UPDATE regx_company
                        SET is_claimed = %s, profile_created_by = %s
                        WHERE id = %s
                    """, (True, profile_created_by, company_id))
                else:
                    # If profile_created_by exists, only insert the claimant
                    cursor.execute("""
                        INSERT INTO regx_claimants (claimant, claimant_role, status, c_id)
                        VALUES (%s, %s, %s, %s)
                    """, (claimant_email, claimant_role, True, company_id))
                    cursor.execute("""
                        UPDATE regx_company
                        SET is_claimed = %s
                        WHERE id = %s
                    """, (True, company_id))

                conn.commit()

                # Clear session data
                session.pop('otp_verified', None)
                session.pop('company_id', None)
                session.pop('email', None)
                session.pop('role', None)
                session.pop('company_name', None)

                # Send claim request email
                OTPManager.send_claim_request_email(
                    claimant_email, company_name)

                return jsonify({
                    "status": True,
                    "message": "Claim request submitted successfully.",
                    "redirect_url": url_for('regx.search_company')
                })

        except Exception as e:
            log.error(f"Failed to update company details: {e}")
            if conn:
                conn.rollback()
            return jsonify({"status": False, "message": "Failed to update company details."})
