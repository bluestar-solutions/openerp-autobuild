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
import sys
import json
import jsonschema
from oebuild_logger import _ex, logging
from settings_parser.schema import oebuild_conf_schema as schema
import textwrap
import dialogs
import params
import re

class IgnoreSubConf(Exception):
    pass

class OEBuildConfParser():

    _logger = logging.getLogger(__name__)
    
    def __init__(self):
        for dfile in params.DEPRECATED_FILES:
            if os.path.exists(dfile):
                self._logger.warning('File %s is deprecated, you can remove it from the project' % dfile)
            
    def _load_file(self, file_name, strict_mode=True, alt_schema=False):
        conf = None
        with open(file_name, "r") as source_file:
            try:
                conf = json.load(source_file)
            except ValueError, e:
                if strict_mode:
                    self._logger.error(_ex('%s is not JSON valid' % file_name, e))
                    sys.exit(1)
                else:
                    self._logger.warning(_ex('%s is not JSON valid and will be ignored' % file_name, e))
                    raise IgnoreSubConf()
          
        if conf.get(schema.OEBUILD_VERSION, None) != params.VERSION:
            conf = self._update_file(conf.get(schema.OEBUILD_VERSION, None), file_name, alt_schema)
        self._validate_conf(conf, file_name, strict_mode, alt_schema)  
        
        return conf

    def _load_alt_file(self, source_conf, file_name):       
        conf = self._load_file(file_name, strict_mode=False, alt_schema=True)
        new_conf = dict(source_conf)
        
        for componant in ['server', 'addons', 'web']:
            if componant in conf[schema.OPENERP]:
                new_conf[schema.OPENERP][componant].update(conf[schema.OPENERP][componant])
        
        for dep2 in conf[schema.DEPENDENCIES]:
            for dep in new_conf[schema.DEPENDENCIES]:
                if dep[schema.NAME] == dep2[schema.NAME]:
                    dep.update(dep2)
                    
        return new_conf
        
    def _validate_conf(self, conf, file_name, strict_mode=True, alt_schema=False):
        try:
            jsonschema.validate(conf, schema.OEBUILD_ALT_SCHEMA if alt_schema else schema.OEBUILD_SCHEMA)
        except Exception, e:
            if strict_mode:
                self._logger.error(_ex('%s is not a valid configuration file' % file_name, e))
                sys.exit(1)
            else:
                self._logger.warning(_ex('%s will be ignored because it is not a valid configuration file' % file_name, e))
                raise IgnoreSubConf()
        
    def load_oebuild_config_file(self, conf_file_list):   
        if not (os.path.exists(params.DEFAULT_CONF_FILENAME) and os.path.isfile(params.DEFAULT_CONF_FILENAME)):
            self._logger.error('The project configuration does not exist : %s' % params.DEFAULT_CONF_FILENAME)
            sys.exit(1)
            
        conf = self._load_file(params.DEFAULT_CONF_FILENAME)
            
        for conf_name in conf_file_list:
            conf_file_name = params.CUSTOM_CONF_FILENAME % conf_name
            if os.path.exists(conf_file_name) and os.path.isfile(conf_file_name):
                try:
                    conf = self._load_alt_file(conf, conf_file_name)
                except IgnoreSubConf:
                    pass
            
        return conf
    
    def load_transitive_oebuild_config_file(self, conf_file_path, conf_file_list):
        conf_file = '%s/%s' % (conf_file_path, params.DEFAULT_CONF_FILENAME)
        if not (os.path.exists(conf_file) and os.path.isfile(conf_file)):
            # Probably not an oebuild project
            self._logger.info('%s : %s file not found. It is probably not a oebuild module' % (conf_file_path, params.DEFAULT_CONF_FILENAME))
            raise IgnoreSubConf()
        
        conf = self._load_file(conf_file)
                
        for conf_name in conf_file_list:
            conf_file = '%s/%s' % (conf_file_path, params.CUSTOM_CONF_FILENAME % conf_name)
            if os.path.exists(conf_file) and os.path.isfile(conf_file):
                try:
                    conf = self._load_alt_file(conf, conf_file)
                except IgnoreSubConf:
                    pass
                
        return conf
    
