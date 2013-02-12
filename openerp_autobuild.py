#!/usr/bin/env python
# coding: utf-8

import sys
import subprocess
from optparse import OptionParser
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
    
    _, err = call_command('dropdb %s' % config['database'], log_err=False)
    if err:
        logging.info('dropdb : database doesn''t exist, nothing to frop')
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
        local = Branch.open(path)
        res = local.pull(remote)
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