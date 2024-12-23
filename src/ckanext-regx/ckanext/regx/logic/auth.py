import ckan.plugins.toolkit as tk


@tk.auth_allow_anonymous_access
def regx_get_sum(context, data_dict):
    return {"success": True}


def get_auth_functions():
    return {
        "regx_get_sum": regx_get_sum,
    }
