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
import oebuild_conf_schema_1_5 as c_s
import tarfile

load_plugins()

VERSION = '1.5'
SUPPORTED_VERSIONS = ('1.4', '1.5')
PID_FILE = '%s/%s' % (tempfile.gettempdir(), 'openerp-pid')
CONF_FILE = 'oebuild.conf'
DEPRECATED_FILES = ('.project-dependencies',)
OPENERP_PATH = '%s/%s' % (os.getcwd().rstrip('/'), 'openerp')
DEPS_PATH = '%s/%s' % (os.getcwd().rstrip('/'), 'deps')
TARGET_PATH = '%s/%s' % (os.getcwd().rstrip('/'), 'target')
TARGET_ADDONS_PATH = '%s/%s' % (TARGET_PATH, 'custom-addons')
SRC_PATH = '%s/%s' % (os.getcwd().rstrip('/'), 'src')

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
    
    args = parser.parse_args()
    
    for dfile in DEPRECATED_FILES:
        if os.path.exists(dfile):
            logger.warning('File %s is deprecated, you can remove it from the project' % dfile)
    
    load_config_file()
    
    logger.info('Entering %s mode' % args.func)
    
    if args.func == "assembly":
        assembly(args.with_oe)
    else:  
        kill_old_openerp()
        run_openerp(args)
        
    logger.info('Terminate %s mode' % args.func)
    
def assembly(with_oe=False):
    if os.path.exists(TARGET_PATH):
        shutil.rmtree(TARGET_PATH)
    shutil.copytree(SRC_PATH, TARGET_ADDONS_PATH)
    for path in deps_addons_path:
        full_path = '%s/%s' % (DEPS_PATH.rstrip('/'), path[5:])
        for addon in os.listdir(full_path):
            if os.path.isdir('%s/%s' % (full_path, addon)) and addon not in ['.bzr', '.git']:
                shutil.copytree('%s/%s' % (full_path, addon), '%s/%s' % (TARGET_ADDONS_PATH, addon))
    
    os.chdir(TARGET_PATH)
    tar = tarfile.open('%s.tar.gz' % ('openerp-install' if with_oe else 'custom-addons'), "w:gz")
    tar.add('custom-addons')
    
    if with_oe:
        for oe in ['server','web','addons']:
            tar.add('%s/%s' % (OPENERP_PATH, oe), arcname=oe)
            
    tar.close()
    
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

def run_openerp(args):
        
    if args.modules == "def-all":
        modules = ""
        for module in os.listdir("./src"):
            modules = "%s,%s" % (module,modules)
        modules = modules.rstrip(",")
    else:
        modules = args.modules
        
    addons_path = "openerp/addons"
    for path in deps_addons_path:
        addons_path = "%s,%s" % (addons_path, path)
    addons_path = "%s,src,openerp/web/addons" % addons_path
    
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

        
        openerp_output, _ = call_command('openerp/server/openerp-server --addons-path=%s -d %s --db_user=openerp --db_password=openerp -%s %s --log-level=test --test-enable%s%s' %
                                         (
                                          addons_path,
                                          args.db_name,
                                          update_or_install,
                                          modules,
                                          ' --test-commit' if args.commit else '',
                                          ' --stop-after-init' if args.analyze else '',
                                          ), parse_log=args.analyze, register_pid=PID_FILE)
    else:
        openerp_output, _ = call_command('openerp/server/openerp-server -c .openerp-dev-default --addons-path=%s -u %s --log-level=%s --log-handler=%s --xmlrpc-port=%d' % 
                                          (
                                          addons_path,
                                          modules,
                                          'info' if args.func == "run" else 'debug',
                                          ':INFO' if args.func == "run" else ':DEBUG',
                                          args.tcp_port,
                                          ), parse_log=False, register_pid=PID_FILE)

    if args.func == "test" and args.analyze:
        openerp_output = re.sub(r'(?m)^.*ERROR.*expected \+32 444 11 22 33, got \+32 444112233.*\n?', '', openerp_output)
        openerp_output = re.sub(r'(?m)^.*ERROR.*At least one test failed when loading the modules.*\n?', '', openerp_output)
        if 'ERROR' in openerp_output:
            sys.exit(1)
    sys.exit(0)
    
def load_config_file():
    if not (os.path.exists(CONF_FILE) and os.path.isfile(CONF_FILE)):
        logger.error('The project configuration does not exist : %s' % CONF_FILE)
        sys.exit(1)
        
    with open(CONF_FILE, "r") as source_file:
        try:
            conf = json.load(source_file)
        except ValueError, error:
            logger.error('%s is not JSON valid : %s' % (CONF_FILE, error))
            sys.exit(1)
        try:
            validictory.validate(conf, c_s.OEBUILD_SCHEMA)
        except ValueError, error:
            logger.error('%s is not a valid configuration file : %s' % (CONF_FILE, error))
            sys.exit(1)

    if conf[c_s.OEBUILD_VERSION] not in SUPPORTED_VERSIONS:
        logger.error(('The project configuration file is in version %s, openerp-autobuild is ' +
                      'in version %s and support only versions %s for configuration file') % (conf[c_s.OEBUILD_VERSION], VERSION, SUPPORTED_VERSIONS))
        sys.exit(1)
       
    for sp in ('server', 'addons', 'web'):
        try:
            bzr_checkout(conf['openerp-%s' % sp][c_s.URL], '%s/%s' % (OPENERP_PATH, sp), conf['openerp-%s' % sp].get(c_s.BZR_REV, None))
        except ConnectionError, error:
            logger.error('%s: %s' % ('%s/%s' % (OPENERP_PATH, sp), error))
    
    for dep in conf[c_s.DEPENDENCIES]:
        destination = '%s/%s' % (DEPS_PATH.rstrip('/'), dep[c_s.DESTINATION])
        if dep[c_s.SCM] == c_s.SCM_BZR:
            try:
                bzr_checkout(dep[c_s.URL], destination, dep.get(c_s.BZR_REV, None))
            except ConnectionError, error:
                logger.error('%s: %s' % (destination, error))
        elif dep[c_s.SCM] == c_s.SCM_GIT:
            try:
                git_checkout(dep[c_s.URL], destination, dep.get(c_s.GIT_BRANCH, None))
            except AssertionError, error:
                logger.error('%s: %s' % (destination, error))
            except GitCommandError, error:
                logger.critical('%s: %s' % (destination, error))
                sys.exit(1)
        addons_path = 'deps/%s' % dep[c_s.DESTINATION]
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