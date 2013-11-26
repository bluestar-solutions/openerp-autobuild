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
import re

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

# Sequences to get colored ouput
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"

COLORS = {
    'DEBUG': WHITE,
    'INFO': GREEN,
    'WARNING': YELLOW,
    'ERROR': RED,
    'CRITICAL': MAGENTA,
    'TEST': BLUE,
}

COLORIZED = lambda levelname, expression: COLOR_SEQ % (30 + COLORS[levelname]) + expression + RESET_SEQ

LOG_PARSER = re.compile(r'(^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} \d*) (%s) (.*$)' % ('|'.join(COLORS.keys())))

def _ex(message, e):
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
         
class ColoredFormatter(logging.Formatter):
    def __init__(self, msg, use_color=True):
        logging.Formatter.__init__(self, msg)
        self.use_color = use_color
 
    def format(self, record):
        levelname = record.levelname
        if self.use_color and levelname in COLORS:
            levelname_color = COLORIZED(levelname, levelname)
            record.levelname = levelname_color
        return logging.Formatter.format(self, record)
     
class ColoredLogger(logging.Logger):
    def __init__(self, name):
        logging.Logger.__init__(self, name, logging.DEBUG)                
  
        fmt = ColoredFormatter('%(asctime)s %(process)d %(levelname)s ? %(module)s: %(message)s')
          
        h1 = logging.StreamHandler(sys.stdout)
        h1.setFormatter(fmt)
        f1 = SingleLevelFilter(logging.INFO, False)
        h1.addFilter(f1)
        self.addHandler(h1)
          
        h2 = logging.StreamHandler(sys.stderr)
        h2.setFormatter(fmt)
        f2 = SingleLevelFilter(logging.INFO, True)
        h2.addFilter(f2)
        self.addHandler(h2)
  
logging.setLoggerClass(ColoredLogger)
