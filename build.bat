REM build python wheel on a windows platform
del dist\*.whl
del dist\*.tar.gz
del installers\linux\*.whl
del installers\windows\*.whl
poetry -vvv build
copy dist\*.whl installers\linux
copy dist\*.whl installers\windows



