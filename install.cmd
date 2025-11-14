@echo off
setlocal

:: Check if config.yaml exists
if not exist "config\config.yml" (
    echo config.yml not found, copying config.yml.dist...
    copy "config\config.yml.dist" "config\config.yml"

    echo Please, edit your config.yml file, save it, and close notepad to continue
    echo Mandatory key: dcs.saved_games
    :: Open config.yml in Notepad
    notepad "config\config.yml"
) else (
    echo config.yml found, reusing it.
)


:: Run poetry install
call poetry install --only main

echo this console should be closed automatically in 5 seconds
timeout /t 5