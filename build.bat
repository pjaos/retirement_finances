REM build python wheel on a windows platform
REM del dist\*.whl
REM del dist\*.tar.gz
REM del installers\windows\*.whl
REM poetry -vvv build
REM copy dist\*.whl installers\windows

del /Q windows_installer\windows\*.exe
del /Q  windows_installer/*.exe
pyinstaller --distpath windows_installer/ --workpath windows_installer/ retirement_finances.spec
"C:\Program Files (x86)\Inno Setup 6\iscc.exe" windows_installer/retirement_finances.iss




