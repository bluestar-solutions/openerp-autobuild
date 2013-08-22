#!/usr/bin/env python
# coding: utf-8

import logging, sys

class SingleLevelFilter(logging.Filter):
    def __init__(self, passlevel, reject):
        self.passlevel = passlevel
        self.reject = reject

    def filter(self, record):
        if self.reject:
            return (record.levelno != self.passlevel)
        else:
            return (record.levelno == self.passlevel)
        
def getLogger():
    logger = logging.getLogger()
    
    fmt = logging.Formatter('%(asctime)s %(process)d %(levelname)s ? %(module)s: %(message)s')
    
    h1 = logging.StreamHandler(sys.stdout)
    h1.setFormatter(fmt)
    f1 = SingleLevelFilter(logging.INFO, False)
    h1.addFilter(f1)
    logger.addHandler(h1)
    
    h2 = logging.StreamHandler(sys.stderr)
    h2.setFormatter(fmt)
    f2 = SingleLevelFilter(logging.INFO, True)
    h2.addFilter(f2)
    logger.addHandler(h2)
    
    logger.setLevel(logging.DEBUG)
    
#     logger.debug("A DEBUG message")
#     logger.info("An INFO message")
#     logger.warning("A WARNING message")
#     logger.error("An ERROR message")
#     logger.critical("A CRITICAL message")
    
    return logger