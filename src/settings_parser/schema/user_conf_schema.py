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

import static_params

OEBUILD_VERSION = "oebuild-version"
URL = "url"
BZR_REV = "bzr-rev"
OPENERP = "openerp"
SERIE = "serie"
USER = "user"
MODULE_AUTHOR = "module_author"
WEBSITE = "website"
WORKSPACE = "workspace"
CONF_FILES = "custom-configuration-files"
DEFAULT_SERIE = "default-serie"
DATABASE = "database"
HOST = "host"
PORT = "port"
USER = "user"
PASSWORD = "password"
PYTHON_DEPENDENCIES = "python-dependencies"
NAME = "name"
SPECIFIER = "specifier"
COMMENT = "comment"

PYTHON_DEPENDENCY = {
    "type": "object",
    "properties": {
        NAME: {"type": "string"},
        SPECIFIER: {"type": "string"}
    },
    "required": [NAME],
    "additionalProperties" : False
}
OPENERP_TYPE = lambda default = True: {
    "type": "object",
    "properties": {
        SERIE: {"type": "string"},
        "server": {"type": "string", "format": "uri"},
        "addons": {"type": "string", "format": "uri"},
        "web": {"type": "string", "format": "uri"},
        PYTHON_DEPENDENCIES: {
            "type": "array",
            "items": PYTHON_DEPENDENCY
        },
    },
    "required": [SERIE, "server", "addons", "web", PYTHON_DEPENDENCIES] if default else [SERIE],
    "additionalProperties": False
}
USER_CONFIG_SCHEMA = lambda default = True: {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        COMMENT: {"type": "array", "items": {"type": "string"}},
        USER: {"type": "string"},
        MODULE_AUTHOR: {"type": "string"},
        WEBSITE: {"type": "string", "format": "url"},
        OEBUILD_VERSION: {"type": "string", "pattern": static_params.VERSION},
        WORKSPACE: {"type": "string", "format": "uri"},
        CONF_FILES: {
            "type": "array",
            "items": {"type": "string", "format": "uri"},
        },
        OPENERP: {
            "type": "array",
            "items": OPENERP_TYPE(default),
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
            "additionalProperties" : False
        }
    },
    "required": [WORKSPACE, CONF_FILES, OPENERP, DEFAULT_SERIE, DATABASE] if default else [CONF_FILES, OPENERP, DATABASE],
    "additionalProperties" : False
}
