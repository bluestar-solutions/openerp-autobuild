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

import oebuild_conf_schema as schema

OPENERP_TYPE = {
    "type": "object",
    "properties": {
        schema.URL: {"type": "string", "format": "uri"},
        schema.BZR_REV: {"type": "string", "pattern": "^[0-9]+$"},
    },
}
DEPENDENCY = {
    "type": "object",
    "properties": {
        schema.NAME: {"type": "string"},
        schema.DESTINATION: {"type": "string", "format": "uri"},
        schema.ADDONS_PATH: {"type": "string", "format": "uri"},
        schema.SOURCE: {
            "type": "object", 
            "oneOf": [
                {"$ref": "#/definitions/gitDependency"}, 
                {"$ref": "#/definitions/bzrDependency"},
                {"$ref": "#/definitions/localDependency"}
            ],
        },
    },
    "required": [schema.NAME]
}
OEBUILD_SCHEMA = {
    "type": "object",
    "properties": {
        schema.OEBUILD_VERSION: {"type": "string", "pattern": "^[0-9]+|.[0-9]+$"},
        schema.PROJECT: {"type": "string", "pattern": "^[a-z|0-9|-]+$"},
        schema.OPENERP: {
            "type": "object",
            "properties": {
                schema.SERIE: {"type": "string"},
                "server": OPENERP_TYPE,
                "addons": OPENERP_TYPE,
                "web": OPENERP_TYPE,
            },
            "required": [schema.SERIE]
        },
        schema.PYTHON_DEPENDENCIES: {
            "type": "array",
            "items": {"type": "string"}
        },
        schema.DEPENDENCIES: {
            "type": "array",
            "items": DEPENDENCY
        }
    },
    "required": [schema.OEBUILD_VERSION, schema.PROJECT, schema.DEPENDENCIES],
    "definitions": {
        "gitDependency": {
            "type": "object",
            "properties": {
                schema.SCM: {"type": "string", "pattern": schema.SCM_GIT},
                schema.URL: {"type": "string", "format": "uri"},
                schema.GIT_BRANCH: {"type": "string"},
            },
            "required": [schema.SCM, schema.URL]
        },
        "bzrDependency": {
            "type": "object",
            "properties": {
                schema.SCM: {"type": "string", "pattern": schema.SCM_BZR},
                schema.URL: {"type": "string", "format": "uri"},
                schema.BZR_REV: {"type": "string", "pattern": "^[0-9]+$"},
            },
            "required": [schema.SCM, schema.URL]
        },
        "localDependency": {
            "type": "object",
            "properties": {
                schema.SCM: {"type": "string", "pattern": schema.SCM_LOCAL},
                schema.URL: {"type": "string", "format": "uri"},
            },
            "required": [schema.SCM, schema.URL]
        }        
    }
}
