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
import shutil
import json
import jsonschema
import oebuild_logger
from settings_parser.schema import user_conf_schema
import params

class UserConfParser():
    
    VERSION_1_7 = '1.7'

    _logger = oebuild_logger.getLogger()
    
    def __init__(self):
        self._verify()
    
    def load_user_config_file(self):
        if not (os.path.exists(params.USER_OEBUILD_CONFIG_FILE) and os.path.isfile(params.USER_OEBUILD_CONFIG_FILE)):
            self._logger.error('User openerp configuration file does not exist : %s' % params.USER_OEBUILD_CONFIG_FILE)
            sys.exit(1)
            
        with open(params.USER_OEBUILD_CONFIG_FILE, "r") as source_file:
            try:
                conf = json.load(source_file)
            except ValueError, error:
                self._logger.error('%s is not JSON valid : %s' % (params.USER_OEBUILD_CONFIG_FILE, error))
                sys.exit(1)
            try:
                jsonschema.validate(conf, user_conf_schema.USER_CONFIG_SCHEMA)
            except ValueError, error:
                self._logger.error('%s is not a valid user configuration file : %s' % (params.USER_OEBUILD_CONFIG_FILE, error))
                sys.exit(1)
                
        return conf
    
    def _verify(self):
        if not os.path.exists(params.USER_CONFIG_PATH):
            os.makedirs(params.USER_CONFIG_PATH)
        if not os.path.exists(params.USER_OEBUILD_CONFIG_PATH):
            os.makedirs(params.USER_OEBUILD_CONFIG_PATH)
        if not os.path.exists(params.USER_OEBUILD_CONFIG_FILE):
            if os.path.exists(params.USER_OEBUILD_CONFIG_FILE_1_7):
                self._update(self.VERSION_1_7)
            else:
                infile = open("%s/conf/default_user_config.json" % params.OE_HOME_PATH)
                outfile = open(params.USER_OEBUILD_CONFIG_FILE, 'w')
                for line in infile:
                    outfile.write(line.replace("$USERNAME", getpass.getuser()))
                infile.close()
                outfile.close()
                
#         keep = [params.USER_OEBUILD_CONFIG_FILE]
#         for f in [f for f in os.listdir(params.USER_OEBUILD_CONFIG_PATH) if os.path.join(params.USER_OEBUILD_CONFIG_PATH, f) not in keep]:
#             path = os.path.join(params.USER_OEBUILD_CONFIG_PATH, f)
#             if os.path.isdir(path):
#                 shutil.rmtree(path)
#             else:
#                 os.remove(path)
    
    def _update(self, version_from):
        if version_from == self.VERSION_1_7:
            self._update_1_7_to_1_8()

    def _update_1_7_to_1_8(self):
        shutil.copyfile(params.USER_OEBUILD_CONFIG_FILE_1_7, params.USER_OEBUILD_CONFIG_FILE)
