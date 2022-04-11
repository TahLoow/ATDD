root/src/database/db_populators

This folder describes "populators". Each Populator is assigned to one table in the ATDD. 
Populators describe the process to GENERATE the data and LOAD it into ATDD tables
(located in root/database/augmented_tdd.db). Some populators do not require a GENERATEd backup file because they are fast.

There are two classes of populators, described in ./populator_helpers.py:
1) **Populator**
   
   This class offers two main functions:
   - "_execute_generate", which saves a backup file of necessary data (i.e, hours worth of refactoring_miner output)
   - "_execute_load", which loads data into the database from from either a backup file or other realtime source

2) **PerVersionPopulator**
   
   This class performs similarly to Populator. PerVersionPopulators are for data that must be collected
   at version snapshops; the repo is cloned to a specific version, then all PerVersionPopulators act
   upon the version, and then the repo checks out the subsequent version and the process repeats. 
   This stops redundant cloning, improves wait time, and makes the populator easier to work with. 