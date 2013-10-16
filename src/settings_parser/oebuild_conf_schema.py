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

DEPENDENCIES = "dependencies"
SCM = "scm"
SCM_GIT = "git"
SCM_BZR = "bzr"
SCM_LOCAL = "local"
URL = "url"
BZR_REV = "bzr-rev"
GIT_BRANCH = "git-branch"
DESTINATION = "destination"
OEBUILD_VERSION = "oebuild-version"
ADDONS_PATH = "addons-path"
PROJECT = "project"
NAME = "name"
SOURCE = "source"
OPENERP = "openerp"
SERIE = "serie"

OPENERP_TYPE = {
    "type": "object",
    "properties": {
        URL: {"type": "string", "format": "uri", "required": False},
        BZR_REV: {"type": "string", "pattern": "^[0-9]+$", "required": False},
    },
    "required": False,
}
DEPENDENCY = {
    "type": "object",
    "properties": {
        NAME: {"type": "string", "required": True},
        DESTINATION: {"type": "string", "format": "uri", "required": False},
        ADDONS_PATH: {"type": "string", "format": "uri", "required": False},
        SOURCE: {
            "type": "object", 
            "oneOf": [
                {"$ref": "#/definitions/gitDependency"}, 
                {"$ref": "#/definitions/bzrDependency"},
                {"$ref": "#/definitions/localDependency"},
            ], 
            "required": True
        },
    }
}
OEBUILD_SCHEMA = {
    "type": "object",
    "properties": {
        OEBUILD_VERSION: {"type": "string", "pattern": "^[0-9]+|.[0-9]+$", "required": True},
        PROJECT: {"type": "string", "pattern": "^[a-z|0-9|-]+$", "required": True},
        OPENERP: {
            "type": "object",
            "properties": {
                SERIE: {"type": "string", "required": True},
                "server": OPENERP_TYPE,
                "addons": OPENERP_TYPE,
                "web": OPENERP_TYPE,
            }
        },
        DEPENDENCIES: {
            "type": "array",
            "items": {"type": DEPENDENCY},
            "required": True
        }
    },
    "definitions": {
        "gitDependency": {
            "type": "object",
            "properties": {
                SCM: {"type": "string", "pattern": SCM_GIT, "required": True},
                URL: {"type": "string", "format": "uri", "required": True},
                GIT_BRANCH: {"type": "string", "required": False},
            },
        },
        "bzrDependency": {
            "type": "object",
            "properties": {
                SCM: {"type": "string", "pattern": SCM_BZR, "required": True},
                URL: {"type": "string", "format": "uri", "required": True},
                BZR_REV: {"type": "string", "pattern": "^[0-9]+$", "required": False},
            },
        },
        "localDependency": {
            "type": "object",
            "properties": {
                SCM: {"type": "string", "pattern": SCM_LOCAL, "required": True},
                URL: {"type": "string", "format": "uri", "required": True},
            },
        }     
    }
}