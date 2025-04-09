REM The windows installer program is executed by the Windows installer once the
REM file are copied to a Windows platform.

REM Check python is installed.
python --version
if  errorlevel 1 goto NO_PYTHON_ERROR

REM Install PIP
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
if  errorlevel 1 goto CMD_ERROR
python get-pip.py
if  errorlevel 1 goto CMD_ERROR

REM Ensure we have the latest pip version
python -m pip install --upgrade pip
if  errorlevel 1 goto CMD_ERROR

REM Install poetry
python -m pip install poetry
if  errorlevel 1 goto CMD_ERROR
python -m poetry self update
if  errorlevel 1 goto CMD_ERROR
REM Set the folder to use for the python virtual env
python -m poetry config virtualenvs.path C:\Python_Program_Files\venvs
REM This installs the shell cmd with poetry >= 2.0
python -m poetry self add poetry-plugin-shell

REM Create the python poetry env
python -m poetry lock
if  errorlevel 1 goto CMD_ERROR
python -m poetry install
if  errorlevel 1 goto CMD_ERROR

exit /b 0

:CMD_ERROR
REM The last command failed. Please try again.
pause
exit /b 1

:NO_PYTHON_ERROR
REM Python not installed. Install Python and try again.
REM The python command below should allow the user to start the Windows Python installer.
python
pause
exit /b 2

:EOF