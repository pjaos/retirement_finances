del /Q windows_installer\*.exe
del /Q installers\windows\*.exe
copy .\pyproject.toml .\src\retirement_finances\assets\
pyinstaller --noconfirm --clean --distpath windows_installer/dist --workpath windows_installer/build retirement_finances.spec
"C:\Program Files (x86)\Inno Setup 6\iscc.exe" windows_installer/retirement_finances.iss

