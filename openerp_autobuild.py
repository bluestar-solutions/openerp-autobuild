#!/usr/bin/env python
# coding: utf-8

import sys
import subprocess
from optparse import OptionParser

def main():
    usage = "usage: %prog [options]"
    parser = OptionParser(usage)
    parser.add_option("-H", "--openerp-home", dest="oe_home",
                      help="the home of openerp")
    parser.add_option("-i", "--install", dest="install",
                      help="the addons to install")
    parser.add_option("-a", "--addons", dest="addons",
                      help="the database username")
    parser.add_option("-d", "--database", dest="database",
                      help="the database name")
    parser.add_option("-w", "--workspace", dest="workspace",
                      help="the workspace")
    options, _ = parser.parse_args()
    
    _, _ = call_command('cd %s' % options.oe_home)
    _, _ = call_command('createdb %s --encoding=unicode' % options.database)
    
    addons = 'addons,'
    for addon in options.addons.split(','):
        addons += '../../' + addon + ','
    addons += 'web/addons'
    
    _, _ = call_command('server/openerp-server --addons-path=%s -d %s -i %s --log-level=test --stop-after-init > %s/openerp.log' % (addons, options.database, options.install, options.workspace))
    
    _, _ = call_command('dropdb %s' % options.database)
    
    _, _ = call_command('cat %s/openerp.log' % options.workspace)
    if 'ERROR' in open('%s/openerp.log' % options.workspace).read():
        sys.exit(1)
    
    sys.exit(0)

def call_command(command):
    process = subprocess.Popen(command.split(' '),
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    return process.communicate()

if __name__ == "__main__":
    main()