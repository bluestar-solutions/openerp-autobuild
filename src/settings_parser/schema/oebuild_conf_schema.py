# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP Autobuild
#    Copyright (C) 2012-2015 Bluestar Solutions Sàrl (<http://www.blues2.ch>).
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
PROJECT = "project"
PIP_URL = "pip-url"
OPENERP = "openerp"
SERIE = "serie"
PYTHON_DEPENDENCIES = "python-dependencies"
DEPENDENCIES = "dependencies"
RUN_SCRIPTS = "run-scripts"
SCM = "scm"
SCM_GIT = "git"
SCM_BZR = "bzr"
SCM_LOCAL = "local"
URL = "url"
GIT_BRANCH = "git-branch"
GIT_COMMIT = "git-commit"
BZR_REV = "bzr-rev"
DESTINATION = "destination"
ADDONS_PATH = "addons-path"
NAME = "name"
SOURCE = "source"
ENTERPRISE_SOURCE = "enterprise-source"
SPECIFIER = "specifier"
OPTIONS = "options"
I18N_ADDONS = "i18n-addons"

OPENERP_TYPE = {
    "type": "object",
    "properties": {
        URL: {"type": "string", "format": "uri"},
        GIT_BRANCH: {"type": "string"},
        GIT_COMMIT: {"type": "string", "pattern": "[a-z0-9]{40}"}
    },
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
DEPENDENCY = {
    "type": "object",
    "properties": {
        NAME: {"type": "string"},
        DESTINATION: {"type": "string", "format": "uri"},
        ADDONS_PATH: {"type": "string", "format": "uri"},
        SOURCE: {
            "type": "object",
            "oneOf": [
                {"$ref": "#/definitions/gitDependency"},
                {"$ref": "#/definitions/localDependency"},
                {"$ref": "#/definitions/bzrDependency"},
            ],
        },
    },
    "required": [NAME],
    "additionalProperties": False
}
DEPENCENCY_DEFINITIONS = {
    "gitDependency": {
        "type": "object",
        "properties": {
            SCM: {"type": "string", "pattern": SCM_GIT},
            URL: {"type": "string", "format": "uri"},
            GIT_BRANCH: {"type": "string"},
            GIT_COMMIT: {"type": "string", "pattern": "[a-z0-9]{40}"}
        },
        "required": [SCM, URL],
        "not": {
            "anyOf": [
                {"required": [GIT_BRANCH, GIT_COMMIT]}
            ]
        },
        "additionalProperties": False
    },
    "localDependency": {
        "type": "object",
        "properties": {
            SCM: {"type": "string", "pattern": SCM_LOCAL},
            URL: {"type": "string", "format": "uri"},
        },
        "required": [SCM, URL],
        "additionalProperties": False
    },
    "bzrDependency": {
        "type": "object",
        "properties": {
            SCM: {"type": "string", "pattern": SCM_BZR},
            URL: {"type": "string", "format": "uri"},
            BZR_REV: {"type": "string", "pattern": "^[0-9]+$"},
        },
        "required": [SCM, URL],
        "additionalProperties": False
    },
}
OEBUILD_SCHEMA = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        OEBUILD_VERSION: {"type": "string", "pattern": static_params.VERSION},
        PROJECT: {"type": "string", "pattern": "^[a-z|0-9|-]+$"},
        OPENERP: {
            "type": "object",
            "properties": {
                SERIE: {"type": "string"},
                SOURCE: OPENERP_TYPE,
                ENTERPRISE_SOURCE: OPENERP_TYPE,
            },
            "required": [SERIE],
            "additionalProperties": False
        },
        PYTHON_DEPENDENCIES: {
            "type": "array",
            "items": PYTHON_DEPENDENCY
        },
        PIP_URL: {"type": "string", "format": "uri"},
        DEPENDENCIES: {
            "type": "array",
            "items": DEPENDENCY
        },
        RUN_SCRIPTS: {
            "type": "array",
            "items": {"type": "string"}
        },
        I18N_ADDONS: {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": [OEBUILD_VERSION, PROJECT, DEPENDENCIES],
    "additionalProperties": False,
    "definitions": DEPENCENCY_DEFINITIONS
}
OEBUILD_ALT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        OEBUILD_VERSION: {"type": "string", "pattern": static_params.VERSION},
        OPENERP: {
            "type": "object",
            "properties": {
                SOURCE: OPENERP_TYPE
            },
            "additionalProperties": False
        },
        DEPENDENCIES: {
            "type": "array",
            "items": DEPENDENCY
        }
    },
    "required": [OEBUILD_VERSION, DEPENDENCIES],
    "additionalProperties": False,
    "definitions": DEPENCENCY_DEFINITIONS
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
