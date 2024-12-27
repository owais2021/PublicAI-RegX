
# import ckan.plugins as plugins
# import ckan.plugins.toolkit as toolkit


# import ckanext.regx.cli as cli
# import ckanext.regx.helpers as helpers
# import ckanext.regx.views as views
# from ckanext.regx.logic import (
#     action, auth, validators
# )


# class RegxPlugin(plugins.SingletonPlugin):
#     plugins.implements(plugins.IConfigurer)

# plugins.implements(plugins.IAuthFunctions)
# plugins.implements(plugins.IActions)
# plugins.implements(plugins.IBlueprint)
# plugins.implements(plugins.IClick)
# plugins.implements(plugins.ITemplateHelpers)
# plugins.implements(plugins.IValidators)

# IConfigurer

# def update_config(self, config_):
#     toolkit.add_template_directory(config_, "templates")
#     toolkit.add_public_directory(config_, "public")
#     toolkit.add_resource("assets", "regx")

# IAuthFunctions

# def get_auth_functions(self):
#     return auth.get_auth_functions()

# IActions

# def get_actions(self):
#     return action.get_actions()

# IBlueprint

# def get_blueprint(self):
#     return views.get_blueprints()

# IClick

# def get_commands(self):
#     return cli.get_commands()

# ITemplateHelpers

# def get_helpers(self):
#     return helpers.get_helpers()

# IValidators

# def get_validators(self):
#     return validators.get_validators()

# My
# -*- coding: utf-8 -*-

# Was working
# from ckan.plugins import toolkit as tk
# from ckan.plugins import SingletonPlugin, implements
# from ckan.plugins.interfaces import IBlueprint, IConfigurer
# from flask import Blueprint, render_template
# import os


# class RegxPlugin(SingletonPlugin):
#     implements(IBlueprint)
#     implements(IConfigurer)

#     def get_blueprint(self):
#         # Register Blueprint for Flask
#         blueprint = Blueprint(
#             "regx",
#             __name__,
#             template_folder=os.path.join(
#                 os.path.dirname(__file__), "templates"),
#             url_prefix="/regx"
#         )

#         @blueprint.route("/")
#         def index():
#             return render_template("index.html")

#         return blueprint

#     def update_config(self, config):
#         # Register the templates directory with CKAN
#         tk.add_template_directory(config, "templates")
#         print(os.path.join(os.path.dirname(__file__), "templates"))

# sherry

# from ckan.plugins import toolkit as tk
# from ckan.plugins import SingletonPlugin, implements
# from ckan.plugins.interfaces import IBlueprint, IConfigurer
# from flask import Blueprint, render_template, request, redirect, flash
# import os


# class RegxPlugin(SingletonPlugin):
#     implements(IBlueprint)
#     implements(IConfigurer)

#     def get_blueprint(self):
#         # Register Blueprint for Flask
#         blueprint = Blueprint(
#             "regx",
#             __name__,
#             template_folder=os.path.join(
#                 os.path.dirname(__file__), "templates"),
#             static_folder=os.path.join(os.path.dirname(__file__), "public"),
#             url_prefix="/regx"
#         )

#         @blueprint.route("/")
#         def index():
#             # Render the default page (index.html)
#             return render_template("index.html")

#         @blueprint.route("/company_form", methods=["GET"])
#         def company_form():
#             # Render the company form page
#             return render_template("company_form.html")

#         @blueprint.route("/submit_form", methods=["POST"])
#         def submit_form():
#             # Handle form submission
#             company_name = request.form.get("company_name")
#             website = request.form.get("website")
#             address = request.form.get("address")

#             # Basic validation
#             if not company_name or not website or not address:
#                 flash("All fields are required!", "error")
#                 return redirect(tk.url_for("regx.company_form"))

#             flash("Company details submitted successfully!", "success")
#             return redirect(tk.url_for("regx.company_form"))

#         return blueprint

#     def update_config(self, config):
#         # Register the templates and public directories with CKAN
#         tk.add_template_directory(config, "templates")
#         tk.add_public_directory(config, "public")
#         print("Templates directory:", os.path.join(
#             os.path.dirname(__file__), "templates"))


# again

# from ckan.plugins import toolkit as tk
# from ckan.plugins import SingletonPlugin, implements
# from ckan.plugins.interfaces import IBlueprint, IConfigurer
# from flask import Blueprint, render_template
# import os

# from ckan.plugins import toolkit as tk
# from ckan.plugins import SingletonPlugin, implements
# from ckan.plugins.interfaces import IBlueprint, IConfigurer
# from flask import Blueprint, render_template, request
# import os


# class RegxPlugin(SingletonPlugin):
#     implements(IBlueprint)
#     implements(IConfigurer)

#     def get_blueprint(self):
#         blueprint = Blueprint(
#             "regx",
#             __name__,
#             template_folder=os.path.join(
#                 os.path.dirname(__file__), "templates"),
#             url_prefix="/regx"
#         )

