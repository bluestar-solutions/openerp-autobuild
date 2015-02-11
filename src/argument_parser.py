#!/usr/bin/env python
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
from argparse import ArgumentParser, RawDescriptionHelpFormatter
import argcomplete
from bzrlib.plugin import load_plugins
import static_params

load_plugins()


class OEArgumentParser():

    args = None

    def __init__(self):

        parser = ArgumentParser(
            formatter_class=RawDescriptionHelpFormatter,
            description='''\
OpenERP Autobuild version %s
--------------------------%s
A developer tool for OpenERP with many features:

    * Run OpenERP locally with options and user defined settings.
    * Run OpenERP with automated tests for your modules.
    * Initialize a new OpenERP project with autobuild settings.
    * Initailize configuration files for Eclipse (with PyDev plugin).
    * Manage your module dependencies.
    * Assembly your module with the desired OpenERP version
      and all dependencies.
            ''' % (static_params.VERSION, '-' * len(static_params.VERSION)),
            epilog='''\
goal help:
    %(prog)s GOAL -h

Copyright (C) 2012-2013 Bluestar Solutions Sàrl (<http://www.blues2.ch>).
Released under GNU AGPLv3.
            ''',
            version='''\
OpenERP Autobuild %s

Copyright (C) 2012-2013 Bluestar Solutions Sàrl (<http://www.blues2.ch>).
Released under GNU AGPLv3.
            ''' % static_params.VERSION)

        shared_parser = ArgumentParser(add_help=False)
        shared_parser.add_argument(
            "-m", "--modules", dest="modules", default="def-all",
            help="Modules to use. If omitted, all modules will be used."
        )
        shared_parser.add_argument(
            "-p", "--tcp-port", dest="tcp_port", type=int, default="-1",
            help="TCP server port (default:8069)."
        )
        shared_parser.add_argument(
            "-n", "--netrpc-port", dest="netrpc_port", type=int, default="-1",
            help="NetRPC server port (default:8070). "
            "Warning: not compatible with serie 8.0"
        )
        shared_parser.add_argument(
            "--no-update", action="store_true", dest="no_update",
            help="Bypass updates and try to launch with last parameters."
        )
        shared_parser.add_argument(
            "--home-config", dest="home_config", default="",
            help="Bypass default config with a specific configuration"
        )
        shared_parser.add_argument(
            "--etc-config", dest="etc_config", default="",
            help="Bypass default config with a specific configuration"
        )

        subparsers = parser.add_subparsers(metavar="GOAL")

        parser_run = subparsers.add_parser(
            'run', help="Run openERP server normally (default)",
            parents=[shared_parser]
        )
        parser_run.set_defaults(func="run")

        parser_debug = subparsers.add_parser(
            'debug', help="Run openERP server with full debug messages",
            parents=[shared_parser]
        )
        parser_debug.set_defaults(func="debug")

        parser_test = subparsers.add_parser(
            'test', help="Run openERP server, perform tests, "
            "stop the server and display tests results",
            parents=[shared_parser]
        )
        parser_test.add_argument(
            "--test-commit", action="store_true", dest="commit",
            help="Commit test results in DB."
        )
        parser_test.add_argument(
            "--db-name", dest="db_name", help="Database name for tests.",
            default='autobuild_%s' % os.getcwd().split('/')[-1]
        )
        parser_test.add_argument(
            "--force-install", action="store_true", dest="install",
            help="Force new install."
        )
        parser_test.add_argument(
            "--analyze", action="store_true", dest="analyze",
            help="Analyze log and stop OpenERP, for continuous integration."
        )
        parser_test.add_argument(
            "--stop-after-init", action="store_true", dest="stopafterinit",
            help="Force OpenERP server to stop when tests are done."
        )
        parser_test.set_defaults(func="test")

        parser_init_new = subparsers.add_parser(
            'project-init', help="Initialize an empty OpenERP project",
            parents=[shared_parser]
        )
        parser_init_new.set_defaults(func="init-new")

        parser_assembly = subparsers.add_parser(
            'project-assembly',
            help="Prepare all files to deploy in target folder",
            parents=[shared_parser]
        )
        parser_assembly.add_argument(
            "--with-oe", action="store_true", dest="with_oe",
            help="Include OpenERP files"
        )
        parser_assembly.set_defaults(func="assembly")

        parser_create_module = subparsers.add_parser(
            'module-create', help="Create a new module"
        )
        parser_create_module.add_argument(
            'module_name', help="module base name"
        )
        parser_create_module.add_argument(
            '-mn', '--module_long_name', dest="module_long_name",
            required=False, help="long module name"
        )
        parser_create_module.add_argument(
            '-c', '--category', dest="category", required=False,
            help="The module category"
        )
        parser_create_module.set_defaults(func="create-module")

        parser_eclipse_init = subparsers.add_parser(
            'eclipse-init', help="Initialize an Eclipse Pyedv project",
            parents=[shared_parser]
        )
        parser_eclipse_init.set_defaults(func="init-eclipse")

        argcomplete.autocomplete(parser)
        self.args = parser.parse_args()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
