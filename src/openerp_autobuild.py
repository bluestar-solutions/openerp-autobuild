#!/usr/bin/env python
# coding: utf-8

import sys
import re
import subprocess
from argparse import ArgumentParser
import json 
from bzrlib.plugin import load_plugins
from bzrlib.bzrdir import BzrDir
from bzrlib.errors import ConnectionError
import os.path
from git import Repo
from git.exc import GitCommandError
import tempfile
import validictory
import shutil
import oebuild_logger
import oebuild_conf_schema as c_s
import tarfile
import lxml.etree
import lxml.builder

load_plugins()

OE_HOME_PATH = os.path.dirname(os.path.realpath(__file__))
USER_HOME_PATH = os.path.expanduser("~")
CONFIG_PATH = '%s/.config/openerp-autobuild' % USER_HOME_PATH
CONFIG_FILE_PATH = '%s/openerp-autobuild' % CONFIG_PATH
CONFIG_FILE = '%s/oebuild_config.py' % CONFIG_FILE_PATH
OE_CONFIG_FILE = '%s/.openerp-dev-default' % os.getcwd()

if not os.path.exists(CONFIG_PATH):
    os.makedirs(CONFIG_PATH)
if not os.path.exists(CONFIG_FILE_PATH):
    os.makedirs(CONFIG_FILE_PATH)
if not os.path.exists(CONFIG_FILE):
    shutil.copyfile("%s/oebuild_config.default" % OE_HOME_PATH, CONFIG_FILE)
    with open(CONFIG_FILE,'a+b') as f:
        contents = f.readlines()
        f.truncate(0)
        for l in contents:
            f.write(re.sub(r'{USERNAME}', os.path.expanduser("~").split('/')[-1], l))
if not os.path.exists(OE_CONFIG_FILE):
    shutil.copyfile("%s/oe_config.default" % OE_HOME_PATH, OE_CONFIG_FILE)
    
sys.path.insert(0, CONFIG_FILE_PATH)
import oebuild_config
WORKSPACE = oebuild_config.WORKSPACE
ADDONS = oebuild_config.ADDONS
WEB = oebuild_config.WEB
SERVER = oebuild_config.SERVER

if not os.path.exists(WORKSPACE):
    os.makedirs(WORKSPACE)

VERSION = '1.6'
SUPPORTED_VERSIONS = ('1.6')
PID_FILE = '%s/%s' % (tempfile.gettempdir(), 'openerp-pid')
CONF_FILENAME = 'oebuild.conf'
DEPRECATED_FILES = ('.project-dependencies',)

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
    shared_parser.add_argument("--update", dest="udeps", action="store_true", help="Update server and dependencies.")

    parser = ArgumentParser(description="Autobuild script for openERP.")
    subparsers = parser.add_subparsers(metavar="ACTION")
    
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
    
    for dfile in DEPRECATED_FILES:
        if os.path.exists(dfile):
            logger.warning('File %s is deprecated, you can remove it from the project' % dfile)
            
    logger.info('Entering %s mode' % args.func)
    
    if args.func == "init-new":
        init_new()
    else:
        conf = load_config_file()
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
    project = conf[c_s.PROJECT]
    if os.path.exists(target_path(project)):
        shutil.rmtree(target_path(project))
    
    full_path = src_path
    print str(full_path)
    for addon in os.listdir(full_path):
        if os.path.isdir('%s/%s' % (full_path, addon)) and addon[0] != '.':
            shutil.copytree('%s/%s' % (full_path, addon), '%s/%s' % (target_addons_path(project), addon))
            print str(('%s/%s' % (full_path, addon), '%s/%s' % (target_addons_path(project), addon)))
                    
    for path in deps_addons_path:
        full_path = '%s/%s' % (deps_path(project), path.rstrip('/'))
        for addon in os.listdir(full_path):
            if os.path.isdir('%s/%s' % (full_path, addon)) and addon[0] != '.' and not os.path.exists('%s/%s' % (target_addons_path(project), addon)):
                shutil.copytree('%s/%s' % (full_path, addon), '%s/%s' % (target_addons_path(project), addon))
                print str(('%s/%s' % (full_path, addon), '%s/%s' % (target_addons_path(project), addon)))
    
    os.chdir(target_path(project))
    tar = tarfile.open('%s.tar.gz' % ('openerp-install' if with_oe else 'custom-addons'), "w:gz")
    tar.add('custom-addons')
    
    if with_oe:
        for oe in ['server','web','addons']:
            tar.add('%s/%s' % (openerp_path(project), oe), arcname=oe)
            
    tar.close()
    
