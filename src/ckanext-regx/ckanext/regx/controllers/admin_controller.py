import logging
import json
from flask import jsonify, Response, request
from ckan.plugins import toolkit as tk
from ckanext.regx.lib.database import connect_to_db, close_db_connection

log = logging.getLogger(__name__)


class AdminController:
    @staticmethod
    def admin_all_profiles():
        try:
            if "application/json" in request.headers.get("Accept", ""):
                connection = connect_to_db()
                if connection:
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute("""
                                SELECT c.id, c.company_name, c.email_address, c.website, c.status, c.created,
                                       array_agg(a.alternative_name) FILTER (WHERE a.alternative_name IS NOT NULL) AS alternative_names
                                FROM regx_company c
                                LEFT JOIN regx_alternative_names a ON c.id = a.company_id
                                GROUP BY c.id
                                ORDER BY c.created DESC
                            """)
                            rows = cursor.fetchall()
                            companies = [
                                {
                                    "id": row[0],
                                    "company_name": row[1],
                                    "email_address": row[2],
                                    "website": row[3],
                                    "status": row[4],
                                    "created": row[5].strftime('%Y-%m-%d') if row[5] else None,
                                    "alternative_names": row[6] if row[6] else []
                                }
                                for row in rows
                            ]
                            return jsonify({"data": companies})
                    finally:
                        close_db_connection(connection)
                else:
                    return jsonify({"error": "Database connection failed."}), 500
            else:
                return tk.render("admin_all_profiles.html")
        except Exception as e:
            log.error(f"Error fetching companies: {e}")
            return jsonify({"error": "Unexpected error occurred."}), 500

    @staticmethod
    def toggle_status():
        """
        Toggle the active/inactive status of a company profile.
        """
        try:
            company_id = request.form.get("company_id")
            new_status = request.form.get("new_status") == "true"

            if not company_id:
                return jsonify({"error": "Company ID is required."}), 400

            connection = connect_to_db()
            if connection:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "UPDATE regx_company SET status = %s WHERE id = %s",
                            (new_status, company_id),
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

    @staticmethod
    def download_dataset(company_id):
        """
        Download dataset for a specific company as JSON.
        """
        try:
            connection = connect_to_db()
            if connection:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "SELECT id, company_name, email_address, website, status FROM regx_company WHERE id = %s",
                            (company_id,),
                        )
                        row = cursor.fetchone()
                        if row:
                            company_data = {
                                "id": row[0],
                                "company_name": row[1],
                                "address": row[2],
                                "website": row[3],
                                "status": row[4],
                            }
                            response = Response(
                                json.dumps(company_data, indent=4),
                                content_type="application/json",
                            )
                            response.headers["Content-Disposition"] = (f"attachment; filename=company_{company_id}.json")  # noqa
                            return response
                        else:
                            return jsonify({"error": "Company not found."}), 404
                finally:
                    close_db_connection(connection)
            else:
                return jsonify({"error": "Database connection failed."}), 500
        except Exception as e:
            log.error(f"Error downloading dataset: {e}")
            return jsonify({"error": "Unexpected error occurred."}), 500
