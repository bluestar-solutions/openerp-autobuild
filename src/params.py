#!/usr/bin/env python
# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP Autobuild
#    Copyright (C) 2013 Bluestar Solutions Sàrl (<http://www.blues2.ch>).
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

VERSION = '1.8'

OE_HOME_PATH = os.path.dirname(os.path.realpath(__file__))

USER_HOME_PATH = os.path.expanduser("~")
USER_CONFIG_PATH = '%s/.config' % USER_HOME_PATH
USER_OEBUILD_CONFIG_PATH = '%s/openerp-autobuild' % USER_CONFIG_PATH
USER_OEBUILD_CONFIG_FILE = '%s/oebuild_config.json' % USER_OEBUILD_CONFIG_PATH
USER_OEBUILD_CONFIG_FILE_1_7 = '%s/oebuild_config-1.7.json' % USER_OEBUILD_CONFIG_PATH

SUPPORTED_VERSIONS = ('1.7', '1.8')
DEFAULT_CONF_FILENAME = 'oebuild.conf'
CUSTOM_CONF_FILENAME = 'oebuild-%s.conf'
DEPRECATED_FILES = ('.project-dependencies',)
