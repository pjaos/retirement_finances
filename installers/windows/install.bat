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

REM Ensure we have pipx installed
python -m pip install pipx
if  errorlevel 1 goto CMD_ERROR

REM Ensure the path is set to reach application installed with pipx
python -m pipx ensurepath
if  errorlevel 1 goto CMD_ERROR

REM Install the retirement finances app via pipx, this may take a while...
python -m pipx install installers/retirement_finances-3.7-py3-none-any.whl
if  errorlevel 1 goto CMD_ERROR

exit /b 0

:CMD_ERROR
REM The last command failed. Please try again.
pause
exit /b 1

:NO_PYTHON_ERROR
REM Python not installed. Install Python and try again.
REM The python command below should allow the user to start the Windows Python installer.
REM Ensure you install python 3.12
python
pause
exit /b 2

:EOF