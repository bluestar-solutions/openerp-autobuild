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
__builtins__.OE_HOME_PATH = os.path.dirname(os.path.realpath(__file__))

import sys
import subprocess
import tempfile
from argparse import ArgumentParser, RawDescriptionHelpFormatter
import textwrap
from bzrlib.plugin import load_plugins
from bzrlib.bzrdir import BzrDir
from bzrlib.errors import ConnectionError
from bzrlib.errors import NotBranchError
from git import Repo
from git.exc import GitCommandError
from git.exc import InvalidGitRepositoryError
import shutil
import oebuild_logger
from settings_parser import oebuild_conf_schema, oebuild_conf_parser
from settings_parser import user_conf_schema, user_conf_parser
import tarfile
import lxml.etree
import lxml.builder
import psycopg2.extras
import StringIO
from xml.dom import minidom

load_plugins()

PID_FILE = '%s/%s' % (tempfile.gettempdir(), 'openerp-pid')

OE_CONFIG_FILE = '%s/.openerp-dev-default' % os.getcwd()
if not os.path.exists(OE_CONFIG_FILE):
    shutil.copyfile("%s/conf/default_openerp_config" % OE_HOME_PATH, OE_CONFIG_FILE) #@UndefinedVariable
    
user_conf = user_conf_parser.load_user_config_file()
WORKSPACE = user_conf[user_conf_schema.WORKSPACE].replace('~', user_conf_parser.USER_HOME_PATH)

if not os.path.exists(WORKSPACE):
    os.makedirs(WORKSPACE)

openerp_path = lambda project: '%s/%s/%s' % (WORKSPACE, project, 'openerp')
deps_path = lambda project: '%s/%s/%s' % (WORKSPACE, project, 'deps')
target_path = lambda project: '%s/%s/%s' % (WORKSPACE, project, 'target')
target_addons_path = lambda project: '%s/%s' % (target_path(project), 'custom-addons')
src_path = os.path.curdir

logger = oebuild_logger.getLogger()
deps_addons_path = []
    
def main():
    shared_parser = ArgumentParser(add_help=False)
    shared_parser.add_argument("-m", "--modules", dest="modules", default="def-all", help="Modules to use. If omitted, all modules will be used.")
    shared_parser.add_argument("-p", "--tcp-port", dest="tcp_port", type=int, default="8069", help="TCP server port (default:8069).")

    parser = ArgumentParser(formatter_class=RawDescriptionHelpFormatter,
                            description=textwrap.dedent('''\
                                OpenERP Autobuild version %s
                                --------------------------%s
                                A developer tool for OpenERP with many features:
                                    
                                    * Run OpenERP locally with options and user defined settings.
                                    * Run OpenERP with automated tests for your modules.
                                    * Initialize a new OpenERP project with autobuild settings.
                                    * Initailize configuration files for Eclipse (with PyDev plugin).
                                    * Manage your module dependencies.
                                    * Assembly your module with the desired OpenERP version and all dependencies.
                                ''' % (oebuild_conf_parser.VERSION, '-' * len(oebuild_conf_parser.VERSION))),
                            epilog=textwrap.dedent('''\
                                goal help:
                                    %(prog)s GOAL -h
                            
                                Copyright (C) 2012-2013 Bluestar Solutions Sàrl (<http://www.blues2.ch>).
                                Released under GNU AGPLv3.
                                '''))
    subparsers = parser.add_subparsers(metavar="GOAL")
    
    parser_run = subparsers.add_parser('run', help="Run openERP server normally (default)", parents=[shared_parser])
    parser_run.set_defaults(func="run")
    
    parser_test = subparsers.add_parser('test', help="Run openERP server, perform tests, stop the server and display tests results", parents=[shared_parser])
    parser_test.add_argument("--test-commit", action="store_true", dest="commit", help="Commit test results in DB.")
    parser_test.add_argument("--db-name", dest="db_name", help="Database name for tests.", default='autobuild_%s' % os.getcwd().split('/')[-1])
    parser_test.add_argument("--force-install", action="store_true", dest="install", help="Force new install.")
    parser_test.add_argument("--analyze", action="store_true", dest="analyze", help="Analyze log and stop OpenERP, for continuous integration.")
    parser_test.set_defaults(func="test")
    
    parser_debug = subparsers.add_parser('debug', help="Run openERP server with full debug messages", parents=[shared_parser])
    parser_debug.set_defaults(func="debug")
    
    parser_assembly = subparsers.add_parser('assembly', help="Prepare all files to deploy in target folder", parents=[shared_parser])
    parser_assembly.add_argument("--with-oe", action="store_true", dest="with_oe", help="Include OpenERP files")
    parser_assembly.set_defaults(func="assembly")
    
    parser_eclipse_init = subparsers.add_parser('init-eclipse', help="Initialize an Eclipse Pyedv project", parents=[shared_parser])
    parser_eclipse_init.set_defaults(func="init-eclipse")
    
    parser_init_new = subparsers.add_parser('init', help="Initialize an empty OpenERP project")
    parser_init_new.set_defaults(func="init-new")
    
    args = parser.parse_args()
            
    logger.info('Entering %s mode' % args.func)
    
    if args.func == "init-new":
        oebuild_conf_parser.create_oebuild_config_file(user_conf[user_conf_schema.DEFAULT_SERIE])
    else:
        conf = oebuild_conf_parser.load_oebuild_config_file(user_conf[user_conf_schema.CONF_FILES])
        get_deps(conf)
    
        if args.func == "init-eclipse":
            init_eclipse(conf)
        elif args.func == "assembly":
            assembly(conf, args.with_oe)
        else:  
            kill_old_openerp()
            run_openerp(conf, args)
        
    logger.info('Terminate %s mode' % args.func)
    
