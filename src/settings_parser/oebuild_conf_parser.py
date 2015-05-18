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
import json
import jsonschema
from oebuild_logger import _ex, logger
from settings_parser.schema import oebuild_conf_schema as schema
import dialogs
import re
import json_regex as jre
import static_params
import difflib


class IgnoreSubConf(Exception):
    pass


class OEBuildConfParser():

    _analyze = False
    params = None

    def __init__(self, params, analyze=False):
        self._analyze = analyze
        self.params = params
        for dfile in static_params.DEPRECATED_FILES:
            if os.path.exists(dfile):
                logger.warning('File %s is deprecated, you can remove '
                               'it from the project' % dfile)

    def _load_file(self, file_name, strict_mode=True, alt_schema=False):
        conf = None
        with open(file_name, "r") as source_file:
            try:
                conf = json.load(source_file)
            except ValueError, e:
                if strict_mode:
                    logger.error(
                        _ex('%s is not JSON valid' % file_name, e)
                    )
                    sys.exit(1)
                else:
                    logger.warning(
                        _ex('%s is not JSON valid and will be ignored' %
                            file_name, e)
                    )
                    raise IgnoreSubConf()

        if conf.get(schema.OEBUILD_VERSION, None) != static_params.VERSION:
            conf = self._update_file(conf.get(schema.OEBUILD_VERSION, None),
                                     file_name, alt_schema)
        self._validate_conf(conf, file_name, strict_mode, alt_schema)

        return conf

    def _load_alt_file(self, source_conf, file_name):
        conf = self._load_file(file_name, strict_mode=False, alt_schema=True)
        new_conf = dict(source_conf)

        for dep2 in conf[schema.DEPENDENCIES]:
            for dep in new_conf[schema.DEPENDENCIES]:
                if dep[schema.NAME] == dep2[schema.NAME]:
                    dep.update(dep2)

        return new_conf

    def _validate_conf(self, conf, file_name, strict_mode=True,
                       alt_schema=False):
        try:
            jsonschema.validate(conf, schema.OEBUILD_ALT_SCHEMA if alt_schema
                                else schema.OEBUILD_SCHEMA)
        except Exception, e:
            if strict_mode:
                logger.error(
                    _ex('%s is not a valid configuration file' % file_name, e)
                )
                sys.exit(1)
            else:
                logger.warning(
                    _ex('%s will be ignored because it is not a valid '
                        'configuration file' % file_name, e)
                )
                raise IgnoreSubConf()

    def load_oebuild_config_file(self, conf_file_list):
        if not (os.path.exists(static_params.PROJECT_CONFIG_FILE) and
                os.path.isfile(static_params.PROJECT_CONFIG_FILE)):
            logger.error(
                'The project configuration does not exist : %s' %
                static_params.PROJECT_CONFIG_FILE
            )
            sys.exit(1)

        conf = self._load_file(static_params.PROJECT_CONFIG_FILE)

        for conf_name in conf_file_list:
            conf_file_name = (static_params.PROJECT_ALT_CONFIF_FILE_PATTERN %
                              conf_name)
            if (os.path.exists(conf_file_name) and
                    os.path.isfile(conf_file_name)):
                try:
                    conf = self._load_alt_file(conf, conf_file_name)
                except IgnoreSubConf:
                    pass

        return conf

    def load_transitive_oebuild_config_file(self, conf_file_path,
                                            conf_file_list):
        conf_file = '%s/%s' % (conf_file_path,
                               static_params.PROJECT_CONFIG_FILE)
        if not (os.path.exists(conf_file) and os.path.isfile(conf_file)):
            # Probably not an oebuild project
            logger.info(
                '%s : %s file not found. It is probably not a oebuild module' %
                (conf_file_path, static_params.PROJECT_CONFIG_FILE)
            )
            raise IgnoreSubConf()

        conf = self._load_file(conf_file)

        for conf_name in conf_file_list:
            conf_file = '%s/%s' % (
                conf_file_path,
                static_params.PROJECT_ALT_CONFIF_FILE_PATTERN % conf_name
            )
            if os.path.exists(conf_file) and os.path.isfile(conf_file):
                try:
                    conf = self._load_alt_file(conf, conf_file)
                except IgnoreSubConf:
                    pass

        return conf

    def create_oebuild_config_file(self, default_serie):
        overwrite = "no"
        if os.path.exists(static_params.PROJECT_CONFIG_FILE):
            overwrite = dialogs.query_yes_no(
                "%s file already exists, overwrite it with default one ?" %
                static_params.PROJECT_CONFIG_FILE, overwrite
            )
        if (os.path.exists(static_params.PROJECT_CONFIG_FILE) and
                overwrite == "no"):
            return

        with open(static_params.DEFAULT_PROJECT_CONFIG_FILE, 'r') as f:
            content = f.read()

        content = re.sub(r'\$OEBUILD_VERSION', static_params.VERSION, content)
        content = re.sub(r'\$PROJECT_NAME',
                         os.getcwd().split('/')[-1], content)
        content = re.sub(r'\$SERIE', default_serie, content)

        with open(static_params.PROJECT_CONFIG_FILE, 'w+') as f:
            f.write(content)

    def _update_file(self, version_from, file_name, alt_schema=False):
        logger.info(
            '%s is in version %s and openerp-autobuild is in version %s' %
            (file_name, version_from, static_params.VERSION)
        )

        valid_keys = (self.UPDATE_ALT_FROM.keys() if alt_schema
                      else self.UPDATE_FROM.keys())
        if version_from not in valid_keys:
            logger.warning(
                "Cannot update from version %s: %s will be ignored" %
                (version_from, file_name)
            )
            raise IgnoreSubConf()

        updated_fname = file_name + ".updated"
        with open(file_name, "r") as source_file:
            orig_content = source_file.read()
            with open(updated_fname, "w+") as updated_file:
                content = orig_content
                regs = (self.UPDATE_ALT_FROM[version_from] if alt_schema
                        else self.UPDATE_FROM[version_from])

                if not alt_schema and version_from == "1.7":
                    python_deps_file = ('%s/default_python_deps.json' %
                                        self.params.USER_CONFIG_PATH)
                    if (os.path.exists(python_deps_file) and
                            os.path.isfile(python_deps_file)):
                        with open(python_deps_file, "r") as f:
                            python_deps = json.load(f)
                    else:
                        python_deps = []

                    regs.append((r'(\n?)(\s*)("dependencies"\s*:)',
                                 r'\1\2"python-dependencies": %s,\1\2\3' %
                                 json.dumps(python_deps)))

                for pattern, replace in regs:
                    old_content = content
                    content = re.sub(pattern, replace, content)
                updated_file.write(content)

        diff = ''.join(difflib.unified_diff(orig_content.splitlines(1),
                                            old_content.splitlines(1)))
        logger.warning("Changes to apply on file '%s':\n%s", file_name, diff)
        answer = dialogs.ANSWER_NO
        if len(file_name.split('/')) == 1 and not self._analyze:
            answer = dialogs.query_yes_no(
                "Do you want to replace the project configuration files "
                "by the updated version (otherwise the updated versions "
                "will be saved to new files) ?", default=dialogs.ANSWER_NO
            )
        if answer == dialogs.ANSWER_YES:
            os.rename(updated_fname, file_name)
            updated_fname = file_name
            logger.info(
                '%s has been updated to version %s' %
                (file_name, static_params.VERSION)
            )
        else:
            logger.info(
                'An updated version of %s will be used and stored in %s' %
                (file_name, updated_fname)
            )

        with open(updated_fname, "r") as updated_file:
            return json.load(updated_file)

    UPDATE_FROM = {
        "1.7": [jre.update_version("1.7", "2.1"),
                jre.remove_param_array('server'),
                jre.remove_param_array('addons'),
                jre.remove_param_array('web')]
    }

    UPDATE_ALT_FROM = {
        "1.7": [jre.update_version("1.7", "2.1"),
                jre.remove_param("project"),
                jre.remove_param("serie")]
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