def init_new():
    if os.path.isfile('oebuild.conf'):
        answer = ''
        while answer.lower() not in ['y','n']:
            answer = raw_input("Configuration file already exists. Continue (y/n) ? ")
        
        if answer.lower() == 'n':
            return
        
    with open('oebuild.conf','w') as f:
        _, remote_server = BzrDir.open_tree_or_branch(SERVER)
        _, remote_addons = BzrDir.open_tree_or_branch(ADDONS)
        _, remote_web = BzrDir.open_tree_or_branch(WEB)
        
        contents = """{
    "oebuild-version": "1.6",
    "project": "%s",
    "openerp-server": {
        "url": "%s",
        "bzr-rev": "%s"
    },
    "openerp-addons": {
        "url": "%s",
        "bzr-rev": "%s"
    },
    "openerp-web": {
        "url": "%s",
        "bzr-rev": "%s"
    },
    "dependencies": []
}""" % (os.getcwd().split('/')[-1],SERVER,remote_server.revno(),ADDONS,remote_addons.revno(),WEB,remote_web.revno())
        
        f.write(contents)
    
def init_eclipse(conf):
    create_eclipse_project(conf)
    create_eclipse_pydev_project(conf)
        
def create_eclipse_project(conf):
    EM = lxml.builder.ElementMaker()
    
    doc = EM.projectDescription (
        EM.name(conf[c_s.PROJECT])
    )
    
    lxml.etree.ElementTree(doc).write(".project", pretty_print=True, 
                                      xml_declaration=True, encoding='UTF-8')
    
def create_eclipse_pydev_project(conf):
    project = conf[c_s.PROJECT]
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
    
    lxml.etree.ElementTree(doc).write(".pydevproject", pretty_print=True, 
                                      xml_declaration=True, encoding='UTF-8', standalone=False)
       
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
    project = conf[c_s.PROJECT]
        
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
    
    if args.func == "test":
        update_or_install = "u"
        out, _ = call_command("psql -U openerp -d postgres --tuples-only --command \"select * from pg_database where datname = '%s';\" | awk '{print $1}'" % args.db_name)
        db_exists = (out == args.db_name)
        if db_exists:
            logger.info('Database %s exists' % args.db_name)
        else:
            logger.info('Database %s does not exists' % args.db_name)
        
        if not db_exists or args.install:
            if db_exists:
                _, _ = call_command('dropdb -U openerp %s' % args.db_name)
            call_command('createdb -U openerp %s --encoding=unicode' % args.db_name)
            update_or_install = "i"

        
        openerp_output, _ = call_command('%s --addons-path=%s -d %s --db_user=openerp --db_password=openerp -%s %s --log-level=test --test-enable%s%s' %
                                         (
                                          '%s/%s' % (openerp_path(project), 'server/openerp-server'),
                                          addons_path,
                                          args.db_name,
                                          update_or_install,
                                          modules,
                                          ' --test-commit' if args.commit else '',
                                          ' --stop-after-init' if args.analyze else '',
                                          ), parse_log=args.analyze, register_pid=PID_FILE)
    else:
        openerp_output, _ = call_command('%s -c .openerp-dev-default --addons-path=%s -u %s --log-level=%s --log-handler=%s --xmlrpc-port=%d' % 
                                          (
                                           '%s/%s' % (openerp_path(project), 'server/openerp-server'),
                                           addons_path,
                                           modules,
                                           'info' if args.func == "run" else 'debug',
                                           ':INFO' if args.func == "run" else ':DEBUG',
                                           args.tcp_port,
                                          ), parse_log=False, register_pid=PID_FILE)

    if args.func == "test" and args.analyze:
        if 'ERROR' in openerp_output:
            sys.exit(1)
    sys.exit(0)
    
def load_config_file():
    if not (os.path.exists(CONF_FILENAME) and os.path.isfile(CONF_FILENAME)):
        logger.error('The project configuration does not exist : %s' % CONF_FILENAME)
        sys.exit(1)
        
    with open(CONF_FILENAME, "r") as source_file:
        try:
            conf = json.load(source_file)
        except ValueError, error:
            logger.error('%s is not JSON valid : %s' % (CONF_FILENAME, error))
            sys.exit(1)
        try:
            validictory.validate(conf, c_s.OEBUILD_SCHEMA)
        except ValueError, error:
            logger.error('%s is not a valid configuration file : %s' % (CONF_FILENAME, error))
            sys.exit(1)

    if conf[c_s.OEBUILD_VERSION] not in SUPPORTED_VERSIONS:
        logger.error(('The project configuration file is in version %s, openerp-autobuild is ' +
                      'in version %s and support only versions %s for configuration file') % (conf[c_s.OEBUILD_VERSION], VERSION, SUPPORTED_VERSIONS))
        sys.exit(1)
        
    return conf

