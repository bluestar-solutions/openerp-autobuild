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

import os
import sys
import getpass
import json
import validictory
import oebuild_logger
from settings_parser import user_conf_schema, oebuild_conf_parser

logger = oebuild_logger.getLogger()

USER_HOME_PATH = os.path.expanduser("~")
USER_CONFIG_PATH = '%s/.config' % USER_HOME_PATH
USER_OEBUILD_CONFIG_PATH = '%s/openerp-autobuild' % USER_CONFIG_PATH
USER_OEBUILD_CONFIG_FILE = '%s/oebuild_config-%s.json' % (USER_OEBUILD_CONFIG_PATH, oebuild_conf_parser.VERSION)

if not os.path.exists(USER_CONFIG_PATH):
    os.makedirs(USER_CONFIG_PATH)
if not os.path.exists(USER_OEBUILD_CONFIG_PATH):
    os.makedirs(USER_OEBUILD_CONFIG_PATH)
if not os.path.exists(USER_OEBUILD_CONFIG_FILE):
    infile = open("%s/conf/default_user_config.json" % OE_HOME_PATH) #@UndefinedVariable
    outfile = open(USER_OEBUILD_CONFIG_FILE, 'w')
    for line in infile:
        outfile.write(line.replace("$USERNAME", getpass.getuser()))
    infile.close()
    outfile.close

def load_user_config_file():
    if not (os.path.exists(USER_OEBUILD_CONFIG_FILE) and os.path.isfile(USER_OEBUILD_CONFIG_FILE)):
        logger.error('User openerp configuration file does not exist : %s' % USER_OEBUILD_CONFIG_FILE)
        sys.exit(1)
        
    with open(USER_OEBUILD_CONFIG_FILE, "r") as source_file:
        try:
            conf = json.load(source_file)
        except ValueError, error:
            logger.error('%s is not JSON valid : %s' % (USER_OEBUILD_CONFIG_FILE, error))
            sys.exit(1)
        try:
            validictory.validate(conf, user_conf_schema.USER_CONFIG_SCHEMA)
        except ValueError, error:
            logger.error('%s is not a valid user configuration file : %s' % (USER_OEBUILD_CONFIG_FILE, error))
            sys.exit(1)
        
    return conf
