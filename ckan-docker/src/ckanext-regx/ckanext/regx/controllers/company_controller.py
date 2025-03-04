from flask import request, redirect, url_for, flash, get_flashed_messages, render_template, jsonify
from ckan.plugins import toolkit as tk
from ckan.common import c
from ckanext.regx.lib.database import connect_to_db, close_db_connection
from ckanext.regx.lib.otp_manager import OTPManager
import psycopg2

import logging

# Setting up logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class CompanyController:
    @staticmethod
    def company_form():
        log.debug("Rendering company form.")
        # Fetch flash messages
        # website=f"https://{domain}"
        user_email = c.userobj.email
        log.debug(f"user email {user_email}")
        flash_messages = get_flashed_messages(with_categories=True)
        return tk.render('company_form.html', extra_vars={'flash_messages': flash_messages})

    @staticmethod
    def submit_company():

        try:
            company_name = request.form.get('company_name')
            website = OTPManager.parsewebsite(request.form.get('website'))
            official_email = request.form.get('official_email')
            your_email = request.form.get('your_email')
            role = request.form.get('role')
            alternative_names = request.form.getlist('alt_names[]')
            street = request.form.get('street')
            postcode = request.form.get('postcode')
            city = request.form.get('city')
            vat = request.form.get('vat')
            tax_id = request.form.get('tax_id')
            profile_created_by = c.userobj.email
            public_id = OTPManager.generate_uuid()

            company_address = f"{street}, {postcode}, {city}"

            log.debug(f"Received data: {company_name}, {website}, {official_email}, {your_email}, {role}, {alternative_names}")  # noqa

            # Validate form data
            if not all([company_name, website, official_email, your_email, role, vat, tax_id]):
                flash("All fields are required.", "error")
                return redirect(url_for('regx.company_form'))

            check_website = website.split(
                '//')[-1].split('/')[0].replace('www.', '')
            official_email_domain = official_email.split('@')[-1]
            your_emaiil_domain = your_email.split('@')[-1]
            if check_website != official_email_domain:
                flash(
                    "Official Contact Email and website domain does not match", "error")
                return redirect(url_for('regx.company_form'))
            if check_website != your_emaiil_domain:
                flash("Your email and website domain does not match", "error")
                return redirect(url_for('regx.company_form'))

            connection = connect_to_db()
            if connection:
                try:
                    connection.autocommit = False
                    with connection.cursor() as cursor:
                        # Check if the company and website already exists with OR operator
                        cursor.execute(
                            "SELECT COUNT(*) FROM regx_company WHERE company_name=%s OR website=%s",
                            (company_name, website)
                        )
                        if cursor.fetchone()[0] > 0:
                            flash("Company already exists in our database.", "error")
                            return redirect(url_for('regx.company_form'))

                        cursor.execute(
                            """
                            INSERT INTO regx_company (id, company_name, website, email_address, vat_number, tax_id, company_address, profile_created_by, public_id, status, is_claimed)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                            """,
                            (public_id, company_name, website, official_email,
                             vat, tax_id, company_address, profile_created_by, public_id, False, True)
                        )
                        company_id = cursor.fetchone()[0]

                        # Inserting alternative names
                        for alt_name in alternative_names:
                            if alt_name:
                                cursor.execute(
                                    """
                                    INSERT INTO regx_alternative_names (alternative_name, company_id)
                                    VALUES (%s, %s)
                                    """,
                                    (alt_name, company_id)
                                )
                        cursor.execute(
                            """
                            INSERT INTO regx_claimants (claimant, claimant_role, status, c_id)
                            VALUES (%s, %s, %s, %s)
                            """,
                            (your_email, role, True, company_id)
                        )
                        connection.commit()
                        log.debug(f"uuid here{public_id}")
                        flash("Company created successfully!", "success")
                except psycopg2.Error as e:
                    connection.rollback()
                    log.error(f"PostgreSQL Error: {e.pgerror}")
                    flash("An error occurred while saving the company.", "error")
                finally:
                    close_db_connection(connection)
            else:
                flash("Failed to connect to the database.", "error")

        except Exception as e:
            log.error(f"Unexpected error: {e}")
            flash("An unexpected error occurred.", "error")

        return redirect(url_for('regx.company_form'))

    @staticmethod
    def get_profiles():
        company = None
        if request.method == 'GET':
            profile_created_by = c.userobj.email
            connection = connect_to_db()
            if connection:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "SELECT company_name, status, created, website, vat_number, id FROM regx_company WHERE profile_created_by = %s",
                            (profile_created_by,)
                        )
                        company = cursor.fetchall()
                        print(company)
                finally:
                    close_db_connection(connection)

        return render_template('get_profiles.html', company=company)

    @staticmethod
    def view_claimants(company_id):
        try:
            if "application/json" in request.headers.get("Accept", ""):
                connection = connect_to_db()
                if connection:
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute("""
                                SELECT
                                c.id          AS company_id,
                                cl.id         AS claimant_id,
                                c.company_name,
                                cl.claimant,
                                cl.claimant_role,
                                cl.status     AS claimant_status
                            FROM regx_company c
                            JOIN regx_claimants cl ON c.id = cl.c_id
                            WHERE c.id = %s;
                        """, (company_id,))
                            rows = cursor.fetchall()
                            companies = []
                            for row in rows:
                                companies.append({
                                    # each row will have the same company_id
                                    "company_id": row[0],
                                    # claimant_id, now used as the row’s unique ID
                                    "id": row[1],
                                    "company_name": row[2],
                                    "claimant": row[3],
                                    "claimant_role": row[4],
                                    "status": row[5],
                                })
                            return jsonify({"data": companies})
                    finally:
                        close_db_connection(connection)
                else:
                    return jsonify({"error": "Database connection failed."}), 500
            else:
                return tk.render("view_claimants.html")
        except Exception as e:
            log.error(f"Error fetching companies: {e}")
            return jsonify({"error": "Unexpected error occurred."}), 500

    @staticmethod
    def toggle_status_claimant():
        """
        Toggle the active/inactive status of a company profile.
        """
        try:
            claimant_id = request.form.get("claimant_id")
            new_status = request.form.get("new_status") == "true"

            log.debug(
                f"Preparing to send claim request email to {claimant_id}")

            if not claimant_id:
                return jsonify({"error": "Company ID is required."}), 400

            connection = connect_to_db()
            if connection:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "UPDATE regx_claimants SET status = %s WHERE id = %s",
                            (new_status, claimant_id),
                        )
                        connection.commit()
                        return jsonify({"message": "Status updated successfully."})
                finally:
                    close_db_connection(connection)
            else:
                return jsonify({"error": "Database connection failed."}), 500
        except Exception as e:
            log.error(f"Error toggling status: {e}")
            return jsonify({"error": "Unexpected error occurred."}), 500