def assembly(conf, with_oe=False):
    project = conf[oebuild_conf_schema.PROJECT]
    if os.path.exists(target_path(project)):
        shutil.rmtree(target_path(project))
    
    full_path = src_path
    for addon in os.listdir(full_path):
        if os.path.isdir('%s/%s' % (full_path, addon)) and addon[0] != '.':
            shutil.copytree('%s/%s' % (full_path, addon), '%s/%s' % (target_addons_path(project), addon))
                    
    for path in deps_addons_path:
        full_path = '%s/%s' % (deps_path(project), path.rstrip('/'))
        for addon in os.listdir(full_path):
            if os.path.isdir('%s/%s' % (full_path, addon)) and addon[0] != '.' and not os.path.exists('%s/%s' % (target_addons_path(project), addon)):
                shutil.copytree('%s/%s' % (full_path, addon), '%s/%s' % (target_addons_path(project), addon))
    
    os.chdir(target_path(project))
    tar = tarfile.open('%s.tar.gz' % ('openerp-install' if with_oe else 'custom-addons'), "w:gz")
    tar.add('custom-addons')
    
    if with_oe:
        for oe in ['server','web','addons']:
            tar.add('%s/%s' % (openerp_path(project), oe), arcname=oe)
            
    tar.close()
    
def init_eclipse(conf):
    create_eclipse_project(conf)
    create_eclipse_pydev_project(conf)
    
def write_xml(filename, document, standalone=None):
    stream = StringIO.StringIO()
    lxml.etree.ElementTree(document).write(stream, xml_declaration=True, encoding='UTF-8', standalone=standalone)
    mdom = minidom.parseString(stream.getvalue())
    header = stream.getvalue().split('\n')[0]
    stream.close()

    f = open(filename, "wb")
    pretty = mdom.toprettyxml(encoding='UTF-8')
    f.write(header + '\n' + '\n'.join(pretty.split('\n')[1:]))
    f.close()
        
def create_eclipse_project(conf):
    EM = lxml.builder.ElementMaker()
    
    doc = EM.projectDescription (
        EM.name(conf[oebuild_conf_schema.PROJECT])
    )
    write_xml('.project', doc)
    
