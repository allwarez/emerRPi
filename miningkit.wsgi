activate_this = '/home/kit/miningkit/venv/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import sys
sys.path.insert(0, '/home/kit/miningkit')

from server import app as application
