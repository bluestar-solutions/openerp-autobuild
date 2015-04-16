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
import shutil
import static_params


class Params():

    USER_HOME_PATH = os.path.expanduser("~")
    USER_CONFIG_PATH = '%s/.config/openerp-autobuild' % USER_HOME_PATH
    USER_CONFIG_FILE = '%s/oebuild_config.json' % USER_CONFIG_PATH

    ETC_CONFIG_FILE = "/etc/oebuild_config.json"

    def __init__(self, alternate_config_path=None):

        if alternate_config_path:
            self.USER_HOME_PATH = '%s/home' % alternate_config_path
            self.USER_CONFIG_PATH = self.USER_HOME_PATH
            self.USER_CONFIG_FILE = ('%s/oebuild_config.json' %
                                     self.USER_CONFIG_PATH)
            self.ETC_CONFIG_FILE = ("%s/etc/oebuild_config.json" %
                                    alternate_config_path)
            if not os.path.exists(self.USER_HOME_PATH):
                os.makedirs(self.USER_HOME_PATH)

        self.INIT_PY_TPL = self.get_user_config_file('initpy.tpl')
        self.OPENERP_PY_TPL = self.get_user_config_file('openerppy.tpl')
        self.HEADER_PY_TPL = self.get_user_config_file('header.tpl')

    def get_user_config_file(self, name):
        path = '%s/%s' % (self.USER_CONFIG_PATH, name)
        if not os.path.isfile(path):
            shutil.copyfile('%s/%s' % (static_params.DEFAULT_CONF_PATH, name),
                            path)
        return path

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
