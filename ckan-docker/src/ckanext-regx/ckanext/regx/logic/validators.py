import ckan.plugins.toolkit as tk


def regx_required(value):
    if not value or value is tk.missing:
        raise tk.Invalid(tk._("Required"))
    return value


def get_validators():
    return {
        "regx_required": regx_required,
    }
