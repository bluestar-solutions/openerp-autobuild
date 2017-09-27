import sys
from os.path import dirname

static_python_path = "%s/%s" % (dirname(__file__), 'lib')
sys.path.append(static_python_path)
