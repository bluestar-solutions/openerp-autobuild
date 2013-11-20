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

import logging, sys

def ex(message, e):
    if hasattr(e, '__module__'):
        return '%s: [%s: %s]' % (message, e.__module__ + "." + e.__class__.__name__, e)
    return '%s: [%s: %s]' % (message, e.__class__.__name__, e)

class SingleLevelFilter(logging.Filter):
    def __init__(self, passlevel, reject):
        self.passlevel = passlevel
        self.reject = reject

    def filter(self, record):
        if self.reject:
            return (record.levelno != self.passlevel)
        else:
            return (record.levelno == self.passlevel)
        
class Logger:
    
    class __Logger:
        
        def __init__(self):
            self.logger = logging.getLogger()
            
            fmt = logging.Formatter('%(asctime)s %(process)d %(levelname)s ? %(module)s: %(message)s')
            
            h1 = logging.StreamHandler(sys.stdout)
            h1.setFormatter(fmt)
            f1 = SingleLevelFilter(logging.INFO, False)
            h1.addFilter(f1)
            self.logger.addHandler(h1)
            
            h2 = logging.StreamHandler(sys.stderr)
            h2.setFormatter(fmt)
            f2 = SingleLevelFilter(logging.INFO, True)
            h2.addFilter(f2)
            self.logger.addHandler(h2)
            
            self.logger.setLevel(logging.DEBUG)
            
        def getLogger(self):
            return self.logger
    
    __instance = None
    
    def __init__(self):
        if Logger.__instance is None:
            Logger.__instance = Logger.__Logger()
    
    def __getattr__(self, attr):
        return getattr(self.__instance, attr)
    
    def __setattr__(self, attr, val):
        return setattr(self.__instance, attr, val)

def getLogger():
    return Logger().getLogger()