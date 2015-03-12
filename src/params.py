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


class Params():

    USER_HOME_PATH = os.path.expanduser("~")
    USER_CONFIG_PATH = '%s/.config/openerp-autobuild' % USER_HOME_PATH
    USER_CONFIG_FILE = '%s/oebuild_config.json' % USER_CONFIG_PATH

    ETC_CONFIG_FILE = "/etc/oebuild_config.json"

    def __init__(self, user_home_path=None, etc_path=None):

        if user_home_path:
            self.USER_HOME_PATH = user_home_path
            self.USER_CONFIG_PATH = '%s' % self.USER_HOME_PATH
            self.USER_CONFIG_FILE = ('%s/oebuild_config.json' %
                                     self.USER_CONFIG_PATH)

        self.INIT_PY_TPL = ('%s/.config/openerp-autobuild/initpy.tpl' %
                            self.USER_HOME_PATH)
        self.OPENERP_PY_TPL = ('%s/.config/openerp-autobuild/openerppy.tpl' %
                               self.USER_HOME_PATH)
        self.HEADER_PY_TPL = ('%s/.config/openerp-autobuild/header.tpl' %
                              self.USER_HOME_PATH)
        self.CLASS_TPL = ('%s/.config/openerp-autobuild/class.tpl' %
                          self.USER_HOME_PATH)

        if etc_path:
            self.ETC_CONFIG_FILE = "%s/oebuild_config.json" % etc_path

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