#     def load_subconfig_file(self, conf_file):
#         with open(conf_file, "r") as source_file:
#             try:
#                 conf = json.load(source_file)
#             except ValueError, error:
#                 self._logger.warning('%s will be ignored because it is not a valid JSON file : %s' % (conf_file, error))
#                 raise IgnoreSubConf()
#     
#         if conf[schema.OEBUILD_VERSION] not in params.SUPPORTED_VERSIONS:
#             self._logger.warning(('%s will be ignored because this version is not supported : %s. '+
#                                   'openerp-autobuild version %s supports only those version : %s')\
#                                  % (conf_file, conf[schema.OEBUILD_VERSION], params.VERSION, params.SUPPORTED_VERSIONS))
#             raise IgnoreSubConf()
#         raise IgnoreSubConf()
#     
#         try:
#             jsonschema.validate(conf, schema.OEBUILD_SCHEMA)
#         except Exception, e:
#             self._logger.warning(_ex('%s will be ignored because it is not a valid configuration file' % conf_file), e)
#             raise IgnoreSubConf()
#             
#         return conf
    
    def create_oebuild_config_file(self, default_serie):      
        overwrite = "no"
        if os.path.exists(params.DEFAULT_CONF_FILENAME):
            overwrite = dialogs.query_yes_no("%s file already exists, overwrite it with default one ?" % params.DEFAULT_CONF_FILENAME, overwrite)   
        if os.path.exists(params.DEFAULT_CONF_FILENAME) and overwrite == "no":
            return
            
        with open(params.DEFAULT_CONF_FILENAME,'w') as f:     
            f.write(textwrap.dedent('''\
                {
                    "oebuild-version": "%s",
                    "project": "%s",
                    "openerp": {
                        "serie": "%s"
                    },
                    "dependencies": []
                }
                
                ''' % (params.VERSION, os.getcwd().split('/')[-1], default_serie)))
            
    def _update_file(self, version_from, file_name, alt_schema=False):
        self._logger.warning(('%s is in version %s and openerp-autobuild is in version %s') % 
                             (file_name, version_from, params.VERSION))
        
        updated_fname = file_name + ".updated"
        with open(file_name, "r") as source_file:
            with open(updated_fname, "w+") as updated_file:
                content = source_file.read()
                regs = self.UPDATE_ALT_FROM[version_from] if alt_schema else self.UPDATE_FROM[version_from]
                for pattern, replace in regs:
                    content = re.sub(pattern, replace, content)
                updated_file.write(content)
                
        answer = dialogs.ANSWER_NO
        if len(file_name.split('/')) == 1:
            answer = dialogs.query_yes_no("Do you want to replace the project configuration files by the updated version " + 
                                          "(otherwise the updated versions will be saved to new files) ?", default=dialogs.ANSWER_NO)
        if answer == dialogs.ANSWER_YES:
            os.rename(updated_fname, file_name)
            updated_fname = file_name
            self._logger.info('%s has been updated to version 1.8' % file_name)
        else:
            self._logger.info('An updated version of %s will be used and stored in %s' % (file_name, updated_fname))
            
        with open(updated_fname, "r") as updated_file:
            return json.load(updated_file)

    # 
    update_version = lambda v_from, v_to: (r'("oebuild-version"\s*:\s*)"%s"' % v_from, r'\1"%s"' % v_to)
    remove_param = lambda p_name: (r'"%s"\s*:\s*".*"\s*,?\s*\n?' % p_name, r'')
    
    UPDATE_FROM =  {
        "1.7": [update_version("1.7", "1.8"),
                (r'(\n?)(\s*)("dependencies"\s*:)', r'\1\2"python-dependencies": [],\1\2\3')]
    }
    
    UPDATE_ALT_FROM =  {
        "1.7": [update_version("1.7", "1.8"),
                remove_param("project"),
                remove_param("serie")]
    }