def create_eclipse_pydev_project(conf):
    project = conf[oebuild_conf_schema.PROJECT]
    EM = lxml.builder.ElementMaker()
    
    ext_path = EM.pydev_pathproperty(name='org.python.pydev.PROJECT_EXTERNAL_SOURCE_PATH')
    ext_path.append(EM.path(openerp_path(project) + '/server'))
    
    doc = EM.pydev_project (
        EM.pydev_property('Default', name='org.python.pydev.PYTHON_PROJECT_INTERPRETER'),
        EM.pydev_property(name='org.python.pydev.PYTHON_PROJECT_VERSION'),
        
        EM.pydev_pathproperty(
            EM.path(os.path.curdir),
            name='org.python.pydev.PROJECT_SOURCE_PATH'
        ),
        
        ext_path
    )
    doc.addprevious(lxml.etree.ProcessingInstruction('eclipse-pydev', 'version="1.0"'))
    write_xml('.pydevproject', doc, standalone=False)

       
def kill_old_openerp():
    if os.path.exists(PID_FILE) and os.path.isfile(PID_FILE):
        with open(PID_FILE,"r") as f:
            pid = f.read()
            pid = int(pid) if pid != '' else 0
        if pid != 0:
            try:
                os.kill(pid,9)
            except:
                pass
            with open(PID_FILE,"w") as f:
                f.write("%d" % 0)

def run_openerp(conf, args):
    project = conf[oebuild_conf_schema.PROJECT]
        
    if args.modules == "def-all":
        modules = ""
        for module in os.listdir("."):
            if os.path.isdir(module) and not module.startswith('.'):
                modules = "%s,%s" % (module,modules)
        modules = modules.rstrip(",")
    else:
        modules = args.modules
        
    addons_path = '%s/%s' % (openerp_path(project), 'addons')
    for path in deps_addons_path:
        addons_path = "%s,%s" % (addons_path, '%s/%s' % (deps_path(project), path))
    addons_path = "%s%s,%s" % (addons_path, ',.' if modules != '' else '', '%s/%s' % (openerp_path(project), 'web/addons'))
    
    db_conf = user_conf[user_conf_schema.DATABASE]
    if args.func == "test":
        update_or_install = "u"
        try:
            conn = psycopg2.connect(host = db_conf.get(user_conf_schema.HOST, 'localhost'),
                                    port = db_conf.get(user_conf_schema.PORT, '5432'),
                                    user = db_conf[user_conf_schema.USER],
                                    password = db_conf[user_conf_schema.PASSWORD],
                                    database = 'postgres')
        except:
            logger.error("Unable to connect to the database.")
            sys.exit(1)

        cur = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)
        cur.execute("select * from pg_database where datname = '%s'" % args.db_name)
        db_exists = cur.fetchall() or False
        if db_exists:
            logger.info('Database %s exists' % args.db_name)
        else:
            logger.info('Database %s does not exists' % args.db_name)
        
        if not db_exists or args.install:
            old_isolation_level = conn.isolation_level
            conn.set_isolation_level(0)
            
            if db_exists:
                cur.execute('drop database "%s"' % args.db_name)
                conn.commit()
                
            cur.execute('create database "%s" owner "%s" encoding \'unicode\'' % (args.db_name, db_conf[user_conf_schema.USER]))
            conn.commit()

            conn.set_isolation_level(old_isolation_level)  
            update_or_install = "i"

        cmd = '%s/%s' % (openerp_path(project), 'server/openerp-server')
        cmd += ' --addons-path=%s' % addons_path
        cmd += ' -d %s' % args.db_name
        cmd += ' --db_user=%s' % db_conf[user_conf_schema.USER]
        cmd += ' --db_password=%s' % db_conf[user_conf_schema.PASSWORD]
        cmd += ' --db_host=%s' % db_conf.get(user_conf_schema.HOST, 'localhost')
        cmd += ' --db_port=%s' % db_conf.get(user_conf_schema.PORT, '5432')
        cmd += ' -%s %s' % (update_or_install, modules)
        cmd += ' --log-level=test --test-enable'
        if args.commit:
            cmd += ' --test-commit'
        if args.analyze:
            cmd += ' --stop-after-init'
        openerp_output, _ = call_command(cmd, parse_log=args.analyze, register_pid=PID_FILE
        )
    else:
        cmd = '%s/%s -c .openerp-dev-default' % (openerp_path(project), 'server/openerp-server')
        cmd += ' --addons-path=%s' % addons_path
        cmd += ' --db_user=%s' % db_conf[user_conf_schema.USER]
        cmd += ' --db_password=%s' % db_conf[user_conf_schema.PASSWORD]
        cmd += ' --db_host=%s' % db_conf.get(user_conf_schema.HOST, 'localhost')
        cmd += ' --db_port=%s' % db_conf.get(user_conf_schema.PORT, '5432')
        cmd += ' -u %s' % modules
        cmd += ' --log-level=%s' % ('info' if args.func == "run" else 'debug')
        cmd += ' --log-handler=%s' % (':INFO' if args.func == "run" else ':DEBUG')
        cmd += ' --xmlrpc-port=%d' % args.tcp_port
        openerp_output, _ = call_command(cmd, parse_log=False, register_pid=PID_FILE)

    if args.func == "test" and args.analyze:
        if 'ERROR' in openerp_output:
            sys.exit(1)
    sys.exit(0)

