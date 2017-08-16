#!/usr/bin/env python
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK - Needed to activate argcomplete on this script !
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
import subprocess
from bzrlib.plugin import load_plugins
from bzrlib.bzrdir import BzrDir
from bzrlib.errors import NotBranchError
from git import Repo
from git import RemoteProgress
import shutil
from settings_parser.schema import (
    user_conf_schema, oebuild_conf_schema as schema,
    oebuild_conf_schema
)
from settings_parser.user_conf_parser import UserConfParser
from settings_parser.oebuild_conf_parser import (
    OEBuildConfParser, IgnoreSubConf
)
import tarfile
import lxml.etree
import lxml.builder
import psycopg2.extras
import StringIO
from xml.dom import minidom
import dialogs
import json
from params import Params
import static_params
from oebuild_logger import _ex, logging, logger, LOG_PARSER, COLORIZED
import re
from argument_parser import OEArgumentParser
import codecs
from glob import glob

load_plugins()


class Autobuild():

    _arg_parser = None

    user_conf = None
    project = None
    workspace_path = None
    project_path = None
    openerp_path = None
    deps_path = None
    target_path = None
    target_addons_path = None
    deps_cache_file = None
    py_deps_cache_file = None
    virtualenv_path = None
    virtual_python = None
    virtual_pip = None
    src_path = os.path.curdir
    oebuild_conf_parser = None

    deps_addons_path = []
    python_deps = []
    params = None

    def __init__(self, arg_parser):
        self._arg_parser = arg_parser
        args = self._arg_parser.args
        if args.alternate_config and args.alternate_config[:2] == './':
            args.alternate_config = '%s/../%s' % (
                static_params.OE_HOME_PATH,
                args.alternate_config[2:]
            )

        self.params = Params(args.alternate_config)

        self.oebuild_conf_parser = OEBuildConfParser(
            self.params, args.func == 'test' and args.run_test_analyze
        )

        self.user_conf = UserConfParser(self.params).load_user_config_file()
        logger.setLevel(
            getattr(logging, self.user_conf[
                user_conf_schema.OEBUILD_LOG_LEVEL
            ])
        )
        self.workspace_path = (
            self.user_conf[user_conf_schema.WORKSPACE].replace(
                '~', self.params.USER_HOME_PATH
            )
        )

        logger.info('Entering %s mode' % args.func)

        if args.func == "create-module":
            conf = self.oebuild_conf_parser.load_oebuild_config_file(
                self.user_conf[user_conf_schema.CONF_FILES]
            )
            self.create_module(conf, args)

        elif args.func == "init-new":
            overwrite = "no"
            if os.path.exists(static_params.OE_CONFIG_FILE):
                overwrite = dialogs.query_yes_no(
                    "%s file already exists, overwrite it with default one ?" %
                    static_params.OE_CONFIG_FILE, overwrite
                )
            if ((not os.path.exists(static_params.OE_CONFIG_FILE)) or
                    overwrite == "yes"):
                shutil.copyfile(static_params.DEFAULT_OE_CONFIG_FILE,
                                static_params.OE_CONFIG_FILE)

            self.oebuild_conf_parser.create_oebuild_config_file(
                self.user_conf[user_conf_schema.DEFAULT_SERIE]
            )
        elif args.func == 'project-version':
            self.set_version(args.project_version_new_version)
        else:
            conf = self.oebuild_conf_parser.load_oebuild_config_file(
                self.user_conf[user_conf_schema.CONF_FILES]
            )
            self.project = conf[schema.PROJECT]
            self.project_path = '%s/%s' % (self.workspace_path, self.project)
            self.openerp_path = '%s/%s' % (self.project_path, 'openerp')
            self.deps_path = '%s/%s' % (self.project_path, 'deps')
            self.target_path = '%s/%s' % (self.project_path, 'target')
            self.target_addons_path = '%s/%s' % (self.target_path,
                                                 'custom-addons')
            self.deps_cache_file = '%s/%s' % (self.project_path, 'deps.cache')
            self.py_deps_cache_file = '%s/%s' % (self.project_path,
                                                 'python-deps.cache')
            self.virtualenv_path = '%s/%s' % (self.project_path, 'venv')
            self.virtual_python = '%s/%s' % (self.virtualenv_path,
                                             'bin/python')
            self.virtual_pip = '%s/%s' % (self.virtualenv_path, 'bin/pip')
            self.pid_file = '%s/%s' % ('/tmp', '%s.pid' % self.project)

            if args.local:
                try:
                    with open(self.deps_cache_file, 'r') as f:
                        self.deps_addons_path = json.loads(f.read())
                except Exception, e:
                    logger.error(_ex('Impossible to read %s' %
                                     self.deps_cache_file, e))
                    sys.exit(1)
            else:
                self.get_deps(args, conf)
                try:
                    with open(self.deps_cache_file, 'w') as f:
                        f.write(json.dumps(self.deps_addons_path))
                except Exception, e:
                    logger.warning(_ex('Impossible to write %s' %
                                       self.deps_cache_file, e))
            if args.func == "init-eclipse":
                self.init_eclipse(conf)
            elif args.func == "assembly":
                self.assembly(conf, args.project_assembly_include_odoo,
                              args.project_assembly_only_i18n)
            elif args.func == "i18n-export":
                self.export_i18n(conf, args)
            else:
                self.kill_old_openerp(conf)
                self.run_openerp(conf, args)

        logger.info('Terminate %s mode' % args.func)

    def exclude_git(self, filename):
        excludes = ['.git', '.gitignore']
        return any([exclude in filename for exclude in excludes])

    def set_version(self, new_version):
        version_pattern = r"(['\"]version['\"]\s*:\s*['\"])(.*)(['\"])"
        version_result = r"\g<1>%s\g<3>" % new_version
        for root, _, filenames in os.walk('.'):
            for filename in filenames:
                if filename == '__openerp__.py':
                    filepath = os.path.join(root, filename)
                    logger.info(
                        'Change version to %s in %s' % (new_version, filepath)
                    )
                    with open(filepath, 'r') as f:
                        content = f.read()
                    new_content = re.sub(
                        version_pattern, version_result, content
                    )
                    with open(filepath, 'w') as f:
                        f.write(new_content)

    def assembly(self, conf, with_oe=False, only_i18n=False):
        if os.path.exists(self.target_path):
            shutil.rmtree(self.target_path)
        os.mkdir(self.target_path)

        if only_i18n:
            fn = "%s/%s_i18n.tar.gz" % (self.target_path, re.sub(
                '[^0-9a-zA-Z_]+', '_', os.getcwd().split('/')[-1]))
            if os.path.exists(fn):
                os.remove(fn)
            cmd = ("find * -name '*.po' -o -name '*.pot' | "
                   "tar -cf %s -T -" % fn)
            logger.info('Assembly i18n files ...')
            _, _, _ = self.call_command(
                cmd, parse_log=False, log_in=False
            )
            return

        os.mkdir(self.target_addons_path)

        dependency_file = open("%s/DEPENDENCY.txt" % (self.target_path), "w")

        dependency_file.writelines([
            '%s%s\n' % (python_dep['name'],
                        python_dep['specifier']
                        if 'specifier' in python_dep else '')
            for python_dep in self.python_deps
        ])
        dependency_file.close()

        shell_file = open("%s/install_deps.sh" % self.target_path, "w")
        shell_file.write("""#!/bin/sh
if [ "$(/usr/bin/id -u)" != "0" ]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

pip install -r DEPENDENCY.txt \
    && echo "Successfully installed all dependencies" || echo \
    "An error occured. Please review the log above to find what went wrong."
""")
        shell_file.close()

        full_path = self.src_path
        for addon in os.listdir(full_path):
            if os.path.isdir('%s/%s' % (full_path, addon)) and addon[0] != '.':
                shutil.copytree('%s/%s' % (full_path, addon),
                                '%s/%s' % (self.target_addons_path, addon))

        for path in self.deps_addons_path:
            full_path = '%s/%s' % (self.deps_path, path.rstrip('/'))
            for addon in os.listdir(full_path):
                if (os.path.isdir('%s/%s' % (full_path, addon)) and
                        addon[0] != '.' and not
                        os.path.exists('%s/%s' %
                                       (self.target_addons_path, addon))):
                    shutil.copytree('%s/%s' % (full_path, addon),
                                    '%s/%s' % (self.target_addons_path, addon))

        os.chdir(self.target_path)
        tar = tarfile.open('%s.tar.gz' % ('openerp-install'
                                          if with_oe else 'custom-addons'),
                           "w:gz")
        tar.add('custom-addons', exclude=self.exclude_git)

        tar.add('install_deps.sh')
        tar.add('DEPENDENCY.txt')

        if with_oe:
            tar.add(self.openerp_path, arcname="",
                    exclude=self.exclude_git)
        tar.close()

    def export_i18n(self, conf, args):
        addons = conf.get(schema.I18N_ADDONS)
        if not addons:
            logger.info("No i18n addons defined, exited with no action.")
            return

        self.create_or_update_venv(conf, args)

        if not os.path.exists(static_params.OE_CONFIG_FILE):
            logger.error('The OpenERP configuration does not exist : '
                         '%s, use openerp-autobuild init to create it.' %
                         static_params.OE_CONFIG_FILE)
            sys.exit(1)

        if not os.path.exists(self.workspace_path):
            logger.info('Creating nonexistent openerp-autobuild '
                        'workspace : %s', self.workspace_path)
            os.makedirs(self.workspace_path)

        logger.info('Modules to export: %s' % ",".join(addons))

        addons_path = '%s/%s' % (self.openerp_path, 'addons')
        for path in self.deps_addons_path:
            addons_path = "%s,%s" % (addons_path, '%s/%s' %
                                     (self.deps_path, path))
        if glob('*/__openerp__.py'):
            addons_path = "%s%s" % (addons_path, ',.')

        db_conf = self.user_conf[user_conf_schema.DATABASE]
        try:
            conn = psycopg2.connect(
                host=db_conf.get(user_conf_schema.HOST, 'localhost'),
                port=db_conf.get(user_conf_schema.PORT, '5432'),
                user=db_conf.get(user_conf_schema.USER, 'openerp'),
                password=db_conf.get(user_conf_schema.PASSWORD, 'openerp'),
                database='postgres'
            )
        except:
            logger.error("Unable to connect to the database.")
            sys.exit(1)

        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("select * from pg_database where datname = '%s'" %
                    args.run_database)
        db_exists = cur.fetchall() or False
        if db_exists:
            logger.info('Database %s exists' %
                        args.run_database)
        else:
            logger.info('Database %s does not exist' %
                        args.run_database)

        old_isolation_level = conn.isolation_level
        conn.set_isolation_level(0)
        if db_exists:
            logger.info('Drop database %s' % args.run_database)
            cur.execute('drop database "%s"' % args.run_database)
            conn.commit()
        logger.info('Create database %s' % args.run_database)
        cur.execute('create database "%s" owner "%s" '
                    'encoding \'unicode\'' %
                    (args.run_database,
                     db_conf[user_conf_schema.USER]))
        conn.commit()

        conn.set_isolation_level(old_isolation_level)

        cmd = '%s %s/%s' % (self.virtual_python,
                            self.openerp_path, self.get_binary(conf))
        cmd += ' --addons-path=%s' % addons_path
        cmd += ' -d %s' % args.run_database
        cmd += ' --db_user=%s' % db_conf.get(user_conf_schema.USER,
                                             'openerp')
        cmd += ' --db_password=%s' % db_conf.get(user_conf_schema.PASSWORD,
                                                 'openerp')
        cmd += ' --db_host=%s' % db_conf.get(user_conf_schema.HOST,
                                             'localhost')
        cmd += ' --db_port=%s' % db_conf.get(user_conf_schema.PORT,
                                             '5432')
        cmd += ' -i %s' % ','.join(addons)
        cmd += ' --without-demo=all'
        cmd += ' --stop-after-init'
        try:
            logger.info('Start OpenERP ...')
            _, _, _ = self.call_command(
                cmd, parse_log=False,
                register_pid=self.pid_file, log_in=False
            )
        except KeyboardInterrupt:
            logger.info("OpenERP stopped from command line")
            if args.func == "test" and args.run_test_analyze:
                sys.exit(1)

        for addon in addons:
            if not os.path.exists('./%s' % addon):
                logger.warn(("Addon %s does not exists in this project and "
                             "you can only export i18n for your project "
                             "addons. This addon will be skiped.") % addon)
                continue
            addon_folder = './%s/i18n' % addon
            i18n_file = '%s/%s.po' % (addon_folder, addon)
            if not os.path.exists(addon_folder):
                os.makedirs(addon_folder)
            cmd = '%s %s/%s' % (self.virtual_python,
                                self.openerp_path, self.get_binary(conf))
            cmd += ' --addons-path=%s' % addons_path
            cmd += ' -d %s' % args.run_database
            cmd += ' --db_user=%s' % db_conf.get(user_conf_schema.USER,
                                                 'openerp')
            cmd += ' --db_password=%s' % db_conf.get(user_conf_schema.PASSWORD,
                                                     'openerp')
            cmd += ' --db_host=%s' % db_conf.get(user_conf_schema.HOST,
                                                 'localhost')
            cmd += ' --db_port=%s' % db_conf.get(user_conf_schema.PORT,
                                                 '5432')
            cmd += ' --modules=%s' % addon
            cmd += ' --i18n-export=%s' % i18n_file
            try:
                logger.info('Start OpenERP ...')
                _, _, _ = self.call_command(
                    cmd, parse_log=False,
                    register_pid=self.pid_file, log_in=False
                )
            except KeyboardInterrupt:
                logger.info("OpenERP stopped from command line")
                if args.func == "test" and args.run_test_analyze:
                    sys.exit(1)
            if os.path.exists(i18n_file):
                shutil.move(i18n_file, i18n_file.replace('.po', '.pot'))

        if args.run_test_drop_database:
            old_isolation_level = conn.isolation_level
            conn.set_isolation_level(0)
            logger.info('Drop database %s' % args.run_database)
            cur.execute('drop database "%s"' % args.run_database)
            conn.commit()
            conn.set_isolation_level(old_isolation_level)
        conn.close()

        sys.exit(0)

    def create_module(self, conf, args):
        module_path = '%s/%s' % (self.src_path, args.module_create_name)
        if os.path.exists(module_path):
            logger.error("The module already exists")
            sys.exit(1)

        if args.module_create_long_name is None:
            module_long_name = args.module_create_name
        else:
            module_long_name = args.module_create_long_name

        with codecs.open(self.params.HEADER_PY_TPL, 'r', 'utf-8') as f:
            header = f.read()

        header = re.sub(r'\$AUTHOR',
                        self.user_conf[user_conf_schema.MODULE_AUTHOR], header)
        header = re.sub(r'\$WEBSITE',
                        self.user_conf[user_conf_schema.WEBSITE], header)

        with codecs.open(self.params.INIT_PY_TPL, 'r', 'utf-8') as f:
            initpy = f.read()

        initpy = re.sub(r'\$HEADER', header, initpy)

        with codecs.open(self.params.OPENERP_PY_TPL, 'r', 'utf-8') as f:
            openerppy = f.read()

        openerppy = re.sub(r'\$HEADER', header, openerppy)
        openerppy = re.sub(r'\$AUTHOR',
                           self.user_conf[user_conf_schema.MODULE_AUTHOR],
                           openerppy)
        openerppy = re.sub(r'\$WEBSITE',
                           self.user_conf[user_conf_schema.WEBSITE], openerppy)
        openerppy = re.sub(r'\$MODULE_LONG_NAME', module_long_name, openerppy)

        if args.module_create_category is not None:
            openerppy = re.sub(r'\$CATEGORY', args.module_create_category,
                               openerppy)

        os.mkdir(module_path)

        with codecs.open("%s/__init__.py" % module_path, 'w+', 'utf8') as f:
            f.write(initpy)

        with codecs.open("%s/__openerp__.py" % module_path, 'w+', 'utf8') as f:
            f.write(openerppy)

    def init_eclipse(self, conf):
        self.create_eclipse_project(conf)
        self.create_eclipse_pydev_project(conf)

    def write_xml(self, filename, document, standalone=None):
        stream = StringIO.StringIO()
        lxml.etree.ElementTree(document).write(stream, xml_declaration=True,
                                               encoding='UTF-8',
                                               standalone=standalone)
        mdom = minidom.parseString(stream.getvalue())
        header = stream.getvalue().split('\n')[0]
        stream.close()

        f = open(filename, "wb")
        pretty = mdom.toprettyxml(encoding='UTF-8')
        f.write(header + '\n' + '\n'.join(pretty.split('\n')[1:]))
        f.close()

    def create_eclipse_project(self, conf):
        EM = lxml.builder.ElementMaker()

        doc = EM.projectDescription(
            EM.name(conf[schema.PROJECT])
        )
        self.write_xml('.project', doc)

    def create_eclipse_pydev_project(self, conf):
        EM = lxml.builder.ElementMaker()

        ext_path = EM.pydev_pathproperty(
            name='org.python.pydev.PROJECT_EXTERNAL_SOURCE_PATH'
        )
        ext_path.append(EM.path(self.openerp_path))

        doc = EM.pydev_project(
            EM.pydev_property(
                'Default', name='org.python.pydev.PYTHON_PROJECT_INTERPRETER'
            ),
            EM.pydev_property(name='org.python.pydev.PYTHON_PROJECT_VERSION'),

            EM.pydev_pathproperty(
                EM.path(os.path.curdir),
                name='org.python.pydev.PROJECT_SOURCE_PATH'
            ),

            ext_path
        )
        doc.addprevious(lxml.etree.ProcessingInstruction(
            'eclipse-pydev', 'version="1.0"')
        )
        self.write_xml('.pydevproject', doc, standalone=False)

    def create_or_update_venv(self, conf, args):

        if (os.path.exists(self.virtualenv_path) and
                os.path.exists(self.py_deps_cache_file)):
            if args.local:
                return

            is_config_changed = True
            with open(self.py_deps_cache_file, 'r') as f:
                last_run_py_deps = set(['%s%s%s' % (
                    dep[oebuild_conf_schema.NAME],
                    dep.get(oebuild_conf_schema.SPECIFIER, ''),
                    dep.get(oebuild_conf_schema.OPTIONS, '')
                ) for dep in json.load(f)])
                current_py_deps = set(['%s%s%s' % (
                    dep[oebuild_conf_schema.NAME],
                    dep.get(oebuild_conf_schema.SPECIFIER, ''),
                    dep.get(oebuild_conf_schema.OPTIONS, '')
                ) for dep in self.python_deps])
                is_config_changed = (
                    len(last_run_py_deps) != len(current_py_deps) or
                    last_run_py_deps.symmetric_difference(
                        current_py_deps
                    ) != set()
                )

            if not is_config_changed:
                logger.info(
                    "virtualenv %s: No changes in Python dependencies, "
                    "use it as is" % self.virtualenv_path
                )
                return

            logger.info(
                "virtualenv %s: Changes in Python dependencies, "
                "need to rebuild" % self.virtualenv_path
            )
            shutil.rmtree(self.virtualenv_path)
            os.remove(self.py_deps_cache_file)

        elif not os.path.exists(self.py_deps_cache_file):
            if args.local:
                logger.error(
                    "Cannot run in no-update mode without last run Python "
                    "dependencies cache file, try running without "
                    "--no-update argument."
                )
                sys.exit(1)
            if os.path.exists(self.virtualenv_path):
                logger.info(
                    "virtualenv %s : No last run Python dependencies "
                    "cache file, need to rebuild" % self.virtualenv_path
                )
                shutil.rmtree(self.virtualenv_path)

        py_deps_string = " ".join(["'%s%s'" % (
            dep[oebuild_conf_schema.NAME],
            dep.get(oebuild_conf_schema.SPECIFIER, '')
        ) for dep in self.python_deps])
        py_options_string = " ".join([
            dep.get(oebuild_conf_schema.OPTIONS)
            for dep in self.python_deps if dep.get(oebuild_conf_schema.OPTIONS)
        ])
        logger.info(
            "virtualenv %s : Create and install Python dependencies (%s %s)" %
            (self.virtualenv_path, py_deps_string, py_options_string)
        )
        _, out, err = self.call_command(
            "virtualenv -q %s" % self.virtualenv_path,
            log_in=False, log_out=False, log_err=True
        )
        for o in re.split('\n(?=\S)', out):
            if len(o) > 0:
                logger.info("virtualenv %s: %s" % (self.virtualenv_path,
                                                   o.rstrip()))
        errors = False
        for e in re.split('\n(?=\S)', err):
            if len(e) > 0:
                errors = True
                logger.error(u'virtualenv %s: %s' % (
                    self.virtualenv_path, e.rstrip())
                )
        if errors:
            sys.exit(1)

        rc, out, err = self.call_command(
            'LC_ALL=C %s install --egg -q --upgrade %s %s '
            '--log-file .pip-errors.log' %
            (self.virtual_pip, py_options_string, py_deps_string),
            log_in=False, log_out=False, log_err=False
        )
        for o in re.split('\n(?=\S)', out):
            if len(o) > 0:
                logger.info("virtualenv %s: %s" % (self.virtualenv_path,
                                                   o.rstrip()))
        for e in re.split('\n(?=\S)', err):
            if re.search(r'Format RepositoryFormat6\(\) .* is deprecated',
                         e, re.I):
                # If an error is thrown because of using deprecated
                # RepositoryFormat6() format, just warn and continue
                logger.warning(u'virtualenv %s: %s' % (
                    self.virtualenv_path, e.rstrip())
                )
            elif re.search(r'InsecurePlatformWarning:',
                           e, re.I):
                logger.warning(u'virtualenv %s: %s' % (
                    self.virtualenv_path, e.rstrip())
                )
            elif len(e) > 0:
                logger.error(u'virtualenv %s: %s' % (
                    self.virtualenv_path, e.rstrip())
                )
        if rc:
            if args.run_test_analyze and os.path.exists('.pip-errors.log'):
                with open('.pip-errors.log', 'r') as f:
                    pip_log = f.read()
                logger.error("virtualenv %s: Exited with errors:\n%s" % (
                    self.virtualenv_path, pip_log
                ))
            else:
                logger.error("virtualenv %s: Exited with errors" % (
                    self.virtualenv_path
                ))
            sys.exit(1)

        with open(self.py_deps_cache_file, 'w+') as f:
            json.dump(list(self.python_deps), f)

    def kill_old_openerp(self, conf):
        if os.path.exists(self.pid_file) and os.path.isfile(self.pid_file):
            with open(self.pid_file, "r") as f:
                pid = f.read()
                pid = int(pid) if pid != '' else 0
            if pid != 0:
                try:
                    os.kill(pid, 9)
                except:
                    pass
                with open(self.pid_file, "w") as f:
                    f.write("%d" % 0)

    def get_project_modules(self):
        modules = ""
        for module in os.listdir("."):
            if os.path.isdir(module) and not module.startswith('.'):
                modules = "%s,%s" % (module, modules)
        return modules.rstrip(",")

    def run_openerp(self, conf, args):
        self.create_or_update_venv(conf, args)

        for script in conf.get(schema.RUN_SCRIPTS, []):
            rc, out, err = self.call_command(
                script, log_in=False, log_out=False, log_err=False
            )
            logger.info("Run command: %s\n%s\n%s",
                        script, out.rstrip(), err.rstrip())
            if rc:
                logger.error('Command %s failed', script)
                sys.exit(1)

        if not os.path.exists(static_params.OE_CONFIG_FILE):
            logger.error('The OpenERP configuration does not exist : '
                         '%s, use openerp-autobuild init to create it.' %
                         static_params.OE_CONFIG_FILE)
            sys.exit(1)

        if not os.path.exists(self.workspace_path):
            logger.info('Creating nonexistent openerp-autobuild '
                        'workspace : %s', self.workspace_path)
            os.makedirs(self.workspace_path)

        init_modules = None
        update_modules = None
        if args.run_init or args.run_update:
            if not args.run_database:
                logger.error('--database is mandatory if you want to '
                             'install or update modules.')
                sys.exit(1)
            if args.run_init:
                if args.run_init == "project-all":
                    init_modules = self.get_project_modules()
                else:
                    init_modules = args.run_init
            if args.run_update:
                if args.run_update == "project-all":
                    update_modules = self.get_project_modules()
                else:
                    update_modules = args.run_update

        logger.info('Modules to install: %s' % (init_modules or '(None)'))
        logger.info('Modules to update: %s' % (update_modules or '(None)'))

        addons_path = '%s/%s' % (self.openerp_path, 'addons')
        for path in self.deps_addons_path:
            addons_path = "%s,%s" % (addons_path, '%s/%s' %
                                     (self.deps_path, path))
        if glob('*/__openerp__.py'):
            addons_path = "%s%s" % (addons_path, ',.')

        db_conf = self.user_conf[user_conf_schema.DATABASE]
        if args.func == "test":
            try:
                conn = psycopg2.connect(
                    host=db_conf.get(user_conf_schema.HOST, 'localhost'),
                    port=db_conf.get(user_conf_schema.PORT, '5432'),
                    user=db_conf.get(user_conf_schema.USER, 'openerp'),
                    password=db_conf.get(user_conf_schema.PASSWORD, 'openerp'),
                    database='postgres'
                )
            except:
                logger.error("Unable to connect to the database.")
                sys.exit(1)

            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("select * from pg_database where datname = '%s'" %
                        args.run_database)
            db_exists = cur.fetchall() or False
            if db_exists:
                logger.info('Database %s exists' %
                            args.run_database)
            else:
                logger.info('Database %s does not exist' %
                            args.run_database)

            if not db_exists or args.run_test_new_install:
                old_isolation_level = conn.isolation_level
                conn.set_isolation_level(0)

                if db_exists:
                    logger.info('Drop database %s' % args.run_database)
                    cur.execute('drop database "%s"' % args.run_database)
                    conn.commit()

                logger.info('Create database %s' % args.run_database)
                cur.execute('create database "%s" owner "%s" '
                            'encoding \'unicode\'' %
                            (args.run_database,
                             db_conf[user_conf_schema.USER]))
                conn.commit()

                conn.set_isolation_level(old_isolation_level)

            cmd = '%s %s/%s' % (self.virtual_python,
                                self.openerp_path, 'openerp-server')
            cmd += ' --addons-path=%s' % addons_path
            cmd += ' -d %s' % args.run_database
            cmd += ' --db_user=%s' % db_conf.get(user_conf_schema.USER,
                                                 'openerp')
            cmd += ' --db_password=%s' % db_conf.get(user_conf_schema.PASSWORD,
                                                     'openerp')
            cmd += ' --db_host=%s' % db_conf.get(user_conf_schema.HOST,
                                                 'localhost')
            cmd += ' --db_port=%s' % db_conf.get(user_conf_schema.PORT,
                                                 '5432')
            if init_modules:
                cmd += ' -i %s' % init_modules
            if update_modules:
                cmd += ' -u %s' % update_modules
            cmd += ' --log-level=test --test-enable'
            if args.run_test_commit:
                cmd += ' --test-commit'
            if not args.run_test_continue:
                cmd += ' --stop-after-init'
            try:
                logger.info('Start OpenERP ...')
                _, openerp_output, _ = self.call_command(
                    cmd, parse_log=args.run_test_analyze,
                    register_pid=self.pid_file,
                    log_in=False, parse_tests=True
                )
            except KeyboardInterrupt:
                logger.info("OpenERP stopped from command line")
                if args.func == "test" and args.run_test_analyze:
                    sys.exit(1)
        else:
            cmd = '%s %s/%s -c .openerp-dev-default' % (
                self.virtual_python, self.openerp_path, 'openerp-server'
            )
            cmd += ' --addons-path=%s' % addons_path
            cmd += ' --db_user=%s' % db_conf.get(
                user_conf_schema.USER, 'openerp'
            )
            cmd += ' --db_password=%s' % db_conf.get(
                user_conf_schema.PASSWORD, 'openerp'
            )
            cmd += ' --db_host=%s' % db_conf.get(
                user_conf_schema.HOST, 'localhost'
            )
            cmd += ' --db_port=%s' % db_conf.get(
                user_conf_schema.PORT, '5432'
            )
            if args.run_database:
                cmd += ' -d %s' % args.run_database
                if init_modules:
                    cmd += ' -i %s' % init_modules
                if update_modules:
                    cmd += ' -u %s' % update_modules
            if args.run_auto_reload:
                _, openerp_version, _ = self.call_command(
                    '%s/%s --version' % (
                        self.openerp_path, 'openerp-server'
                    ), parse_log=True, log_in=False, log_out=False
                )
                if static_params.OE_VERSION[openerp_version.rstrip()] < '8.0':
                    logger.error("--auto-reload is not available for %s" %
                                 openerp_version)
                    sys.exit(1)
                cmd += ' --auto-reload'

            try:
                logger.info('Start OpenERP ...')
                _, openerp_output, _ = self.call_command(
                    cmd, parse_log=False,
                    register_pid=self.pid_file, log_in=False
                )
            except KeyboardInterrupt:
                logger.info("OpenERP stopped after keyboard interrupt")

        if args.func == "test":
            if args.run_test_drop_database:
                old_isolation_level = conn.isolation_level
                conn.set_isolation_level(0)
                logger.info('Drop database %s' % args.run_database)
                cur.execute('drop database "%s"' % args.run_database)
                conn.commit()
                conn.set_isolation_level(old_isolation_level)

            conn.close()

            if args.run_test_analyze:
                if 'ERROR' in openerp_output:
                    sys.exit(1)
        sys.exit(0)

    def get_deps(self, args, conf):
        oe_conf = conf[schema.OPENERP]
        serie_name = oe_conf[schema.SERIE]

        serie = None
        for tmp_serie in self.user_conf[user_conf_schema.OPENERP]:
            if tmp_serie[user_conf_schema.SERIE] == serie_name:
                serie = tmp_serie
                break
        if not serie:
            logger.error('The serie "%s" does not exists' % (serie_name))
            sys.exit(1)

        try:
            user_source = oe_conf.get(schema.SOURCE, {})
            serie_source = serie[schema.SOURCE]

            url = user_source.get(schema.URL, serie_source[schema.URL])
            git_branch = user_source.get(
                schema.GIT_BRANCH,
                serie_source[schema.GIT_BRANCH]
            )
            git_commit = user_source.get(schema.GIT_COMMIT, serie_source.get(
                schema.GIT_COMMIT, None)
            )
            self.git_checkout(args, url, self.openerp_path,
                              git_branch, git_commit)
        except Exception, e:
            logger.error(
                _ex('Cannot checkout from %s' % url, e),
                exc_info=logger.isEnabledFor(logging.DEBUG)
            )
            sys.exit(1)

        self.add_python_deps(serie[user_conf_schema.PYTHON_DEPENDENCIES])
        self.get_ext_deps(args, self.project, conf[schema.DEPENDENCIES])
        self.add_python_deps(conf[schema.PYTHON_DEPENDENCIES])

    def add_python_deps(self, python_deps):
        existing_names = [idep['name'] for idep in self.python_deps]
        key_name = oebuild_conf_schema.NAME
        key_specifier = oebuild_conf_schema.SPECIFIER
        key_options = oebuild_conf_schema.OPTIONS
        for dep in python_deps:
            if dep['name'] in existing_names:
                existing_dep = [idep for idep in self.python_deps
                                if idep['name'] == dep['name']][0]
                if existing_dep == dep:
                    continue
                if (existing_dep.get(key_specifier, '') and
                        not dep.get(key_specifier, '')):
                    logger.warning(
                        "Dependency %s%s%s does not override %s%s%s: "
                        "version not specified" % (
                            dep[key_name],
                            dep.get(key_specifier, ''),
                            dep.get(key_options, '') and
                            '[%s]' % dep[key_options] or '',
                            existing_dep[key_name],
                            existing_dep.get(key_specifier, ''),
                            existing_dep.get(key_options, '') and
                            '[%s]' % existing_dep[key_options] or '',
                        )
                    )
                    continue
                logger.warning(
                    "Dependency %s%s%s overrides %s%s%s" % (
                        dep[key_name],
                        dep.get(key_specifier, ''),
                        dep.get(key_options, '') and
                        '[%s]' % dep[key_options] or '',
                        existing_dep[key_name],
                        existing_dep.get(key_specifier, ''),
                        existing_dep.get(key_options, '') and
                        '[%s]' % existing_dep[key_options] or '',
                    )
                )
                self.python_deps.remove(existing_dep)
            self.python_deps.append(dep)

    def get_ext_deps(self, args, from_project, deps, deps_mapping=None):
        if not deps_mapping:
            deps_mapping = {}

        for dep in deps:
            if dep[schema.NAME] in deps_mapping.keys():
                src_top = deps_mapping[dep[schema.NAME]][1][schema.SOURCE]
                src_new = dep[schema.SOURCE]
                reason = None
                if src_new[schema.SCM] != src_top[schema.SCM]:
                    reason = 'SCM'
                elif src_new[schema.URL] != src_top[schema.URL]:
                    reason = 'URL'
                elif (src_new[schema.SCM] == schema.SCM_BZR and
                      src_new[schema.BZR_REV] != src_top[schema.BZR_REV]):
                    reason = 'bazaar revision'
                elif (
                    src_new[schema.SCM] == schema.SCM_GIT and
                    src_new[schema.GIT_BRANCH] != src_top[schema.GIT_BRANCH]
                ):
                    reason = 'git branch'
                if reason:
                    logger.warning(
                        "Dependency %s from %s is hidden by a %s dependency "
                        "which use another %s and will ignored" %
                        (dep[schema.NAME], from_project,
                         deps_mapping[dep[schema.NAME]][0], reason)
                    )
                continue

            source = dep[schema.SOURCE]
            deps_mapping[dep[schema.NAME]] = (from_project, dep)
            destination = '%s/%s' % (self.deps_path.rstrip('/'),
                                     dep.get(schema.DESTINATION,
                                             dep[schema.NAME]))

            if source[schema.SCM] == schema.SCM_BZR:
                try:
                    self.bzr_checkout(source[schema.URL], destination,
                                      source.get(schema.BZR_REV, None))
                except Exception, e:
                    logger.error(_ex('Cannot checkout from %s' %
                                     source[schema.URL], e))
                    sys.exit(1)
                try:
                    subconf = self.oebuild_conf_parser.\
                        load_transitive_oebuild_config_file(
                            destination.rstrip('/'),
                            self.user_conf[user_conf_schema.CONF_FILES]
                        )
                    self.add_python_deps(subconf[schema.PYTHON_DEPENDENCIES])
                    self.get_ext_deps(
                        args, subconf[schema.PROJECT],
                        subconf[schema.DEPENDENCIES], deps_mapping
                    )
                except IgnoreSubConf:
                    pass
            elif source[schema.SCM] == schema.SCM_GIT:
                try:
                    self.git_checkout(args,
                                      source[schema.URL], destination,
                                      source.get(schema.GIT_BRANCH, None),
                                      source.get(schema.GIT_COMMIT, None))
                except Exception, e:
                    logger.error(_ex('Cannot checkout from %s' %
                                     source[schema.URL], e))
                    sys.exit(1)
                try:
                    subconf = self.oebuild_conf_parser.\
                        load_transitive_oebuild_config_file(
                            destination.rstrip('/'),
                            self.user_conf[user_conf_schema.CONF_FILES]
                        )
                    self.add_python_deps(subconf[schema.PYTHON_DEPENDENCIES])
                    self.get_ext_deps(args,
                                      subconf[schema.PROJECT],
                                      subconf[schema.DEPENDENCIES],
                                      deps_mapping)
                except IgnoreSubConf:
                    pass
            elif source[schema.SCM] == schema.SCM_LOCAL:
                try:
                    self.local_copy(source[schema.URL], destination)
                except Exception, e:
                    logger.error(_ex('Cannot copy from %s' %
                                     source[schema.URL], e))
                    sys.exit(1)
                try:
                    subconf = self.oebuild_conf_parser.\
                        load_transitive_oebuild_config_file(
                            destination.rstrip('/'),
                            self.user_conf[user_conf_schema.CONF_FILES]
                        )
                    self.add_python_deps(subconf[schema.PYTHON_DEPENDENCIES])
                    self.get_ext_deps(args,
                                      subconf[schema.PROJECT],
                                      subconf[schema.DEPENDENCIES],
                                      deps_mapping)
                except IgnoreSubConf:
                    pass
            addons_path = dep.get(schema.DESTINATION, dep[schema.NAME])
            if dep.get(schema.ADDONS_PATH, False):
                addons_path = '%s/%s' % (addons_path,
                                         dep[schema.ADDONS_PATH].rstrip('/'))
            self.deps_addons_path.append(addons_path)

    def bzr_checkout(self, source, destination, revno=None):
        accelerator_tree, remote = BzrDir.open_tree_or_branch(source)

        if revno:
            revno = int(revno)
        else:
            revno = remote.revno()

        if os.path.exists(destination) and os.path.isdir(destination):
            try:
                local_tree, local = BzrDir.open_tree_or_branch(destination)
                local_revno = local.revision_id_to_revno(
                    local_tree.last_revision()
                )
                if revno == local_revno:
                    logger.info('%s : Up-to-date from %s (revno : %s)' %
                                (destination, source, local_revno))
                    return
                else:
                    shutil.rmtree(destination)
            except NotBranchError:
                shutil.rmtree(destination)

        if not os.path.exists(destination):
            os.makedirs(destination)

        logger.info('%s : Checkout from %s (revno : %s)...' % (
            destination, source, revno)
        )
        remote.create_checkout(destination, remote.get_rev_id(revno),
                               True, accelerator_tree)

    def is_git_uptodate(self, source, destination, branch, commit):
        try:
            local = Repo(destination)
            origin = local.remotes.origin
        except:
            logger.warning('%s : Invalid git repository!' % (
                destination
            ))
            return False

        if origin.url != source:
            logger.info('%s : Source URL has changed', destination)
            return False

        if commit:
            if local.head.commit.hexsha == commit:
                logger.info('%s : Commit already up-to-date', destination)
                return True

        logger.info('%s : Checkout %s %s...' % (
            destination, commit and 'commit' or 'branch',
            commit or branch or 'master'
        ))

        try:
            local.git.reset('--hard')
            local.git.clean('-xdf')  # Remove untracked files, including .pyc
            origin.pull()
        except:
            logger.warning('%s : Checkout %s %s failed!' % (
                destination, commit and 'commit' or 'branch',
                commit or branch or 'master'
            ))
            return False

        local.git.checkout(commit or branch or 'master')
        return True

    def git_checkout(self, args, source, destination,
                     branch=None, commit=None):
        if os.path.exists(destination):
            if self.is_git_uptodate(source, destination, branch, commit):
                return
            shutil.rmtree(destination)

        os.makedirs(destination)

        logger.info('%s : Clone from %s...' % (destination, source))
        with OEBuildRemoteProgress(args.func == 'test' and
                                   args.run_test_analyze) as progress:
            local = Repo.clone_from(source, destination,
                                    progress=progress)

        logger.info('%s : Checkout %s %s...' % (
            destination, commit and 'commit' or 'branch',
            commit or branch or 'master'
        ))
        local.git.checkout(commit or branch or 'master')

    def local_copy(self, source, destination):
        logger.info('%s : Copy from %s...' % (destination, source))
        shutil.rmtree(destination)
        os.mkdir(destination)
        for module in [m for m in os.listdir(source) if (
            os.path.isdir(os.path.join(source, m)) and m[:1] != '.'
        )]:
            shutil.copytree(os.path.join(source, module),
                            os.path.join(destination, module))
        for module in [m for m in os.listdir(source) if (
            os.path.isfile(os.path.join(source, m)) and m[:7] == 'oebuild'
        ) and m[-5:] == '.conf']:
            shutil.copy2(os.path.join(source, module),
                         os.path.join(destination, module))

    def call_command(self, command, log_in=True, log_out=True, log_err=True,
                     parse_log=True, register_pid=None, parse_tests=False):
        if log_in:
            logger.info(command)
        process = subprocess.Popen(command,
                                   shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE if parse_log
                                   else subprocess.STDOUT)

        if register_pid is not None:
            with open(register_pid, "w") as f:
                f.write("%d" % (process.pid + 1))
                # pid + 1 : shell=True -> pid of spawned shell

        if parse_log:
            out, err = process.communicate()
            rc = process.returncode
            if log_err and err:
                logger.error(err)
            if log_out and out:
                logger.info(out)
            return rc, out, err
        else:
            test_ok = True
            while True:
                line = process.stdout.readline()
                if line and len(line.rstrip()) > 0:
                    match = LOG_PARSER.search(line.rstrip())
                    if match and len(match.groups()) == 3:
                        print '%s %s %s' % (match.group(1),
                                            COLORIZED(match.group(2),
                                                      match.group(2)),
                                            match.group(3))
                        if parse_tests and match.group(2) == 'ERROR':
                            test_ok = False
                    else:
                        print line.rstrip()
                elif not line:
                    break
            if parse_tests:
                print '\n' + (COLORIZED('DEBUG', 'OpenERP Test result: ') +
                              (COLORIZED('INFO', 'SUCCESS') if test_ok
                               else COLORIZED('ERROR', 'FAILED')))
            return None, None, None


class OEBuildRemoteProgress(RemoteProgress):

    _re_parse = re.compile(r'(.*):\s*[0-9]*.*')

    def __init__(self, analyze=False):
        super(OEBuildRemoteProgress, self).__init__()
        self._analyze = analyze

    def _parse_progress_line(self, line):
        if (not self._analyze) and self._line_up:
            sys.stdout.write("\033[F")
        else:
            self._line_up = True

        line_out = ('> %s' % line).encode('utf-8')
        line_out_len = len(line_out)
        if line_out_len < self._last_line_len:
            line_out += ' ' * (self._last_line_len - line_out_len)
        print line_out
        self._last_line_len = line_out_len

        sys.stdout.flush()

    def __enter__(self):
        self._msg_type = None
        self._line_up = False
        self._last_line_len = 0
        return self

    def __exit__(self, *_):
        if (not self._analyze) and self._line_up:
            sys.stdout.write("\033[F")


if __name__ == "__main__":
    arg_parser = OEArgumentParser()
    Autobuild(arg_parser)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
