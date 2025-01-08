from flask import request, jsonify
from ckanext.regx.lib.database import connect_to_db, close_db_connection
from ckan.plugins import toolkit as tk
import logging

log = logging.getLogger(__name__)


class SearchProfilesController:
    @staticmethod
    def search_profiles():
        """
        Render the search page for company profiles.
        """
        return tk.render('search_profiles.html')

    @staticmethod
    def fetch_profiles():
        """
        Fetch company profiles based on a search query sent via AJAX POST request.
        """
        search_query = request.form.get('search_query', '')
        connection = connect_to_db()
        if connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT id, company_name, address, website, status, created FROM regx_company WHERE company_name ILIKE %s",
                        ('%' + search_query + '%',)
                    )
                    rows = cursor.fetchall()
                    companies = [
                        {
                            "id": row[0],
                            "company_name": row[1],
                            "address": row[2],
                            "website": row[3],
                            "status": row[4],
                            "created": row[5].strftime('%Y-%m-%d') if row[5] else None
                        }
                        for row in rows
                    ]
                    return jsonify({"data": companies})
            finally:
                close_db_connection(connection)
        else:
            log.error("Failed to connect to the database to fetch profiles.")
            return jsonify({"error": "Database connection failed."}), 500
