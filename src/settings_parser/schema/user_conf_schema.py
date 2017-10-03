# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP Autobuild
#    Copyright (C) 2012-2017 Bluestar Solutions Sàrl (<http://www.blues2.ch>).
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
from settings_parser.schema.oebuild_conf_schema import (
    SOURCE, GIT_BRANCH, GIT_COMMIT
)
OEBUILD_VERSION = "oebuild-version"
OEBUILD_LOG_LEVEL = "oebuild-log-level"
URL = "url"
OPENERP = "openerp"
SERIE = "serie"
BIN = "bin"
USER = "user"
MODULE_AUTHOR = "module_author"
WEBSITE = "website"
WORKSPACE = "workspace"
CONF_FILES = "custom-configuration-files"
DEFAULT_SERIE = "default-serie"
DATABASE = "database"
HOST = "host"
PORT = "port"
PASSWORD = "password"
PYTHON_DEPENDENCIES = "python-dependencies"
NAME = "name"
SPECIFIER = "specifier"
OPTIONS = "options"
COMMENT = "comment"

OPENERP_TYPE = {
    "type": "object",
    "properties": {
        URL: {"type": "string", "format": "uri"},
        GIT_BRANCH: {"type": "string"},
        GIT_COMMIT: {"type": "string", "pattern": "[a-z0-9]{40}"}
    },
    "required": [URL],
    "additionalProperties": False
}
PYTHON_DEPENDENCY = {
    "type": "object",
    "properties": {
        NAME: {"type": "string"},
        SPECIFIER: {"type": "string"},
        OPTIONS: {"type": "string"}
    },
    "required": [NAME],
    "additionalProperties": False
}


def OPENERP_CONF_TYPE(default=True):
    return {
        "type": "object",
        "properties": {
            SERIE: {"type": "string"},
            BIN: {"type": "string"},
            SOURCE: OPENERP_TYPE,
            PYTHON_DEPENDENCIES: {
                "type": "array",
                "items": PYTHON_DEPENDENCY
            },
        },
        "required": [SERIE, SOURCE,
                     PYTHON_DEPENDENCIES] if default else [SERIE],
        "additionalProperties": False
    }


def USER_CONFIG_SCHEMA(default=True):
    return {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "object",
        "properties": {
            COMMENT: {"type": "array", "items": {"type": "string"}},
            MODULE_AUTHOR: {"type": "string"},
            WEBSITE: {"type": "string", "format": "url"},
            OEBUILD_VERSION: {"type": "string", "pattern":
                              static_params.VERSION},
            OEBUILD_LOG_LEVEL: {"enum": ["DEBUG", "INFO", "WARNING", "ERROR"]},
            WORKSPACE: {"type": "string", "format": "uri"},
            CONF_FILES: {
                "type": "array",
                "items": {"type": "string", "format": "uri"},
            },
            OPENERP: {
                "type": "array",
                "items": OPENERP_CONF_TYPE(default),
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
                "additionalProperties": False
            }
        },
        "required": ([WORKSPACE, CONF_FILES, OPENERP, DEFAULT_SERIE, DATABASE]
                     if default else [CONF_FILES, OPENERP, DATABASE]),
        "additionalProperties": False
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
