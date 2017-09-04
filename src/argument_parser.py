#!/usr/bin/env python
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

import os
from argparse import ArgumentParser, RawDescriptionHelpFormatter
import argcomplete
import static_params
import re


class OEArgumentParser():

    args = None

    def __init__(self):

        parser = ArgumentParser(
            formatter_class=RawDescriptionHelpFormatter,
            description="A developer tool for Odoo/OpenERP "
            "with many features.",
            epilog='''\
goal help:
    %(prog)s <goal> -h

Copyright (C) 2012-2015 Bluestar Solutions Sàrl (<http://www.blues2.ch>).
Released under GNU AGPLv3.
            ''',
            version='''\
Odoo Autobuild %s

Copyright (C) 2012-2015 Bluestar Solutions Sàrl (<http://www.blues2.ch>).
Released under GNU AGPLv3.
            ''' % static_params.VERSION)

        parser_shared = ArgumentParser(add_help=False)
        parser_shared.add_argument(
            '-A', "--alternate-config", dest="alternate_config",
            nargs='?', metavar='<path>',
            const='./devconf', default=None,
            help="Use an alternate directory to find configuration files "
            "instead of /etc and /home/user (for development purpose). "
            "Don't specify <path> to use './devconf' with supplied files."
        )
        parser_shared.add_argument(
            '-l', "--local", action="store_true", dest="local",
            help="Bypass remote updates checks "
            "and try to launch with last parameters."
        )

        subparsers = parser.add_subparsers(metavar="<goal>")

        parser_run_shared = ArgumentParser(add_help=False)
        parser_run_shared.add_argument(
            "-u", "--update", dest="run_update",
            nargs='?', metavar='all|<module1>[,<module2>…]',
            const='project-all', default=None,
            help="Modules to update. Don't specify any module to use "
            "the module list of the current project. --database is required."
        )
        parser_run_shared.add_argument(
            '-i', "--init", dest="run_init",
            nargs='?', metavar='all|<module1>[,<module2>…]',
            const='project-all', default=None,
            help="Modules to install. Don't specify any module to use "
            "the module list of the current project. --database is required."
        )
        parser_run_shared.add_argument(
            '-w', "--without-demo", dest="without_demo",
            nargs='?', metavar='all|none|<module1>[,<module2>…]',
            const='project-all', default='all',
            help="Disable loading demo data for specific module list. "
            "Default is all."
        )

        parser_run = subparsers.add_parser(
            'run', help="Run Odoo server normally.",
            parents=[parser_shared, parser_run_shared]
        )
        parser_run.add_argument(
            "-d", "--database", dest="run_database",
            metavar='<database>', default=None,
            help="Database used when installing or updating modules."
        )
        parser_run.add_argument(
            "-a", "--auto-reload", action="store_true", dest="run_auto_reload",
            help="Enable auto-reloading of python files and xml files "
            "without having to restart the server. Requires pyinotify. "
            "Available only for Odoo version 8.0."
        )
        parser_run.add_argument(
            "-D", "--dev", dest="run_dev",
            metavar='<DEV_MODE>', default=None,
            help="Enable developer mode. Param: List of options "
            "separated by comma. Options : all, "
            "[pudb|wdb|ipdb|pdb], reload, qweb, werkzeug, xml."
            "Available since Odoo version 10.0."
        )
        parser_run.set_defaults(func="run")

        parser_test = subparsers.add_parser(
            'run.test', help="Run Odoo server, perform tests, "
            "stop the server and display tests results.",
            parents=[parser_shared, parser_run_shared]
        )
        parser_test.add_argument(
            '-c', "--test-commit", action="store_true", dest="run_test_commit",
            help="Commit test results in DB."
        )
        parser_test.add_argument(
            '-d', "--database", dest="run_database",
            metavar='<database>',
            help="Database name for tests."
            "Use autobuild_{PROJECT_NAME} if not specified.",
            default='autobuild_%s' % re.sub(
                '[^0-9a-zA-Z_]+', '_', os.getcwd().split('/')[-1])
        )
        parser_test.add_argument(
            '-n', "--new-install", action="store_true",
            dest="run_test_new_install",
            help="Force new install. This will delete the database if "
            "it exists."
        )
        parser_test.add_argument(
            '-D', "--drop-database", action="store_true",
            dest="run_test_drop_database",
            help="Drop used database before exiting."
        )
        parser_test.add_argument(
            '-a', "--analyze", action="store_true", dest="run_test_analyze",
            help="Analyze log and stop OpenERP, exit with status 0 if all "
            "test successfully pass, 1 otherwise. Used for "
            "continuous integration."
        )
        parser_test.add_argument(
            '-C', "--continue", action="store_true", dest="run_test_continue",
            help="Continue running OpenERP server when tests are done."
        )
        parser_test.set_defaults(func="test")

        parser_init_new = subparsers.add_parser(
            'project.init', help="Initialize an empty OpenERP project.",
            parents=[parser_shared]
        )
        parser_init_new.set_defaults(func="init-new")

        parser_project_version = subparsers.add_parser(
            'project.version', help="Set the version of all project modules",
            parents=[parser_shared]
        )
        parser_project_version.add_argument(
            '-n', '--new-version', metavar='<version>',
            dest="project_version_new_version", default=None,
            help="The modules new version"
        )
        parser_project_version.set_defaults(func="project-version")

        parser_assembly = subparsers.add_parser(
            'project.assembly',
            help="Prepare all files to deploy in target folder.",
            parents=[parser_shared]
        )
        parser_assembly.add_argument(
            '-i', "--include-odoo", action="store_true",
            dest="project_assembly_include_odoo",
            help="Include OpenERP in target."
        )
        parser_assembly.add_argument(
            '-t', "--only-translations", action="store_true",
            dest="project_assembly_only_i18n",
            help="Include only project addons translations in target."
        )
        parser_assembly.set_defaults(func="assembly")

        parser_i18n_export = subparsers.add_parser(
            'project.i18n.export',
            help="Export i18n templates files for addons specified "
            "in project configuration file.",
            parents=[parser_shared]
        )
        parser_i18n_export.add_argument(
            '-d', "--database", dest="run_database",
            metavar='<database>',
            help="Database name for i18n export."
            "Use autobuild_{PROJECT_NAME} if not specified.",
            default='autobuild_%s' % re.sub(
                '[^0-9a-zA-Z_]+', '_', os.getcwd().split('/')[-1])
        )
        parser_i18n_export.add_argument(
            '-D', "--drop-database", action="store_true",
            dest="run_test_drop_database",
            help="Drop used database before exiting."
        )
        parser_i18n_export.set_defaults(func="i18n-export")

        parser_create_module = subparsers.add_parser(
            'module.create', help="Create a new module.",
            parents=[parser_shared]
        )
        parser_create_module.add_argument(
            'module_create_name', metavar='<name>', default=None,
            help="The module name."
        )
        parser_create_module.add_argument(
            '-L', '--long_name', dest="module_create_long_name",
            metavar='<long-name>', default=None,
            required=False, help="The module long name"
        )
        parser_create_module.add_argument(
            '-c', '--category', dest="module_create_category",
            metavar='<category>', required=False, default=None,
            help="The module category"
        )
        parser_create_module.set_defaults(func="create-module")

        parser_eclipse_init = subparsers.add_parser(
            'eclipse.init', help="Initialize an Eclipse PyDev project.",
            parents=[parser_shared]
        )
        parser_eclipse_init.set_defaults(func="init-eclipse")

        argcomplete.autocomplete(parser)
        self.args = parser.parse_args()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
