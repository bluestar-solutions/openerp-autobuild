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

VERSION = '2.1'

OE_HOME_PATH = os.path.dirname(os.path.realpath(__file__))
DEFAULT_OE_CONFIG_FILE = '%s/conf/default_openerp_config' % OE_HOME_PATH
DEFAULT_PROJECT_CONFIG_FILE = '%s/conf/default_project_config.json' % OE_HOME_PATH
DEFAULT_USER_CONFIG_FILE = '%s/conf/default_user_config.json' % OE_HOME_PATH

USER_HOME_PATH = os.path.expanduser("~")
USER_CONFIG_PATH = '%s/.config/openerp-autobuild' % USER_HOME_PATH

ETC_CONFIG_FILE = "/etc/oebuild_config.json"
USER_CONFIG_FILE = '%s/oebuild_config.json' % USER_CONFIG_PATH

OE_CONFIG_FILE = '.openerp-dev-default'

PROJECT_CONFIG_FILE = 'oebuild.conf'
PROJECT_ALT_CONFIF_FILE_PATTERN = 'oebuild-%s.conf'

DEPRECATED_FILES = ('.project-dependencies',)

INIT_PY_TPL = '%s/.config/openerp-autobuild/initpy.tpl' % USER_HOME_PATH
OPENERP_PY_TPL = '%s/.config/openerp-autobuild/openerppy.tpl' % USER_HOME_PATH
HEADER_PY_TPL = '%s/.config/openerp-autobuild/header.tpl' % USER_HOME_PATH
CLASS_TPL = '%s/.config/openerp-autobuild/class.tpl' % USER_HOME_PATH
