from flask import request, render_template, jsonify
from ckanext.regx.lib.database import connect_to_db, close_db_connection
import logging

log = logging.getLogger(__name__)


class CompanySearchController:
    @staticmethod
    def search_company():
        company = None  # Initialize company as None
        form_submitted = False  # Track if the form was submitted

        if request.method == 'POST':
            form_submitted = True  # Set form_submitted to True when POST is handled
            profile_id = request.form.get('profile_id')
            connection = connect_to_db()
            if connection:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "SELECT company_name, email_address, website, created, id FROM regx_company WHERE company_name ILIKE %s AND status=TRUE",
                            (f"%{profile_id}%",)
                        )
                        company = cursor.fetchall()
                        print(company)
                finally:
                    close_db_connection(connection)

        return render_template('search_company.html', company=company, form_submitted=form_submitted)

    def update_company():
        company_id = request.form['company_id']
        company_name = request.form['company_name']
        website = request.form['website']
        address = request.form['address']
        # Default to 'true' if not specified
        status = request.form.get('status', 'true')

        connection = connect_to_db()
        if connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE regx_company SET company_name=%s, website=%s,email_ address=%s, status=%s WHERE id=%s",
                        (company_name, website, address, status, company_id)
                    )
                    connection.commit()
                    return jsonify({'message': 'Record updated successfully'})
            finally:
                close_db_connection(connection)
        else:
            log.error("Failed to connect to the database.")
            return jsonify({'error': 'Database connection failed'}), 500
