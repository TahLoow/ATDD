@echo off

if exist "env" (
    echo Env folder exists; please remove if you wish to re-init.
    rem file exists
) else (
    echo Building virtual environment for Python in ./env.
    python -m venv env
    pip install wheel
    python -m pip install --upgrade pip
	
    env\Scripts\activate
    
    python setup.py develop
    pip install -e .

    echo Virtual environment init complete
    pause
)

pause