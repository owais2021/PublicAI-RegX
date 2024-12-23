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
# import ckan.plugins as plugins
# from flask import Blueprint


# class RegxPlugin(plugins.SingletonPlugin):
#     plugins.implements(plugins.IBlueprint)

#     def get_blueprint(self):
#         blueprint = Blueprint('regx', __name__, url_prefix='/regx')

#         @blueprint.route('/')
#         def index():
#             return 'Hello from regx!'

#         return blueprint

# ckanext/regx/plugin.py

from ckan.plugins import toolkit as tk
from ckan.plugins import SingletonPlugin, implements
from ckan.plugins.interfaces import IBlueprint, IConfigurer
from flask import Blueprint, render_template
import os


class RegxPlugin(SingletonPlugin):
    implements(IBlueprint)
    implements(IConfigurer)

    def get_blueprint(self):
        # Register Blueprint for Flask
        blueprint = Blueprint(
            "regx",
            __name__,
            template_folder=os.path.join(
                os.path.dirname(__file__), "templates"),
            url_prefix="/regx"
        )

        @blueprint.route("/")
        def index():
            return render_template("index.html")

        return blueprint

    def update_config(self, config):
        # Register the templates directory with CKAN
        tk.add_template_directory(config, "templates")
        print(os.path.join(os.path.dirname(__file__), "templates"))
