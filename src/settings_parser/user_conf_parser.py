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

import os
import sys
import getpass
import json
import jsonschema
from oebuild_logger import _ex, logger
from settings_parser.schema import user_conf_schema
import user_conf_1_7_update
import shutil
import static_params


class UserConfParser():

    params = None

    def __init__(self, params):
        self.params = params
        self._verify()

    def _read_conf(self, file_name):
        with open(file_name, "r") as source_file:
            try:
                return json.load(source_file)
            except ValueError, error:
                logger.error('%s is not JSON valid : %s' %
                             (file_name, error))
                sys.exit(1)

    def _load_conf(self, conf_file, default=True):
        conf = None
        try:
            conf = self._read_conf(conf_file)
            try:
                jsonschema.validate(
                    conf, user_conf_schema.USER_CONFIG_SCHEMA(default)
                )
            except ValueError, error:
                logger.error(
                    '%s is not a valid user configuration file : %s' %
                    (conf_file, error)
                )
                sys.exit(1)
        except IOError, e:
            logger.error(_ex(conf_file, e))
            sys.exit(1)
        return conf

    def load_user_config_file(self):
        if not (os.path.exists(self.params.USER_CONFIG_FILE) and
                os.path.isfile(self.params.USER_CONFIG_FILE)):
            logger.error(
                'User openerp configuration file does not exist : %s' %
                self.params.USER_CONFIG_FILE
            )
            sys.exit(1)

        default_conf = self._load_conf(self.params.ETC_CONFIG_FILE)
        user_conf = self._load_conf(self.params.USER_CONFIG_FILE, False)

        merged_conf = dict(default_conf)
        merged_conf.update(user_conf)

        merged_conf[user_conf_schema.OPENERP] = \
            default_conf[user_conf_schema.OPENERP]
        default_serie_names = [s[user_conf_schema.SERIE]
                               for s in default_conf[user_conf_schema.OPENERP]]
        for serie in user_conf[user_conf_schema.OPENERP]:
            if serie[user_conf_schema.SERIE] in default_serie_names:
                default_serie = [
                    s for s in default_conf[user_conf_schema.OPENERP]
                    if s[user_conf_schema.SERIE] ==
                    serie[user_conf_schema.SERIE]
                ][0]
                merged_serie = default_serie
                merged_serie.update(serie)
                merged_serie[user_conf_schema.PYTHON_DEPENDENCIES] = \
                    default_serie[user_conf_schema.PYTHON_DEPENDENCIES]
                for py_dep in serie.get(
                    user_conf_schema.PYTHON_DEPENDENCIES, []
                ):
                    default_py_dep = [
                        d for d in
                        merged_serie[user_conf_schema.PYTHON_DEPENDENCIES]
                        if d[user_conf_schema.NAME] ==
                        py_dep[user_conf_schema.NAME]
                    ]
                    if default_py_dep:
                        default_py_dep[0].update(py_dep)
                    else:
                        merged_serie[user_conf_schema.PYTHON_DEPENDENCIES].\
                            append(py_dep)
                merged_conf[user_conf_schema.OPENERP].append(merged_serie)
            else:
                merged_conf[user_conf_schema.OPENERP].append(serie)

        merged_conf[user_conf_schema.DATABASE] = \
            default_conf[user_conf_schema.DATABASE]
        merged_conf[user_conf_schema.DATABASE].\
            update(user_conf[user_conf_schema.DATABASE])

        return merged_conf

    def _verify(self):
        user_login = getpass.getuser()
        user_name = user_login
        if os.name == 'posix':
            # Use user full name on posix systems.
            import pwd
            user_name = pwd.getpwuid(os.getuid())[4].split(',')[0]\
                .decode('utf-8').encode('utf-8')

        if not os.path.exists(self.params.USER_CONFIG_PATH):
            os.makedirs(self.params.USER_CONFIG_PATH)
        if not os.path.exists(self.params.USER_CONFIG_FILE):
            infile = open(static_params.DEFAULT_USER_CONFIG_FILE)
            outfile = open(self.params.USER_CONFIG_FILE, 'w')
            for line in infile:
                outfile.write(
                    line
                    .replace("$VERSION", static_params.VERSION)
                    .replace("$USERLOGIN", user_login)
                    .replace("$USERNAME", user_name)
                )
            infile.close()
            outfile.close()

            if os.path.exists(
                user_conf_1_7_update.user_oebuild_config_file_1_7(self.params)
            ):
                conf = self.load_user_config_file()
                conf_1_7 = self._read_conf(
                    user_conf_1_7_update.
                    user_oebuild_config_file_1_7(self.params)
                )
                user_conf_1_7_update.update_from_1_7(conf, conf_1_7,
                                                     self.params)
                self._clean_after_update()

            user_conf = self._load_conf(self.params.USER_CONFIG_FILE, False)
            if (user_conf[user_conf_schema.OEBUILD_VERSION] !=
                    static_params.VERSION):
                self._update(user_conf[user_conf_schema.OEBUILD_VERSION])

    def _clean_after_update(self):
        keep = [self.params.USER_CONFIG_FILE,
                user_conf_1_7_update.user_oebuild_config_file_1_7]

        for f in [
            f for f in os.listdir(self.params.USER_CONFIG_PATH)
            if os.path.join(self.params.USER_CONFIG_PATH, f) not in keep
        ]:
            path = os.path.join(self.params.USER_CONFIG_PATH, f)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)

    def _update(self, version_from):
        #
        # Manage future version update here...
        #
        self._clean_after_update()

UPDATE_FROM = {}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
