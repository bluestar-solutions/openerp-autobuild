# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP Autobuild
#    Copyright (C) 2012-2017 Bluestar Solutions Sàrl (<http://www.blues2.ch>).
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

from settings_parser.schema import user_conf_schema
from oebuild_logger import logger
import re
import json_regex as jre


def user_oebuild_config_file_1_7(params):
    return '%s/oebuild_config-1.7.json' % params.USER_CONFIG_PATH


def update_from_1_7(conf, conf_1_7, params):

    with open(params.USER_CONFIG_FILE) as f:
        content = f.read()

    with open(params.USER_CONFIG_FILE, "w+") as f:
        if conf[user_conf_schema.WORKSPACE] != conf_1_7.get(
                user_conf_schema.WORKSPACE, conf[user_conf_schema.WORKSPACE]
        ):
            reg = jre.add_param_before(user_conf_schema.WORKSPACE,
                                       conf_1_7[user_conf_schema.WORKSPACE],
                                       user_conf_schema.CONF_FILES)
            content = re.sub(reg[0], reg[1], content)
            logger.warning("Your workspace is %s, but the recommended "
                           "value is %s, check your "
                           "configuration file: %s",
                           conf_1_7[user_conf_schema.WORKSPACE],
                           user_conf_schema.WORKSPACE,
                           params.USER_CONFIG_FILE)
        if conf[user_conf_schema.CONF_FILES] != conf_1_7.get(
                user_conf_schema.CONF_FILES, conf[user_conf_schema.CONF_FILES]
        ):
            reg = jre.set_param_array(user_conf_schema.CONF_FILES,
                                      conf_1_7[user_conf_schema.CONF_FILES])
            content = re.sub(reg[0], reg[1], content)

        if conf[user_conf_schema.DEFAULT_SERIE] != conf_1_7.get(
            user_conf_schema.DEFAULT_SERIE,
            conf[user_conf_schema.DEFAULT_SERIE]
        ):
            reg = jre.set_param_value(user_conf_schema.DEFAULT_SERIE,
                                      conf_1_7[user_conf_schema.DEFAULT_SERIE])
            content = re.sub(reg[0], reg[1], content)

        default_series = {}
        new_series = []
        for default_serie in conf[user_conf_schema.OPENERP]:
            default_series[default_serie[user_conf_schema.SERIE]] = \
                default_serie
        for serie_1_7 in conf_1_7.get(user_conf_schema.OPENERP, []):
            if serie_1_7[user_conf_schema.SERIE] not in default_series.keys():
                new_series.append(serie_1_7)
        if new_series:
            oe_content = ''
            first_serie = True
            for new_serie in new_series:
                oe_content += '%s{' % ('' if first_serie else ',')
                first_elem = True
                for key, val in new_serie.iteritems():
                    if key in ['server', 'addons', 'web']:
                        continue
                    if key == 'serie' and val == 'trunk':
                        val = 'master'
                    oe_content += ('%s%s"%s": "%s"' %
                                   ('\n' if first_elem
                                    else ',\n', ' ' * 8, key, val))
                    first_elem = False
                oe_content += '\n%s}' % (' ' * 4)
                first_serie = False
            content = re.sub(
                r'(\n?\s*"%s"\s*:[\s|\n]*)(\[[\s|\n]*\])' %
                user_conf_schema.OPENERP, r'\1[%s]' % oe_content, content
            )

        db_content = []
        if user_conf_schema.DATABASE in conf_1_7.keys():
            db_conf = conf[user_conf_schema.DATABASE]
            db_conf_1_7 = conf_1_7[user_conf_schema.DATABASE]
            if db_conf[user_conf_schema.HOST] != db_conf_1_7.get(
                user_conf_schema.HOST, db_conf[user_conf_schema.HOST]
            ):
                db_content.append('%s"%s": "%s"' %
                                  (' ' * 8, user_conf_schema.HOST,
                                   db_conf_1_7[user_conf_schema.HOST]))
            if db_conf[user_conf_schema.PORT] != db_conf_1_7.get(
                user_conf_schema.PORT, db_conf[user_conf_schema.PORT]
            ):
                db_content.append('%s"%s": "%s"' %
                                  (' ' * 8, user_conf_schema.PORT,
                                   db_conf_1_7[user_conf_schema.PORT]))
            if db_conf[user_conf_schema.USER] != db_conf_1_7.get(
                user_conf_schema.USER, db_conf[user_conf_schema.USER]
            ):
                db_content.append('%s"%s": "%s"' %
                                  (' ' * 8, user_conf_schema.USER,
                                   db_conf_1_7[user_conf_schema.USER]))
            if db_conf[user_conf_schema.PASSWORD] != db_conf_1_7.get(
                user_conf_schema.PASSWORD, db_conf[user_conf_schema.PASSWORD]
            ):
                db_content.append('%s"%s": "%s"' %
                                  (' ' * 8, user_conf_schema.PASSWORD,
                                   db_conf_1_7[user_conf_schema.PASSWORD]))
        if db_content:
            content = re.sub(
                r'(\n?)(\s*)("%s"\s*:[\s|\n]*)(\{[\s|\n]*\})' %
                user_conf_schema.DATABASE,
                r'\1\2\3{\n%s\2}' % (',\n'.join(db_content) + '\n'), content
            )

        f.write(content)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
