#!/usr/bin/env python
# coding: utf-8

import sys
import subprocess
from argparse import ArgumentParser
import json 
from bzrlib.plugin import load_plugins
from bzrlib.branch import Branch
import os.path
import logging
from git import Repo

load_plugins()
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')
    
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
    
    args = parser.parse_args()
    
    if args.udeps or not os.path.exists("./openerp"):
        check_project_dependencies()
    
    kill_old_openerp()
    
    run_openerp(args)
    
def kill_old_openerp():
    if os.path.exists("openerp-pid") and os.path.isfile("openerp-pid"):
        with open("openerp-pid","r") as f:
            pid = f.read()
            pid = int(pid) if pid != '' else 0
        if pid != 0:
            try:
                os.kill(pid,9)
            except:
                pass
            with open("openerp-pid","w") as f:
                f.write("%d" % 0)

def run_openerp(args):
    logging.info('Entering %s mode' % args.func)
    
    if args.modules == "def-all":
        modules = ""
        for module in os.listdir("./src"):
            modules = "%s,%s" % (module,modules)
        modules = modules.rstrip(",")
    else:
        modules = args.modules
        
    addons_path = "openerp/addons"
        
    if os.path.isdir("./deps"):
        for addon in os.listdir("./deps"):
            addons_path = "%s,deps/%s/src" % (addons_path,addon)
    addons_path = "%s,src,openerp/web/addons" % addons_path
    
    if args.func == "test":
        update_or_install = "u"
        db_exists = call_command("psql -U openerp -d postgres --tuples-only --command \"select * from pg_database where datname = '%s';\" | awk '{print $1}'" % args.db_name)[0] == args.db_name
        
        if db_exists or args.install:
            if not db_exists:
                _, err = call_command('dropdb -U openerp %s' % args.db_name)
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
                                          ), parse_log=args.analyze, register_pid="openerp-pid")
    else:
        openerp_output, _ = call_command('openerp/server/openerp-server -c .openerp-dev-default --addons-path=%s -u %s --log-level=%s --log-handler=%s --xmlrpc-port=%d' % 
                                          (
                                          addons_path,
                                          modules,
                                          'info' if args.func == "run" else 'debug',
                                          ':INFO' if args.func == "run" else ':DEBUG',
                                          args.tcp_port,
                                          ), parse_log=False, register_pid="openerp-pid")

    if args.analyze:
        if 'ERROR' in openerp_output:
            sys.exit(1)
        sys.exit(0)
    
def check_project_dependencies():
    with open(".project-dependencies","r") as source_file:
        deps = json.load(source_file)
    
    for source in deps['sources']:
        if source['scm'] == 'bzr':
            bzr_clone(os.getcwd(), source)
        elif source['scm'] == 'git':
            git_clone(os.getcwd(), source)

def bzr_clone(workspace, source):
    path = '%s/%s' % (workspace.rstrip('/'), source['destination'])
    subpath, _ =os.path.split(path)
    if not os.path.exists(path):
        if not os.path.exists(subpath):
            os.makedirs(subpath)  
        logging.info('Clone %s from %s...' % (path, source['url']))
        remote = Branch.open(source['url'])
        remote.bzrdir.sprout(path).open_branch()
    else:
        logging.info('Pull %s from %s...' % (path, source['url']))
        remote = Branch.open(source['url'])
        local = Branch.open("file:///%s" % path)
        res = local.pull(remote, overwrite=True)
        if res.old_revno == res.new_revno:
            logging.info('Already up-to-date.')
        else:
            logging.info('Update revision %s to %s' % (res.old_revno, res.new_revno))

def git_clone(workspace, source):
    path = '%s/%s' % (workspace.rstrip('/'), source['destination'])
    if not os.path.exists(path):
        os.makedirs(path)  
        logging.info('Clone %s from %s...' % (path, source['url']))
        local = Repo.clone_from(source['url'], path)
        logging.info('Checkout branch %s...' % (source['branch']))
        res = local.git.checkout(source['branch'])
        if res:
            logging.info(res)
    else:
        local = Repo(path)
        logging.info('Checkout branch %s...' % (source['branch']))
        res = local.git.checkout(source['branch'])
        if res:
            logging.info(res)
        logging.info('Pull %s from %s...' % (path, source['url']))
        logging.info(local.git.pull())

def call_command(command, log_in=True, log_out=True, log_err=True, parse_log=True, register_pid=None):
    if log_in : 
        logging.info(command)
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
            logging.error(err)
        if log_out and out:
            logging.info(out)
        return (out, err)
    else:
        for l in iter(process.stdout.readline, None):
            print(l.rstrip('\n'))
            process.stdout.flush()
        return (None, None)

if __name__ == "__main__":
    main()