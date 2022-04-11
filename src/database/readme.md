root/src/database

This folder contains utilities for database interactions.

**construct_dataset.py**: Constructs the database with specific tables

**db_action.py**: A simple class that represents save/load actions for the database

**db_connection.py**: Houses a convenience function for easy, modular access to the database

**db_file_backup.py**: Handles operations for dated backup data files (i.e, raw RefactoringMiner output files)

**populate_db_all_repositories**: Configurable, callable file to load/save data for specific tables of specific projects

**db_populator_manager**.py: An interface used by populate_db_all_repositories

**repo_version_walker**: Houses classes to ease repository cloning, access, and version walking