activate_this = '/var/lib/emercoin-web/venv/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import sys
sys.path.insert(0, '/var/lib/emercoin-web')

from server import app as application
