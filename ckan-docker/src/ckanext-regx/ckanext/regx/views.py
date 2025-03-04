from flask import Blueprint, jsonify

# Create a Flask Blueprint
regx_blueprint = Blueprint('regx', __name__)


@regx_blueprint.route('/regx/hello')
def hello():
    return jsonify({"message": "Hello, CKAN from regx!"})