#         @blueprint.route("/")
#         def index():
#             return render_template("index.html")

#         @blueprint.route("/company_form")
#         def company_form():
#             return render_template("company_form.html")

#         @blueprint.route("/submit_form", methods=["POST"])
#         def submit_form():
#             # Access form data
#             # company_name = request.form.get("company_name")
#             # website = request.form.get("website")
#             # address = request.form.get("address")

#             # Process the data (e.g., validation, saving to database)
#             # print(f"Company Name: {company_name}, Website: {
#             #       website}, Address: {address}")

#             # Return a success message or redirect
#             return f"Form submitted successfully! Company Name: , Website: , Address:"

#         return blueprint

#     def update_config(self, config):
#         tk.add_template_directory(config, "templates")
#         tk.add_public_directory(config, "public")

# new
# from ckan.plugins import toolkit as tk
# from ckan.plugins import SingletonPlugin, implements
# from ckan.plugins.interfaces import IBlueprint, IConfigurer
# from flask import Blueprint, render_template, abort
# import os


# class RegxPlugin(SingletonPlugin):
#     # Implement CKAN plugin interfaces
#     implements(IBlueprint)
#     implements(IConfigurer)

#     def get_blueprint(self):
#         # Create a Flask Blueprint for the extension
#         blueprint = Blueprint(
#             "regx",
#             __name__,
#             template_folder=os.path.join(
#                 os.path.dirname(__file__), "templates"),
#             url_prefix="/regx"
#         )

#         # Route for the default index page
#         @blueprint.route("/")
#         def index():
#             return render_template("index.html")

#         # Route for the company form page
#         @blueprint.route("/company_form")
#         def company_form():
#             return render_template("company_form.html")

#         @blueprint.route("/submit_form")
#         def submit_form():
#             return render_template("company_form.html")

#         # Route for the admin-only "All Profiles" page
#         @blueprint.route("/admin_all_profiles")
#         def admin_all_profiles():
#             # Check if the user is logged in and is an admin
#             if not tk.c.userobj or not tk.c.userobj.sysadmin:
#                 # Return a 403 Forbidden error if the user is not an admin
#                 abort(403)
#             return render_template("admin_all_profiles.html")

#         @blueprint.route("/admin_all_user_profiles")
#         def admin_all_user_profiles():
#             # Check if the user is logged in and is an admin
#             if not tk.c.userobj or not tk.c.userobj.sysadmin:
#                 # Return a 403 Forbidden error if the user is not an admin
#                 abort(403)
#             return render_template("admin_all_user_profiles.html")

#         return blueprint

#     def update_config(self, config):
#         # Register the templates and public directories with CKAN
#         tk.add_template_directory(config, "templates")
#         tk.add_public_directory(config, "public")

# DB
from ckan.plugins import toolkit as tk
from ckan.plugins.core import SingletonPlugin, implements
from ckan.plugins.interfaces import IBlueprint, IConfigurer
from flask import Blueprint, render_template, request, redirect, url_for, abort
from ckan.model import Session
from .model import CompanyProfile
import os


class RegxPlugin(SingletonPlugin):
    implements(IBlueprint)
    implements(IConfigurer)

    def get_blueprint(self):
        blueprint = Blueprint(
            'regx',
            __name__,
            template_folder=os.path.join(
                os.path.dirname(__file__), 'templates'),
            static_folder=os.path.join(os.path.dirname(__file__), 'public'),
            url_prefix='/regx'
        )

        @blueprint.route('/')
        def index():
            # Basic index page
            return render_template('index.html')

        @blueprint.route('/company_form', methods=['GET'])
        def company_form():
            # 1. Grab the CSRF token from the CKAN cookie
            token_from_cookie = tk.request.cookies.get('_csrf_token', '')

            # 2. Pass it to the template as 'csrf_value'
            return render_template(
                'company_form.html',
                csrf_value=token_from_cookie
            )

        @blueprint.route('/submit_form', methods=['POST'])
        def submit_form():
            # Retrieve form data
            company_name = request.form['company_name']
            website = request.form['website']
            address = request.form['address']

            # Create and save the new CompanyProfile
            profile = CompanyProfile(
                company_name=company_name,
                website=website,
                address=address
            )
            Session.add(profile)
            Session.commit()

            # Redirect to a confirmation page or back to the form
            return redirect(url_for('.index'))

        @blueprint.route('/admin_all_profiles')
        def admin_all_profiles():
            # Ensure user is logged in and is an admin
            if not tk.c.userobj or not tk.c.userobj.sysadmin:
                abort(403)
            return render_template('admin_all_profiles.html')

        return blueprint

    def update_config(self, config):
        tk.add_template_directory(config, 'templates')
        tk.add_public_directory(config, 'public')
