activate_this = '/Users/kamillo/miningkit/venv/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import sys
sys.path.insert(0, '/Users/kamillo/miningkit')

from server import app as application
