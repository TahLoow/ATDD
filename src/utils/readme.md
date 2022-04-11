root/src/utils

This folder provides frequently used utilities around the project

**version_styles.py**: Describes two ways to interpret "versions" from our projects: By git tags or by N-day time intervals. This research only explored the former. 

**project.py**: Class that houses all information related to a project (Git links, Jira links, local repo paths, database
    queries, etc)

**shell_interface.py:** Command-Line Interface functions for specific third-party tools (Designite, RefMiner, Weka, Git, etc)

**top_level_paths**: Variable references to top-level paths like root/src, root/database, etc.