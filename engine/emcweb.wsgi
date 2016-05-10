import sys

activate_this = '/var/lib/emcweb/venv/bin/activate_this.py'

if (sys.version_info > (3, 0)):
    with open(activate_this) as f:
        code = compile(f.read(), 'activate_this.py', 'exec')
        exec(code)
else:
    execfile(activate_this, dict(__file__=activate_this))

sys.path.insert(0, '/var/lib/emcweb')

from server import app as application