def get_deps(conf):
    project = conf[oebuild_conf_schema.PROJECT]
    oe_conf = conf[oebuild_conf_schema.OPENERP]
    serie_name = oe_conf[oebuild_conf_schema.SERIE]
    
    serie = None
    for tmp_serie in user_conf[user_conf_schema.OPENERP]:
        if tmp_serie[user_conf_schema.SERIE] == serie_name:
            serie = tmp_serie
            break
    if not serie :
        logger.error('The serie "%s" cannot be find in your configuration file : %s' % 
                     (serie_name, user_conf_parser.USER_OEBUILD_CONFIG_FILE))
        sys.exit(1)
    
    for sp in ('server', 'addons', 'web'):
        try:
            url = oe_conf.get(sp, {}).get(oebuild_conf_schema.URL, serie[sp])
            bzr_rev = oe_conf.get(sp, {}).get(oebuild_conf_schema.BZR_REV, None)
            bzr_checkout(url, '%s/%s' % (openerp_path(project), sp), bzr_rev)
        except ConnectionError, error:
            logger.error('%s: %s' % ('%s/%s' % (openerp_path(project), sp), error))
    
    get_ext_deps(project, project, conf[oebuild_conf_schema.DEPENDENCIES])
    
def get_ext_deps(root_project, from_project, deps, deps_mapping=None):
    if not deps_mapping:
        deps_mapping = {}
    
    for dep in deps:
        if dep[oebuild_conf_schema.NAME] in deps_mapping.keys() :
            src_top = deps_mapping[dep[oebuild_conf_schema.NAME]][1][oebuild_conf_schema.SOURCE]
            src_new = dep[oebuild_conf_schema.SOURCE]
            reason = None
            if src_new[oebuild_conf_schema.SCM] != src_top[oebuild_conf_schema.SCM]:
                reason = 'SCM'
            elif src_new[oebuild_conf_schema.URL] != src_top[oebuild_conf_schema.URL]:
                reason = 'URL'
            elif src_new[oebuild_conf_schema.SCM] == oebuild_conf_schema.SCM_BZR and src_new[oebuild_conf_schema.BZR_REV] != src_top[oebuild_conf_schema.BZR_REV]:
                reason = 'bazaar revision'
            elif src_new[oebuild_conf_schema.SCM] == oebuild_conf_schema.SCM_GIT and src_new[oebuild_conf_schema.GIT_BRANCH] != src_top[oebuild_conf_schema.GIT_BRANCH]:
                reason = 'git branch' 
            if reason: 
                logger.warning(("Dependency %s from %s is hidden by a %s dependency which use another %s and will ignored" +
                                "") % (dep[oebuild_conf_schema.NAME], from_project, 
                                       deps_mapping[dep[oebuild_conf_schema.NAME]][0], reason))
            continue
        
        deps_mapping[dep[oebuild_conf_schema.NAME]] = (from_project, dep)
        destination = '%s/%s' % (deps_path(root_project).rstrip('/'), dep.get(oebuild_conf_schema.DESTINATION, dep[oebuild_conf_schema.NAME]))
        source = dep[oebuild_conf_schema.SOURCE]
        if source[oebuild_conf_schema.SCM] == oebuild_conf_schema.SCM_BZR:
            try:
                bzr_checkout(source[oebuild_conf_schema.URL], destination, source.get(oebuild_conf_schema.BZR_REV, None))
            except ConnectionError, error:
                logger.error('%s: %s' % (destination, error))
            try:
                subconf = oebuild_conf_parser.load_subconfig_file_list(destination.rstrip('/'), user_conf[user_conf_schema.CONF_FILES])
                get_ext_deps(root_project, subconf[oebuild_conf_schema.PROJECT], subconf[oebuild_conf_schema.DEPENDENCIES], deps_mapping)
            except oebuild_conf_parser.IgnoreSubConf:
                pass
        elif source[oebuild_conf_schema.SCM] == oebuild_conf_schema.SCM_GIT:
            try:
                git_checkout(source[oebuild_conf_schema.URL], destination, source.get(oebuild_conf_schema.GIT_BRANCH, None))
            except AssertionError, error:
                logger.error('%s: %s' % (destination, error))
            except GitCommandError, error:
                logger.critical('%s: %s' % (destination, error))
                sys.exit(1)
            try:
                subconf = oebuild_conf_parser.load_subconfig_file_list(destination.rstrip('/'), user_conf[user_conf_schema.CONF_FILES])
                get_ext_deps(root_project, subconf[oebuild_conf_schema.PROJECT], subconf[oebuild_conf_schema.DEPENDENCIES], deps_mapping)
            except oebuild_conf_parser.IgnoreSubConf:
                pass
        addons_path = dep.get(oebuild_conf_schema.DESTINATION, dep[oebuild_conf_schema.NAME])
        if dep.get(oebuild_conf_schema.ADDONS_PATH, False):
            addons_path = '%s/%s' % (addons_path, dep[oebuild_conf_schema.ADDONS_PATH].rstrip('/'))
        deps_addons_path.append(addons_path)

