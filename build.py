import os
import subprocess
import sys
import shutil
import venv
from src.constants import *

# Define paths and script name
script_name = MAINSCRIPTPATH
icon_path = os.path.join(DATAFILESPATH, 'pyDatalink_icon.ico')
output_directory = PROJECTPATH
requirements_file = 'requirements.txt'
spec_file = APPNAME + ".spec"
venv_dir = 'venv'



print("Create a virtual environment")
venv.create(venv_dir, with_pip=True)

print("Activate virtual environment")
activate_script = os.path.join(venv_dir, 'Scripts', 'activate') if sys.platform == 'win32' else os.path.join(venv_dir, 'bin', 'activate')

print("Install required python packages")
subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', requirements_file])

print("Create the executable")
pyinstaller_command = [
    'pyinstaller',
    '--name=' + APPNAME,
    '--onefile',
    '--icon=' + icon_path,
    '--distpath=' + output_directory,
    '--clean',
    '--noconfirm',
    "--noconsole",
    "--add-data=" + DATAFILESPATH +";data",
    script_name
]

status = subprocess.run(pyinstaller_command)

if os.path.exists('build'):
    shutil.rmtree('build')
# if os.path.exists(spec_file):
#     os.remove(spec_file)

if sys.platform == 'win32':
    deactivate_script = os.path.join(venv_dir, 'Scripts', 'deactivate.bat')
else:
    deactivate_script = os.path.join(venv_dir, 'bin', 'deactivate')


subprocess.run(deactivate_script, shell=True)


shutil.rmtree(venv_dir)
if status.returncode == 0 :
    print("Build completed successfully!")
else :
    print("Error while building the project")
