:: This builds the python wheel file in the windows folder that can be installed using the install.py file.
copy .\pyproject.toml .\src\retirement_finances\assets\
:: Use poetry command to build python wheel
poetry --output=windows --clean -vvv build
:: Delete the .tar.gz file in dist directory
del /Q windows/*.tar.gz
:: Put a copy of the install.py alongside the python wheel
copy install.py windows