def bzr_checkout(source, destination, revno=None):
    accelerator_tree, remote = BzrDir.open_tree_or_branch(source)
    if revno:
        revno = int(revno)
    else:
        revno = remote.revno()

    if os.path.exists(destination) and os.path.isdir(destination):
        try:
            local_tree, local = BzrDir.open_tree_or_branch(destination)
            local_revno = local.revision_id_to_revno(local_tree.last_revision())
            if revno == local_revno:
                logger.info('%s : Up-to-date from %s (revno : %s)' % (destination, source, local_revno))
                return
            else:
                shutil.rmtree(destination)
        except NotBranchError:
            shutil.rmtree(destination)

    if not os.path.exists(destination):
        os.makedirs(destination)

    logger.info('%s : Checkout from %s (revno : %s)...' % (destination, source, revno))
    remote.create_checkout(destination, remote.get_rev_id(revno), True, accelerator_tree)

def git_checkout(source, destination, branch=None):
    if os.path.exists(destination):
        try:
            local = Repo(destination)
            logger.info('%s : Pull from %s...' % (destination, source))
            local.remotes.origin.pull()
            if branch:
                logger.info('%s : Checkout branch %s...' % (destination, branch))
                local.git.checkout(branch)
            return
        except InvalidGitRepositoryError:
            shutil.rmtree(destination)
         
    os.makedirs(destination)  
    logger.info('%s : Clone from %s...' % (destination, source))
    local = Repo.clone_from(source, destination)
    if branch:
        logger.info('%s : Checkout branch %s...' % (destination, branch))
        local.git.checkout(branch)

def call_command(command, log_in=True, log_out=True, log_err=True, parse_log=True, register_pid=None):
    if log_in : 
        logger.info(command)
    process = subprocess.Popen(command,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE if parse_log else subprocess.STDOUT)
    
    if register_pid is not None:
        with open(register_pid,"w") as f:
            f.write("%d" % (process.pid+1)) # pid + 1 : shell=True -> pid of spawned shell
    
    if parse_log:
        out, err = process.communicate()
        if log_err and err:
            logger.error(err)
        if log_out and out:
            logger.info(out)
        return (out, err)
    else:
        while True:
            line = process.stdout.readline()
            if line != '':
                print(line.rstrip())
            else:
                break
        return (None, None)

if __name__ == "__main__":
    main()