@echo off
(
echo Launching the application.
echo It may take several seconds for the application to start up.
echo To shutdown the application close the browser window, select X in corner, then close the black server app window, select X in corner.
) > message.txt
msg * < message.txt
del message.txt
retirement_finances.exe