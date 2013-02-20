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
    shared_parser.add_argument("-m", "--modules", dest="modules", default="all", help="Modules to use. If omitted, all modules will be used.")
    shared_parser.add_argument("-p", "--tcp-port", dest="tcp_port", type=int, default="8069", help="TCP server port (default:8069).")
    shared_parser.add_argument("--parse-log", dest="parse_log", action="store_true", help="Parse log in one time (Jenkins).")
    
    parser = ArgumentParser(description="Autobuild script for openERP.")
    subparsers = parser.add_subparsers(metavar="ACTION")
    
    parser_run = subparsers.add_parser('run', help="Run openERP server normally (default)", parents=[shared_parser])
    parser_run.add_argument("--install", action="store_true", dest="install", help="Specify if addons should be installed. Update them if omitted.")
    parser_run.set_defaults(func="run")
    
    parser_test = subparsers.add_parser('test', help="Run openERP server, perform tests, stop the server and display tests results", parents=[shared_parser])
    parser_test.add_argument("--test-commit", action="store_true", dest="commit", help="Commit test results in DB.")
    parser_test.set_defaults(func="test")
    
    parser_debug = subparsers.add_parser('debug', help="Run openERP server with full debug messages", parents=[shared_parser])
    parser_debug.set_defaults(func="debug")
    
    args = parser.parse_args()
    
    check_project_dependencies()
    
    kill_old_openerp()
    
    run_openerp(args)
    
def kill_old_openerp():
    if os.path.exists("openerp-pid") and os.path.isfile("openerp-pid"):
        with open("openerp-pid","r") as f:
            pid = int(f.read())
        if pid != 0:
            try:
                os.kill(pid,9)
            except:
                pass
            with open("openerp-pid","w") as f:
                f.write("%d" % 0)

def run_openerp(args):
    logging.info('Entering %s mode' % args.func)
    
    db_name = "openerp_%s_db" % args.func
        
    if args.func == "test" or args.install:
        _, err = call_command('dropdb -U openerp %s' % db_name)
        if err:
            logging.info('dropdb : database doesn''t exist, nothing to drop')
        call_command('createdb -U openerp %s --encoding=unicode' % db_name)
    
    if args.func == "test":
        openerp_output, _ = call_command('openerp/server/openerp-server --addons-path=src,openerp/addons,openerp/web/addons -d %s --db_user=openerp --db_password=openerp -i %s --log-level=test --test-%s --stop-after-init' %
                                         (
                                          db_name,
                                          args.modules,
                                          'commit' if args.commit else 'enable'
                                          ), parse_log=args.parse_log, register_pid="openerp-pid")
    else:
        openerp_output, _ = call_command('openerp/server/openerp-server -c .openerp-dev-default -d %s -%s %s --log-level=%s --log-handler=%s --xmlrpc-port=%d' % 
                                          (
                                          db_name,
                                          'i' if args.install else 'u',
                                          args.modules,
                                          'info' if args.func == "run" else 'debug',
                                          ':INFO' if args.func == "run" else ':DEBUG',
                                          args.tcp_port,
                                          ), parse_log=args.parse_log, register_pid="openerp-pid")

    if args.func == "test":
        call_command('dropdb -U openerp %s' % db_name)

    if args.parse_log:
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
                               stderr=subprocess.STDOUT)
    
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
        for l in iter(process.stdout.readline, b''):
            print(l.rstrip('\n'))
        return (None, None)

if __name__ == "__main__":
    main()