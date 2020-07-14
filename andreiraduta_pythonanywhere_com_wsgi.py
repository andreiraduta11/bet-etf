# This file contains the WSGI configuration required to serve up your
# web application at http://andreiraduta.pythonanywhere.com
# It works by setting the variable 'application' to a WSGI handler of some
# description.

# +++++++++++ GENERAL DEBUGGING TIPS +++++++++++
# getting imports and sys.path right can be fiddly!
# We've tried to collect some general tips here:
# https://help.pythonanywhere.com/pages/DebuggingImportError


# +++++++++++ VIRTUALENV +++++++++++
# If you want to use a virtualenv, set its path on the web app setup tab.
# Then come back here and import your application object as per the
# instructions below


# +++++++++++ CUSTOM WSGI +++++++++++
# If you have a WSGI file that you want to serve using PythonAnywhere, perhaps
# in your home directory under version control, then use something like this:
from sys import path

application_path = '/home/andreiraduta/bet-etf'
if application_path not in path:
    path.append(application_path)

from application import application
application = application.server