def load_subconfig_file(conf_file_path):
    if not (os.path.exists(conf_file_path) and os.path.isfile(conf_file_path)):
        logger.info('The project configuration does not exist : %s' % conf_file_path)
        raise Exception()
        
    with open(conf_file_path, "r") as source_file:
        try:
            conf = json.load(source_file)
        except ValueError, error:
            logger.warning('%s is not JSON valid : %s' % (conf_file_path, error))
            raise Exception()
        try:
            validictory.validate(conf, c_s.OEBUILD_SCHEMA)
        except ValueError, error:
            logger.warning('%s is not a valid configuration file : %s' % (conf_file_path, error))
            raise Exception()

    if conf[c_s.OEBUILD_VERSION] not in SUPPORTED_VERSIONS:
        logger.warning(('The project configuration file is in version %s, openerp-autobuild is ' +
                      'in version %s and support only versions %s for configuration file') % (conf[c_s.OEBUILD_VERSION], VERSION, SUPPORTED_VERSIONS))
        raise Exception()
        
    return conf

def get_deps(conf):
    project = conf[c_s.PROJECT]
    
    for sp in ('server', 'addons', 'web'):
        try:
            bzr_checkout(conf['openerp-%s' % sp][c_s.URL], '%s/%s' % (openerp_path(project), sp), conf['openerp-%s' % sp].get(c_s.BZR_REV, None))
        except ConnectionError, error:
            logger.error('%s: %s' % ('%s/%s' % (openerp_path(project), sp), error))
    
    get_ext_deps(project, conf[c_s.DEPENDENCIES])
    
def get_ext_deps(project, deps):
    for dep in deps:
        destination = '%s/%s' % (deps_path(project).rstrip('/'), dep[c_s.DESTINATION])
        if dep[c_s.SCM] == c_s.SCM_BZR:
            try:
                bzr_checkout(dep[c_s.URL], destination, dep.get(c_s.BZR_REV, None))
            except ConnectionError, error:
                logger.error('%s: %s' % (destination, error))
            try:
                subconf = load_subconfig_file('%s/%s' % (destination.rstrip('/'), 'oebuild.conf'))
                get_ext_deps(project, subconf[c_s.DEPENDENCIES])
            except Exception :
                pass
        elif dep[c_s.SCM] == c_s.SCM_GIT:
            try:
                git_checkout(dep[c_s.URL], destination, dep.get(c_s.GIT_BRANCH, None))
            except AssertionError, error:
                logger.error('%s: %s' % (destination, error))
            except GitCommandError, error:
                logger.critical('%s: %s' % (destination, error))
                sys.exit(1)
            try:
                subconf = load_subconfig_file('%s/%s' % (destination.rstrip('/'), 'oebuild.conf'))
                get_ext_deps(project, subconf[c_s.DEPENDENCIES])
            except Exception :
                pass
        addons_path = dep[c_s.DESTINATION]
        if dep.get(c_s.ADDONS_PATH, False):
            addons_path = '%s/%s' % (addons_path, dep[c_s.ADDONS_PATH].rstrip('/'))
        deps_addons_path.append(addons_path)

def bzr_checkout(source, destination, revno=None):
    accelerator_tree, remote = BzrDir.open_tree_or_branch(source)
    if revno:
        revno = int(revno)
    else:
        revno = remote.revno()
    
    if os.path.exists(destination) and os.path.isdir(destination):
        local_tree, local = BzrDir.open_tree_or_branch(destination)
        local_revno = local.revision_id_to_revno(local_tree.last_revision())
        if revno == local_revno:
            logger.info('%s : Up-to-date (revno : %s)' % (destination, local_revno))
            return
        else:
            shutil.rmtree(destination) 

    if not os.path.exists(destination):
        os.makedirs(destination)

    logger.info('%s : Checkout from %s (revno : %s)...' % (destination, source, revno))
    remote.create_checkout(destination, remote.get_rev_id(revno), True, accelerator_tree)

def git_checkout(source, destination, branch=None):
    if not os.path.exists(destination):
        os.makedirs(destination)  
        logger.info('%s : Clone from %s...' % (destination, source))
        local = Repo.clone_from(source, destination)
        if branch:
            logger.info('%s : Checkout branch %s...' % (destination, branch))
            local.git.checkout(branch)
    else:
        local = Repo(destination)
        logger.info('%s : Pull from %s...' % (destination, source))
        local.remotes.origin.pull()
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