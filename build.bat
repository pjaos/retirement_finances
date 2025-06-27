del /Q windows_installer\*.exe
del /Q installers\windows\*.exe
pyinstaller --distpath windows_installer/ --workpath windows_installer/ retirement_finances.spec
"C:\Program Files (x86)\Inno Setup 6\iscc.exe" windows_installer/retirement_finances.iss




