#!/bin/bash
# Delete old files
rm -f windows_retirement_finances.zip
rm -f linux_retirement_finances.zip
# Create password protected zip file.
zip -r windows_retirement_finances.zip windows
zip -r linux_retirement_finances.zip linux
