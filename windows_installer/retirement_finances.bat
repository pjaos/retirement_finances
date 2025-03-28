REM Launching the application. It may take several seconds for the application to start up.
REM To shutdown the application close the browser window (select X in corner), then close this window (select X in corner).

python -m poetry run python -c "import retirement_finances.retirement_finances; retirement_finances.retirement_finances.main()" %*