# Setup for Development
- Run/double click init.bat
    - This will create a virtual Python environment and install needed packages

- Install desired tools (Refactoring Miner 2.1.0, Designite Java)

- Configure setup in root/src/config.py
    - Correct any install paths for weka_abspath, weka_abspath, designite_abspath, ref_miner_abspath
    - Adjust designite_max_allocation if desired
  
- Open virtual_python_cmd.bat to execute any command line requests

# Usage
**Using virtual_python_cmd.bat, run "src/python main.py help" to read options for populating database**


- To generate and load new data into the database for **all** projects, for **all** tables:
    - Delete database/augmented_tdd.db and database/db_loadfiles
    - Run "python src/main.py create_db" to create an empty database/augmented_tdd.db
    - Run "python src/main.py autopopulate" to read options for populating database
    - Designite and RefactoringMiner can take several hours to process
  