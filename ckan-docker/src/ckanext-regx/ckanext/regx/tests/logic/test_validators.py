"""Tests for validators.py."""

import pytest

import ckan.plugins.toolkit as tk

from ckanext.regx.logic import validators


def test_regx_reauired_with_valid_value():
    assert validators.regx_required("value") == "value"


def test_regx_reauired_with_invalid_value():
    with pytest.raises(tk.Invalid):
        validators.regx_required(None)
