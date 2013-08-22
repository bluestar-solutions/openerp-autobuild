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

OPENERP_TYPE = {
    "type": "object",
    "properties": {
        SERIE: {"type": "string", "required": True},
        "server": {"type": "string", "format": "uri", "required": True},
        "addons": {"type": "string", "format": "uri", "required": True},
        "web": {"type": "string", "format": "uri", "required": True},
    }
}
USER_CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        WORKSPACE: {"type": "string", "format": "uri", "required": True},
        CONF_FILES: {
            "type": "array",
            "items": {"type": "string", "format": "uri"},
            "required": True,
        },                    
        OPENERP: {
            "type": "array",
            "items": OPENERP_TYPE,
            "required": True,
        },
        DEFAULT_SERIE: {"type": "string", "required": True},
        DATABASE: {
            "type": "object",
            "properties": {
                HOST: {"type": "string", "required": False},
                PORT: {"type": "string", "required": False},
                USER: {"type": "string", "required": True},
                PASSWORD: {"type": "string", "required": True},
            }
        }
    },
}