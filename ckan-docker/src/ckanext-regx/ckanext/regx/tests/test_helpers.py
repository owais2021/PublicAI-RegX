"""Tests for helpers.py."""

import ckanext.regx.helpers as helpers


def test_regx_hello():
    assert helpers.regx_hello() == "Hello, regx!"
