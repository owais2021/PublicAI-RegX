"""Tests for views.py."""

import pytest

import ckanext.regx.validators as validators


import ckan.plugins.toolkit as tk


@pytest.mark.ckan_config("ckan.plugins", "regx")
@pytest.mark.usefixtures("with_plugins")
def test_regx_blueprint(app, reset_db):
    resp = app.get(tk.h.url_for("regx.page"))
    assert resp.status_code == 200
    assert resp.body == "Hello, regx!"
