REM build python wheel on a windows platform
poetry -vvv build
cp dist/*.whl installers


