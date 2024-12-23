# # -*- coding: utf-8 -*-
# from setuptools import setup

# # Note: Do not add new arguments to setup(), instead add setuptools
# # configuration options to setup.cfg, or any other project information
# # to pyproject.toml
# # See https://github.com/ckan/ckan/issues/8382 for details

# setup(
#     # If you are changing from the default layout of your extension, you may
#     # have to change the message extractors, you can read more about babel
#     # message extraction at
#     # http://babel.pocoo.org/docs/messages/#extraction-method-mapping-and-configuration
#     message_extractors={
#         'ckanext': [
#             ('**.py', 'python', None),
#             ('**.js', 'javascript', None),
#             ('**/templates/**.html', 'ckan', None),
#         ],
#     }
# )


# -*- coding: utf-8 -*-
# from setuptools import setup


# setup(
#     name='ckanext-regx',
#     version='0.0.1',
#     description='A CKAN extension for demonstration purposes',
#     packages=['ckanext.regx'],
#     entry_points='''
#         [ckan.plugins]
#         regx=ckanext.regx.plugin:RegxPlugin
#     ''',
#     message_extractors={
#         'ckanext': [
#             ('**.py', 'python', None),
#             ('**.js', 'javascript', None),
#             ('**/templates/**.html', 'ckan', None),
#         ],
#     },
# )


# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(
    name='ckanext-regx',
    version='0.0.1',
    description='A CKAN extension for demonstration purposes',
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'ckan.plugins': [
            'regx = ckanext.regx.plugin:RegxPlugin',
        ],
        'babel.extractors': [
            'ckan = ckan.lib.extract:extract_ckan',
        ],
    },
    zip_safe=False,
)
