# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP Autobuild
#    Copyright (C) 2012-2013 Bluestar Solutions Sàrl (<http://www.blues2.ch>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################

URL = "url"
BZR_REV = "bzr-rev"
OPENERP = "openerp"
SERIE = "serie"
WORKSPACE = "workspace"
CONF_FILES = "custom-configuration-files"
DEFAULT_SERIE = "default-serie"
DATABASE = "database"
HOST = "host"
PORT = "port"
USER = "user"
PASSWORD = "password"
PYTHON_DEPENDENCIES = "python-dependencies"

OPENERP_TYPE = {
    "type": "object",
    "properties": {
        SERIE: {"type": "string"},
        "server": {"type": "string", "format": "uri"},
        "addons": {"type": "string", "format": "uri"},
        "web": {"type": "string", "format": "uri"},
        PYTHON_DEPENDENCIES: {
            "type": "array",
            "items": {"type": "string"}
        },
    },
    "required": [SERIE, "server", "addons", "web"]
}
USER_CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        WORKSPACE: {"type": "string", "format": "uri"},
        CONF_FILES: {
            "type": "array",
            "items": {"type": "string", "format": "uri"},
        },                    
        OPENERP: {
            "type": "array",
            "items": OPENERP_TYPE,
        },
        DEFAULT_SERIE: {"type": "string"},
        DATABASE: {
            "type": "object",
            "properties": {
                HOST: {"type": "string"},
                PORT: {"type": "string"},
                USER: {"type": "string"},
                PASSWORD: {"type": "string"},
            },
            "required": [USER, PASSWORD]
        }
    },
    "required": [WORKSPACE, CONF_FILES, OPENERP, DEFAULT_SERIE]
}