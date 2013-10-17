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
import oebuild_logger
from settings_parser import oebuild_conf_schema as schema
from settings_parser import oebuild_conf_schema_1_7
from settings_parser import oebuild_conf_schema_1_8
import textwrap
import dialogs
from oebuild_logger import __ex

logger = oebuild_logger.getLogger()

VERSION = '1.8'
SUPPORTED_VERSIONS = ('1.7', '1.8')
DEFAULT_CONF_FILENAME = 'oebuild.conf'
CUSTOM_CONF_FILENAME = 'oebuild-%s.conf'
DEPRECATED_FILES = ('.project-dependencies',)

for dfile in DEPRECATED_FILES:
    if os.path.exists(dfile):
        logger.warning('File %s is deprecated, you can remove it from the project' % dfile)
        
class IgnoreSubConf(Exception):
    pass

def load_oebuild_config_file(conf_file_list):   
    if not (os.path.exists(DEFAULT_CONF_FILENAME) and os.path.isfile(DEFAULT_CONF_FILENAME)):
        logger.error('The project configuration does not exist : %s' % DEFAULT_CONF_FILENAME)
        sys.exit(1)
        
    conf = None
    with open(DEFAULT_CONF_FILENAME, "r") as source_file:
        try:
            conf = json.load(source_file)
        except ValueError, e:
            logger.error(__ex('%s is not JSON valid' % DEFAULT_CONF_FILENAME), e)
            sys.exit(1)
            
    if conf[schema.OEBUILD_VERSION] not in SUPPORTED_VERSIONS:
        logger.error(('The project configuration file is in version %s, openerp-autobuild is ' +
                      'in version %s and support only versions %s for configuration file') % 
                     (conf[schema.OEBUILD_VERSION], VERSION, SUPPORTED_VERSIONS))
        sys.exit(1)
            
    try:
        if conf[schema.OEBUILD_VERSION] == '1.7':
            jsonschema.validate(conf, oebuild_conf_schema_1_7.OEBUILD_SCHEMA)
        else:
            jsonschema.validate(conf, oebuild_conf_schema_1_8.OEBUILD_SCHEMA)
    except Exception, e:
        logger.error(__ex('%s is not a valid configuration file' % DEFAULT_CONF_FILENAME, e))
        sys.exit(1)
        
    for conf_name in conf_file_list:
        conf_file = CUSTOM_CONF_FILENAME % conf_name
        if os.path.exists(conf_file) and os.path.isfile(conf_file):
            conf = load_alternate_config_file(conf, conf_file) 
        
    return conf

def load_alternate_config_file(conf, conf_file):  
    conf2 = None
    with open(conf_file, "r") as source_file:
        try:
            conf2 = json.load(source_file)
        except ValueError, error:
            logger.error('%s is not JSON valid : %s' % (conf_file, error))
            sys.exit(1)
            
    if conf2[schema.OEBUILD_VERSION] != conf[schema.OEBUILD_VERSION]:
        logger.error(('The oebuild version of the alternate configuration file %s '+
                      'cannot be different from the default configuration file') % conf_file)
        sys.exit(1)
    if conf2[schema.PROJECT] != conf[schema.PROJECT]:
        logger.error(('The project name of the alternate configuration file %s '+
                      'cannot be different from the default configuration file') % conf_file)
        sys.exit(1)
    if conf2[schema.OPENERP][schema.SERIE] != conf[schema.OPENERP][schema.SERIE]:
        logger.error(('The openerp serie of the alternate configuration file %s '+
                      'cannot be different from the default configuration file') % conf_file)
        sys.exit(1)
            
    try:
        if conf2[schema.OEBUILD_VERSION] == '1.7':
            jsonschema.validate(conf2, oebuild_conf_schema_1_7.OEBUILD_SCHEMA)
        else:
            jsonschema.validate(conf2, oebuild_conf_schema_1_8.OEBUILD_SCHEMA)
    except Exception, error:
        logger.error('%s is not a valid configuration file : %s' % (conf_file, error))
        sys.exit(1)
        
    for componant in ['server', 'addons', 'web']:
        if componant in conf2[schema.OPENERP]:
            conf[schema.OPENERP][componant].update(conf2[schema.OPENERP][componant])
    
    for dep2 in conf2[schema.DEPENDENCIES]:
        for dep in conf[schema.DEPENDENCIES]:
            if dep[schema.NAME] == dep2[schema.NAME]:
                dep.update(dep2)
        
    return conf

def load_subconfig_file_list(conf_file_path, conf_file_list):
    conf_file = '%s/%s' % (conf_file_path, DEFAULT_CONF_FILENAME)
    if not (os.path.exists(conf_file) and os.path.isfile(conf_file)):
        # Probably not an oebuild project
        logger.info('The project configuration does not exist : %s' % conf_file)
        raise IgnoreSubConf()
    
    conf = load_subconfig_file(conf_file)
    
    for conf_name in conf_file_list:
        conf_file = '%s/%s' % (conf_file_path, CUSTOM_CONF_FILENAME % conf_name)
        if os.path.exists(conf_file) and os.path.isfile(conf_file):
            try:
                conf2 = load_subconfig_file(conf_file)
                for dep2 in conf2[schema.DEPENDENCIES]:
                    for dep in conf[schema.DEPENDENCIES]:
                        if dep[schema.NAME] == dep2[schema.NAME]:
                            dep.update(dep2)
            except IgnoreSubConf:
                pass
    return conf

def load_subconfig_file(conf_file):
    with open(conf_file, "r") as source_file:
        try:
            conf = json.load(source_file)
        except ValueError, error:
            logger.warning('%s will be ignored because it is not a valid JSON file : %s' % (conf_file, error))
            raise IgnoreSubConf()

    if conf[schema.OEBUILD_VERSION] not in SUPPORTED_VERSIONS:
        logger.warning(('%s will be ignored because this version is not supported : %s. '+
                        'openerp-autobuild version %s supports only those version : %s')\
                       % (conf_file, conf[schema.OEBUILD_VERSION], VERSION, SUPPORTED_VERSIONS))
        raise IgnoreSubConf()

    try:
        if conf[schema.OEBUILD_VERSION] == '1.7':
            jsonschema.validate(conf, oebuild_conf_schema_1_7.OEBUILD_SCHEMA)
        else:
            jsonschema.validate(conf, oebuild_conf_schema_1_8.OEBUILD_SCHEMA)
    except Exception, e:
        logger.warning(__ex('%s will be ignored because it is not a valid configuration file' % conf_file), e)
        raise IgnoreSubConf()
        
    return conf

def create_oebuild_config_file(default_serie):      
    overwrite = "no"
    if os.path.exists(DEFAULT_CONF_FILENAME):
        overwrite = dialogs.query_yes_no("%s file already exists, overwrite it with default one ?" % DEFAULT_CONF_FILENAME, overwrite)   
    if os.path.exists(DEFAULT_CONF_FILENAME) and overwrite == "no":
        return
        
    with open(DEFAULT_CONF_FILENAME,'w') as f:     
        f.write(textwrap.dedent('''\
            {
                "oebuild-version": "%s",
                "project": "%s",
                "openerp": {
                    "serie": "%s"
                },
                "dependencies": []
            }
            
            ''' % (VERSION, os.getcwd().split('/')[-1], default_serie)))
