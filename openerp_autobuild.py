#!/usr/bin/env python
# coding: utf-8

import sys
import subprocess
from optparse import OptionParser
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

def dummy():
    usage = "usage: %prog [options]"
    parser = OptionParser(usage)
    parser.add_option("-c", "--config_file", dest="config_file",
                      help="the autobuild config file")
    parser.add_option("-w", "--workspace", dest="workspace",
                      help="the workspace")
    options, _ = parser.parse_args()
    config_file = open(options.config_file)
    config = json.load(config_file)
    config_file.close()
    
    for source in config['sources']:
        if source['scm'] == 'bzr':
            bzr_clone(options.workspace, source)
        elif source['scm'] == 'git':
            git_clone(options.workspace, source)

    os.chdir('%s/%s' % (options.workspace.rstrip('/'), config['openerp-path'].rstrip('/')))
    
    _, err = call_command('dropdb -w %s' % config['database'], log_err=False)
    if err:
        logging.info('dropdb : database doesn''t exist, nothing to drop')
    call_command('createdb %s --encoding=unicode' % config['database'])
    
    addons_path = 'addons,'
    for addon in config['addons']:
        addons_path += '%s/%s,' % (options.workspace.rstrip('/'), addon)
    addons_path += 'web/addons'
    
    install = ''
    for addon in config['install']:
        install += '%s,' % (addon)
    install = install.rstrip(',')
    
    openerp_output, _  = call_command('server/openerp-server --addons-path=%s -d %s -i %s --log-level=test --test-commit --stop-after-init' % (addons_path, 
                                                                                                                                               config['database'], 
                                                                                                                                               install))
    
    call_command('dropdb %s' % config['database'])

    if 'ERROR' in openerp_output:
        sys.exit(1)
    
    sys.exit(0)
    
    
    
def main():
    parser = ArgumentParser(description="Autobuild script for openERP.")
    subparsers = parser.add_subparsers(metavar="ACTION")
    
    parser_run = subparsers.add_parser('run', help="Run openERP server normally (default)")
    parser_run.add_argument("-m", "--modules", dest="modules", default="all", help="Modules to use. If omitted, all modules will be used.")
    parser_run.add_argument("--install", action="store_true", dest="install", help="Specify if addons should be installed. Update them if omitted.")
    parser_run.set_defaults(func="run")
    
    parser_test = subparsers.add_parser('test', help="Run openERP server, perform tests, stop the server and display tests results")
    parser_test.add_argument("-m", "--modules", dest="modules", default="all", help="Modules to use. If omitted, all modules will be used.")
    parser_test.add_argument("--test-commit", action="store_true", dest="commit", help="Commit test results in DB.")
    parser_test.set_defaults(func="test")
    
    parser_debug = subparsers.add_parser('debug', help="Run openERP server with full debug messages")
    parser_debug.add_argument("-m", "--modules", dest="modules", default="all", help="Modules to use. If omitted, all modules will be used.")
    parser_debug.add_argument("--install", action="store_true", dest="install", help="Specify if addons should be installed. Update them if omitted.")
    parser_debug.set_defaults(func="debug")
    
    args = parser.parse_args()
    
    check_openerp_install()
    
    #run_openerp(args)
    
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
                                          ))
    else:
        openerp_output, _ = call_command('openerp/server/openerp-server -c .openerp-dev-default -d %s -%s %s --log-level=%s --log-handler=%s' % 
                                          (
                                          db_name,
                                          'i' if args.install else 'u',
                                          args.modules,
                                          'info' if args.func == "run" else 'debug',
                                          ':INFO' if args.func == "run" else ':DEBUG'
                                          ))

    if args.func == "test":
        call_command('dropdb -U openerp %s' % db_name)

    if 'ERROR' in openerp_output:
        sys.exit(1)
    
    sys.exit(0)
    
def check_openerp_install():
    with open(".openerp-sources","r") as source_file:
        sources = json.load(source_file)['sources']
    
    for source in sources:
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

def call_command(command, log_in=True, log_out=True, log_err=True):
    if log_in : 
        logging.info(command)
    process = subprocess.Popen(command,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    out, err = process.communicate()
    if log_err and err:
        logging.error(err)
    if log_out and out:
        logging.info(out)
    return (out, err)

if __name__ == "__main__":
    main()