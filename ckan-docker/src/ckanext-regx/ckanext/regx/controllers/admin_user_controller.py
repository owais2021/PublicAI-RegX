import logging
import json
from flask import jsonify, Response, request
from ckan.plugins import toolkit as tk
from ckanext.regx.lib.database import connect_to_db, close_db_connection

log = logging.getLogger(__name__)


class AdminUserController:
    @staticmethod
    def admin_all_user_profiles():
        """
        Fetch all user profiles or render the user profiles page.
        """
        try:
            if "application/json" in request.headers.get("Accept", ""):
                # Fetch user data for DataTables
                connection = connect_to_db()
                if connection:
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute(
                                """
                                SELECT id, name, email, sysadmin, state
                                FROM "user"
                                """
                            )
                            rows = cursor.fetchall()
                            users = [
                                {
                                    "id": row[0],
                                    "name": row[1],
                                    "email": row[2],
                                    "role": "Admin" if row[3] else "User",
                                    "status": "Active" if row[4] == "active" else "Inactive",
                                }
                                for row in rows
                            ]
                            return jsonify({"data": users})
                    finally:
                        close_db_connection(connection)
                else:
                    return jsonify({"error": "Database connection failed."}), 500
            else:
                # Render HTML page for user profiles
                return tk.render("admin_all_user_profiles.html")
        except Exception as e:
            log.error(f"Error fetching user profiles: {e}")
            return jsonify({"error": "Unexpected error occurred."}), 500
