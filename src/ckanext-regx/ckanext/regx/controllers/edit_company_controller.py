from flask import render_template, session, redirect, url_for, flash, request
from ckan.plugins import toolkit as tk
from ckanext.regx.lib.database import connect_to_db, close_db_connection
import logging

log = logging.getLogger(__name__)


class EditCompanyController:

    @staticmethod
    def get_company(company_id):
        """ Fetch a company's data by ID. """
        connection = connect_to_db()
        company = None
        if connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT id, company_name, website, address FROM regx_company WHERE id = %s", (company_id,))
                    company = cursor.fetchone()
            finally:
                close_db_connection(connection)
        return company

    @staticmethod
    def edit_company(company_id):
        if request.method == 'POST':
            company_name = request.form.get('company_name')
            website = request.form.get('website')
            address = request.form.get('address')
            status = False
            connection = connect_to_db()
            if connection:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "UPDATE regx_company SET company_name=%s, website=%s, address=%s, status=%s WHERE id=%s",
                            (company_name, website, address, status, company_id)
                        )
                        connection.commit()
                finally:
                    close_db_connection(connection)
            return redirect(url_for('regx.edit_company', company_id=company_id))
        else:
            company = EditCompanyController.get_company(company_id)
            if company:
                return render_template('edit_company1.html', company=company)
            else:
                return 'No company found', 404

    @staticmethod
    def edit_company_C():  # Calling this via Claim Form
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
