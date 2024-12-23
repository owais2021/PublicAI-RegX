import ckan.plugins.toolkit as tk
import ckanext.regx.logic.schema as schema


@tk.side_effect_free
def regx_get_sum(context, data_dict):
    tk.check_access(
        "regx_get_sum", context, data_dict)
    data, errors = tk.navl_validate(
        data_dict, schema.regx_get_sum(), context)

    if errors:
        raise tk.ValidationError(errors)

    return {
        "left": data["left"],
        "right": data["right"],
        "sum": data["left"] + data["right"]
    }


def get_actions():
    return {
        'regx_get_sum': regx_get_sum,
    }
