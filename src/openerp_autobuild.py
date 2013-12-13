#!/usr/bin/env python
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK - This string is needed to activate argcomplete on this script ! 
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
import sys
import subprocess
from bzrlib.plugin import load_plugins
from bzrlib.bzrdir import BzrDir
from bzrlib.errors import NotBranchError
from git import Repo
from git.exc import InvalidGitRepositoryError
import shutil
from settings_parser.schema import user_conf_schema, oebuild_conf_schema as schema ,\
    oebuild_conf_schema
from settings_parser.user_conf_parser import UserConfParser
from settings_parser.oebuild_conf_parser import OEBuildConfParser, IgnoreSubConf
import tarfile
import lxml.etree
import lxml.builder
import psycopg2.extras
import StringIO
from xml.dom import minidom
import dialogs
import json
import params
from oebuild_logger import _ex, logging, LOG_PARSER, COLORIZED
import re
from argument_parser import OEArgumentParser

load_plugins()
    
class Autobuild():
    
    _logger = logging.getLogger(__name__)
    _arg_parser = None
    
    user_conf = None
    project = None
    workspace_path = lambda self: self.user_conf[user_conf_schema.WORKSPACE].replace('~', params.USER_HOME_PATH)
    project_path = lambda self: '%s/%s' % (self.workspace_path(), self.project)
    openerp_path = lambda self: '%s/%s' % (self.project_path(), 'openerp')
    deps_path = lambda self: '%s/%s' % (self.project_path(), 'deps')
    target_path = lambda self: '%s/%s' % (self.project_path(), 'target')
    target_addons_path = lambda self: '%s/%s' % (self.target_path(), 'custom-addons')
    deps_cache_file = lambda self: '%s/%s' % (self.project_path(), 'deps.cache')
    py_deps_cache_file = lambda self: '%s/%s' % (self.project_path(), 'python-deps.cache')
    virtualenv_path = lambda self: '%s/%s' % (self.project_path(), 'venv')
    virtual_python = lambda self: '%s/%s' % (self.virtualenv_path(), 'bin/python')
    virtual_pip = lambda self: '%s/%s' % (self.virtualenv_path(), 'bin/pip')
    src_path = os.path.curdir

    pid_file = lambda self: '%s/%s' % ('/tmp', '%s.pid' % self.project)
    
    oebuild_conf_parser = None
    
    deps_addons_path = []
    python_deps = []
    
    def __init__(self, arg_parser):
        self._arg_parser = arg_parser
        args = self._arg_parser.args
        
        self.oebuild_conf_parser = OEBuildConfParser(getattr(args, 'analyze', False))
        
        self.user_conf = UserConfParser().load_user_config_file()
                
        self._logger.info('Entering %s mode' % args.func)
        
        if args.func == "init-new":
            overwrite = "no"
            if os.path.exists(params.OE_CONFIG_FILE):
                overwrite = dialogs.query_yes_no("%s file already exists, overwrite it with default one ?" % params.OE_CONFIG_FILE, overwrite)   
            if (not os.path.exists(params.OE_CONFIG_FILE)) or overwrite == "yes":
                shutil.copyfile(params.DEFAULT_OE_CONFIG_FILE, params.OE_CONFIG_FILE)
    
            self.oebuild_conf_parser.create_oebuild_config_file(self.user_conf[user_conf_schema.DEFAULT_SERIE])
        else:
            conf = self.oebuild_conf_parser.load_oebuild_config_file(self.user_conf[user_conf_schema.CONF_FILES])
            self.project = conf[schema.PROJECT]
            
            if args.no_update:
                try:
                    with open(self.deps_cache_file(), 'r') as f:
                        self.deps_addons_path = json.loads(f.read())
                except Exception, e:
                    self._logger.error(_ex('Impossible to read %s' % self.deps_cache_file(), e))
                    sys.exit(1)        
            else:
                self.get_deps(conf)
                try:
                    with open(self.deps_cache_file(), 'w') as f:
                        f.write(json.dumps(self.deps_addons_path))
                except Exception, e:
                    self._logger.warning(_ex('Impossible to write %s' % self.deps_cache_file(), e))
    
            if args.func == "init-eclipse":
                self.init_eclipse(conf)
            elif args.func == "assembly":
                self.assembly(conf, args.with_oe)
            else:
                self.kill_old_openerp(conf)
                self.run_openerp(conf, args)
            
        self._logger.info('Terminate %s mode' % args.func)
        
    def assembly(self, conf, with_oe=False):
        if os.path.exists(self.target_path()):
            shutil.rmtree(self.target_path())
        os.mkdir(self.target_path())
        os.mkdir(self.target_addons_path())
        
        full_path = self.src_path
        for addon in os.listdir(full_path):
            if os.path.isdir('%s/%s' % (full_path, addon)) and addon[0] != '.':
                shutil.copytree('%s/%s' % (full_path, addon), '%s/%s' % (self.target_addons_path(), addon))
                        
        for path in self.deps_addons_path:
            full_path = '%s/%s' % (self.deps_path(), path.rstrip('/'))
            for addon in os.listdir(full_path):
                if os.path.isdir('%s/%s' % (full_path, addon)) and addon[0] != '.' and not os.path.exists('%s/%s' % (self.target_addons_path(), addon)):
                    shutil.copytree('%s/%s' % (full_path, addon), '%s/%s' % (self.target_addons_path(), addon))
        
        os.chdir(self.target_path())
        tar = tarfile.open('%s.tar.gz' % ('openerp-install' if with_oe else 'custom-addons'), "w:gz")
        tar.add('custom-addons')
        
        if with_oe:
            for oe in ['server','web','addons']:
                tar.add('%s/%s' % (self.openerp_path(), oe), arcname=oe)
                
        tar.close()
        
    def init_eclipse(self, conf):
        self.create_eclipse_project(conf)
        self.create_eclipse_pydev_project(conf)
        
    def write_xml(self, filename, document, standalone=None):
        stream = StringIO.StringIO()
        lxml.etree.ElementTree(document).write(stream, xml_declaration=True, encoding='UTF-8', standalone=standalone)
        mdom = minidom.parseString(stream.getvalue())
        header = stream.getvalue().split('\n')[0]
        stream.close()
    
        f = open(filename, "wb")
        pretty = mdom.toprettyxml(encoding='UTF-8')
        f.write(header + '\n' + '\n'.join(pretty.split('\n')[1:]))
        f.close()
            
    def create_eclipse_project(self, conf):
        EM = lxml.builder.ElementMaker()
        
        doc = EM.projectDescription (
            EM.name(conf[schema.PROJECT])
        )
        self.write_xml('.project', doc)
        
    def create_eclipse_pydev_project(self, conf):
        EM = lxml.builder.ElementMaker()
        
        ext_path = EM.pydev_pathproperty(name='org.python.pydev.PROJECT_EXTERNAL_SOURCE_PATH')
        ext_path.append(EM.path(self.openerp_path() + '/server'))
        
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
        self.write_xml('.pydevproject', doc, standalone=False)
        
    def create_or_update_venv(self, conf, args):

        if os.path.exists(self.virtualenv_path()) and os.path.exists(self.py_deps_cache_file()):
            if args.no_update:
                return
            
            is_config_changed = True
            with open(self.py_deps_cache_file(),'r') as f:
                last_run_py_deps = set(['%s%s' % (dep[oebuild_conf_schema.NAME], dep.get(oebuild_conf_schema.SPECIFIER, '')) for dep in json.load(f)])
                current_py_deps = set(['%s%s' % (dep[oebuild_conf_schema.NAME], dep.get(oebuild_conf_schema.SPECIFIER, '')) for dep in self.python_deps])
                is_config_changed = len(last_run_py_deps) != len(current_py_deps) or last_run_py_deps.symmetric_difference(current_py_deps) != set()
                
            if not is_config_changed:
                self._logger.info("virtualenv %s: No changes in Python dependencies, use it as is" % self.virtualenv_path())
                return
            
            self._logger.info("virtualenv %s: Changes in Python dependencies, need to rebuild" % self.virtualenv_path())
            shutil.rmtree(self.virtualenv_path())
            os.remove(self.py_deps_cache_file())
        
        elif not os.path.exists(self.py_deps_cache_file()):
            if args.no_update:
                self._logger.error("Cannot run in no-update mode without last run Python dependencies cache file, try running without --no-update argument.")
                sys.exit(1)
            if os.path.exists(self.virtualenv_path()):
                self._logger.info("virtualenv %s : No last run Python dependencies cache file, need to rebuild" % self.virtualenv_path())
                shutil.rmtree(self.virtualenv_path())    
            
        py_deps_string = " ".join(["'%s%s'" % (dep[oebuild_conf_schema.NAME], dep.get(oebuild_conf_schema.SPECIFIER, '')) for dep in self.python_deps])
        self._logger.info("virtualenv %s : Create and install Python dependencies (%s)" % (self.virtualenv_path(), py_deps_string))
        out, err = self.call_command("virtualenv -q %s" % self.virtualenv_path(),
                                   log_in=False, log_out=False, log_err=True)
        for o in out.split('\n'):
            if len(o) > 0:
                self._logger.info("virtualenv %s: %s" % (self.virtualenv_path(), o))
        for e in err.split('\n'):
            if len(e) > 0:
                self._logger.error("virtualenv %s: %s" % (self.virtualenv_path(), e))
                sys.exit(1)
        
        out, err = self.call_command("%s install -q --upgrade %s" % (
            self.virtual_pip(), py_deps_string
            ),
            log_in=False, log_out=False, log_err=False)
        for o in out.split('\n'):
            if len(o) > 0:
                self._logger.info("virtualenv %s: %s" % (self.virtualenv_path(), o))
        for e in err.split('\n'):
            if re.search(r'Format RepositoryFormat6\(\) .* is deprecated', e, re.I):
                # If an error is thrown because of using deprecated RepositoryFormat6() format, just warn and continue
                self._logger.warning("virtualenv %s: %s" % (self.virtualenv_path(), e))
            elif len(e) > 0:
                self._logger.error("virtualenv %s: %s" % (self.virtualenv_path(), e))
                sys.exit(1)
        
        with open(self.py_deps_cache_file(),'w+') as f:
            json.dump(list(self.python_deps), f)
    
    def kill_old_openerp(self, conf):
        if os.path.exists(self.pid_file()) and os.path.isfile(self.pid_file()):
            with open(self.pid_file(),"r") as f:
                pid = f.read()
                pid = int(pid) if pid != '' else 0
            if pid != 0:
                try:
                    os.kill(pid,9)
                except:
                    pass
                with open(self.pid_file(),"w") as f:
                    f.write("%d" % 0)
    
    def run_openerp(self, conf, args):
        self.create_or_update_venv(conf, args)
        
        if not os.path.exists(params.OE_CONFIG_FILE):
            self._logger.error('The OpenERP configuration does not exist : %s, use openerp-autobuild init to create it.' % params.OE_CONFIG_FILE)
            sys.exit(1)
        
        if not os.path.exists(self.workspace_path()):
            self._logger.info('Creating nonexistent openerp-autobuild workspace : %s', self.workspace_path())
            os.makedirs(self.workspace_path())
        
        if args.modules == "def-all":
            modules = ""
            for module in os.listdir("."):
                if os.path.isdir(module) and not module.startswith('.'):
                    modules = "%s,%s" % (module,modules)
            modules = modules.rstrip(",")
        else:
            modules = args.modules
            
        addons_path = '%s/%s' % (self.openerp_path(), 'addons')
        for path in self.deps_addons_path:
            addons_path = "%s,%s" % (addons_path, '%s/%s' % (self.deps_path(), path))
        addons_path = "%s%s,%s" % (addons_path, ',.' if modules != '' else '', '%s/%s' % (self.openerp_path(), 'web/addons'))
        
        db_conf = self.user_conf[user_conf_schema.DATABASE]
        if args.func == "test":
            update_or_install = "u"
            try:
                conn = psycopg2.connect(host = db_conf.get(user_conf_schema.HOST, 'localhost'),
                                        port = db_conf.get(user_conf_schema.PORT, '5432'),
                                        user = db_conf.get(user_conf_schema.USER, 'openerp'),
                                        password = db_conf.get(user_conf_schema.PASSWORD, 'openerp'),
                                        database = 'postgres')
            except:
                self._logger.error("Unable to connect to the database.")
                sys.exit(1)
    
            cur = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)
            cur.execute("select * from pg_database where datname = '%s'" % args.db_name)
            db_exists = cur.fetchall() or False
            if db_exists:
                self._logger.info('Database %s exists' % args.db_name)
            else:
                self._logger.info('Database %s does not exist' % args.db_name)
            
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
    
            cmd = '%s %s/%s' % (self.virtual_python(), self.openerp_path(), 'server/openerp-server')
            cmd += ' --addons-path=%s' % addons_path
            cmd += ' -d %s' % args.db_name
            cmd += ' --db_user=%s' % db_conf.get(user_conf_schema.USER, 'openerp')
            cmd += ' --db_password=%s' % db_conf.get(user_conf_schema.PASSWORD, 'openerp')
            cmd += ' --db_host=%s' % db_conf.get(user_conf_schema.HOST, 'localhost')
            cmd += ' --db_port=%s' % db_conf.get(user_conf_schema.PORT, '5432')
            cmd += ' -%s %s' % (update_or_install, modules)
            cmd += ' --log-level=test --test-enable'
            if args.commit:
                cmd += ' --test-commit'
            if args.analyze or args.stopafterinit:
                cmd += ' --stop-after-init'
            try:
                self._logger.info('Start OpenERP ...')
                openerp_output, _ = self.call_command(cmd, parse_log=args.analyze, register_pid=self.pid_file(), log_in=False, parse_tests=True)
            except KeyboardInterrupt:
                self._logger.info("OpenERP stopped from command line")
                if args.func == "test" and args.analyze:
                    sys.exit(1)
        else:
            cmd = '%s %s/%s -c .openerp-dev-default' % (self.virtual_python(), self.openerp_path(), 'server/openerp-server')
            cmd += ' --addons-path=%s' % addons_path
            cmd += ' --db_user=%s' % db_conf.get(user_conf_schema.USER, 'openerp')
            cmd += ' --db_password=%s' % db_conf.get(user_conf_schema.PASSWORD, 'openerp')
            cmd += ' --db_host=%s' % db_conf.get(user_conf_schema.HOST, 'localhost')
            cmd += ' --db_port=%s' % db_conf.get(user_conf_schema.PORT, '5432')
            cmd += ' -u %s' % modules
            cmd += ' --log-level=%s' % ('info' if args.func == "run" else 'debug')
            cmd += ' --log-handler=%s' % (':INFO' if args.func == "run" else ':DEBUG')
            cmd += ' --xmlrpc-port=%d' % args.tcp_port
            cmd += ' --netrpc-port=%d' % args.netrpc_port
            try:
                self._logger.info('Start OpenERP ...')
                openerp_output, _ = self.call_command(cmd, parse_log=False, register_pid=self.pid_file(), log_in=False)
            except KeyboardInterrupt:
                self._logger.info("OpenERP stopped after keyboard interrupt")
    
        if args.func == "test" and args.analyze:
            if 'ERROR' in openerp_output:
                sys.exit(1)
        sys.exit(0)
    
    def get_deps(self, conf):
        oe_conf = conf[schema.OPENERP]
        serie_name = oe_conf[schema.SERIE]
        
        serie = None
        for tmp_serie in self.user_conf[user_conf_schema.OPENERP]:
            if tmp_serie[user_conf_schema.SERIE] == serie_name:
                serie = tmp_serie
                break
        if not serie :
            self._logger.error('The serie "%s" does not exists' % (serie_name))
            sys.exit(1)
        
        for sp in ('server', 'addons', 'web'):
            try:
                url = oe_conf.get(sp, {}).get(schema.URL, serie[sp])
                bzr_rev = oe_conf.get(sp, {}).get(schema.BZR_REV, None)
                self.bzr_checkout(url, '%s/%s' % (self.openerp_path(), sp), bzr_rev)
            except Exception, e:
                self._logger.error(_ex('Cannot checkout from %s' % url, e))
                sys.exit(1)
        
        self.add_python_deps(serie[user_conf_schema.PYTHON_DEPENDENCIES])
        self.add_python_deps(conf[schema.PYTHON_DEPENDENCIES])
        self.get_ext_deps(self.project, conf[schema.DEPENDENCIES])
        
    def add_python_deps(self, python_deps):
        existing_names = [idep['name'] for idep in self.python_deps]
        for dep in python_deps:
            if dep['name'] in existing_names:
                existing_dep = [idep for idep in self.python_deps if idep['name'] == dep['name']][0]
                self._logger.warning(("Dependency %s%s is hidden by %s%s and will ignored" +
                                      "") % (dep[oebuild_conf_schema.NAME], dep.get(oebuild_conf_schema.SPECIFIER, ''),
                                             existing_dep[oebuild_conf_schema.NAME], existing_dep.get(oebuild_conf_schema.SPECIFIER, '')))
                continue
            self.python_deps.append(dep)
        
    def get_ext_deps(self, from_project, deps, deps_mapping=None):
        if not deps_mapping:
            deps_mapping = {}
        
        for dep in deps:
            if dep[schema.NAME] in deps_mapping.keys() :
                src_top = deps_mapping[dep[schema.NAME]][1][schema.SOURCE]
                src_new = dep[schema.SOURCE]
                reason = None
                if src_new[schema.SCM] != src_top[schema.SCM]:
                    reason = 'SCM'
                elif src_new[schema.URL] != src_top[schema.URL]:
                    reason = 'URL'
                elif src_new[schema.SCM] == schema.SCM_BZR and src_new[schema.BZR_REV] != src_top[schema.BZR_REV]:
                    reason = 'bazaar revision'
                elif src_new[schema.SCM] == schema.SCM_GIT and src_new[schema.GIT_BRANCH] != src_top[schema.GIT_BRANCH]:
                    reason = 'git branch' 
                if reason: 
                    self._logger.warning(("Dependency %s from %s is hidden by a %s dependency which use another %s and will ignored" +
                                    "") % (dep[schema.NAME], from_project, 
                                           deps_mapping[dep[schema.NAME]][0], reason))
                continue
    
            source = dep[schema.SOURCE]
            deps_mapping[dep[schema.NAME]] = (from_project, dep)
            destination = '%s/%s' % (self.deps_path().rstrip('/'), dep.get(schema.DESTINATION, dep[schema.NAME]))
            
            if source[schema.SCM] == schema.SCM_BZR:
                try:
                    self.bzr_checkout(source[schema.URL], destination, source.get(schema.BZR_REV, None))
                except Exception, e:
                    self._logger.error(_ex('Cannot checkout from %s' % source[schema.URL], e))
                    sys.exit(1)
                try:
                    subconf = self.oebuild_conf_parser.load_transitive_oebuild_config_file(destination.rstrip('/'), self.user_conf[user_conf_schema.CONF_FILES])
                    self.get_ext_deps(subconf[schema.PROJECT], subconf[schema.DEPENDENCIES], deps_mapping)
                except IgnoreSubConf:
                    pass
            elif source[schema.SCM] == schema.SCM_GIT:
                try:
                    self.git_checkout(source[schema.URL], destination, source.get(schema.GIT_BRANCH, None))
                except Exception, e:
                    self._logger.error(_ex('Cannot checkout from %s' % source[schema.URL], e))
                    sys.exit(1)
                try:
                    subconf = self.oebuild_conf_parser.load_transitive_oebuild_config_file(destination.rstrip('/'), self.user_conf[user_conf_schema.CONF_FILES])
                    self.get_ext_deps(subconf[schema.PROJECT], subconf[schema.DEPENDENCIES], deps_mapping)
                except IgnoreSubConf:
                    pass
            elif source[schema.SCM] == schema.SCM_LOCAL:
                try:
                    self.local_copy(source[schema.URL], destination)
                except Exception, e:
                    self._logger.error(_ex('Cannot copy from %s' % source[schema.URL], e))
                    sys.exit(1)
                try:
                    subconf = self.oebuild_conf_parser.load_transitive_oebuild_config_file(destination.rstrip('/'), self.user_conf[user_conf_schema.CONF_FILES])
                    self.get_ext_deps(subconf[schema.PROJECT], subconf[schema.DEPENDENCIES], deps_mapping)
                except IgnoreSubConf:
                    pass
            addons_path = dep.get(schema.DESTINATION, dep[schema.NAME])
            if dep.get(schema.ADDONS_PATH, False):
                addons_path = '%s/%s' % (addons_path, dep[schema.ADDONS_PATH].rstrip('/'))
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
                local_revno = local.revision_id_to_revno(local_tree.last_revision())
                if revno == local_revno:
                    self._logger.info('%s : Up-to-date from %s (revno : %s)' % (destination, source, local_revno))
                    return
                else:
                    shutil.rmtree(destination)
            except NotBranchError:
                shutil.rmtree(destination)
    
        if not os.path.exists(destination):
            os.makedirs(destination)
    
        self._logger.info('%s : Checkout from %s (revno : %s)...' % (destination, source, revno))
        remote.create_checkout(destination, remote.get_rev_id(revno), True, accelerator_tree)
    
    def git_checkout(self, source, destination, branch=None):
        if os.path.exists(destination):
            try:
                local = Repo(destination)
                self._logger.info('%s : Pull from %s...' % (destination, source))
                local.remotes.origin.pull()
                if branch:
                    self._logger.info('%s : Checkout branch %s...' % (destination, branch))
                    local.git.checkout(branch)
                return
            except InvalidGitRepositoryError:
                shutil.rmtree(destination)
             
        os.makedirs(destination)  
        self._logger.info('%s : Clone from %s...' % (destination, source))
        local = Repo.clone_from(source, destination)
        if branch:
            self._logger.info('%s : Checkout branch %s...' % (destination, branch))
            local.git.checkout(branch)
    
    def local_copy(self, source, destination):
        self._logger.info('%s : Copy from %s...' % (destination, source))
        shutil.rmtree(destination)
        os.mkdir(destination)
        for module in [m for m in os.listdir(source) if (os.path.isdir(os.path.join(source, m)) 
                                                           and m[:1] != '.')]:
            shutil.copytree(os.path.join(source, module), os.path.join(destination, module))
        for module in [m for m in os.listdir(source) if (os.path.isfile(os.path.join(source, m))
                                                           and m[:7] == 'oebuild')
                                                           and m[-5:] == '.conf']:
            shutil.copy2(os.path.join(source, module), os.path.join(destination, module))
                        
    def call_command(self, command, log_in=True, log_out=True, log_err=True, parse_log=True, register_pid=None, parse_tests=False):
        if log_in : 
            self._logger.info(command)
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
                self._logger.error(err)
            if log_out and out:
                self._logger.info(out)
            return (out, err)
        else:
            test_ok = True
            while True:
                line = process.stdout.readline()
                if line and len(line.rstrip()) > 0:
                    match = LOG_PARSER.search(line.rstrip())
                    if match and len(match.groups()) == 3:
                        print '%s %s %s' % (match.group(1), COLORIZED(match.group(2), match.group(2)), match.group(3))
                        if parse_tests and match.group(2) == 'ERROR':
                            test_ok = False
                    else:
                        print line.rstrip()
                elif not line:
                    break
            if parse_tests:
                print '\n' + (COLORIZED('DEBUG', 'OpenERP Test result: ') + (COLORIZED('INFO', 'SUCCESS') if test_ok else COLORIZED('ERROR', 'FAILED')))
            return (None, None)

if __name__ == "__main__":
    arg_parser = OEArgumentParser()
    Autobuild(arg_parser)
