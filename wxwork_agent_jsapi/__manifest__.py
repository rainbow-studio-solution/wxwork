# -*- coding: utf-8 -*-
{
    "name": "Enterprise WeChat Application JSAPI",
    "author": "RStudio",
    "website": "",
    "sequence": 1,
    "installable": True,
    "application": False,
    "auto_install": False,
    "category": "wxwork",
    "version": "13.0.0.1",
    "summary": """
        
        """,
    "description": """


        """,
    "depends": [
        "wxwork_base",
        "wxwork_auth_oauth",
    ],
    "external_dependencies": {
        "python": [],
    },
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "qweb": [
        "static/src/xml/*.xml",
    ],
}