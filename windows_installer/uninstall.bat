REM Remove the files created during installation

REM We don't check for errors on the removal of this folder as the __pycache__ folder
REM will only be present in it if the application was launched.
rd /S /Q retirement_finances

python -m poetry env remove --all
if  errorlevel 1 goto CMD_ERROR

del get-pip.py
if  errorlevel 1 goto CMD_ERROR

del poetry.lock
if  errorlevel 1 goto CMD_ERROR

exit /b 0

:CMD_ERROR
REM The last command failed. Uninstall did not complete successfully.
pause
exit /b 1


