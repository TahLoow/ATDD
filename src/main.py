"""
Presents a method by which the sql database can be automatically populated. The projects_to_run varible selects
which projects to use, and the populators_to_run selects which tables to fill. Finally, db_action specifies whether it
will save the information to csv files, or load existing csv files into the database. Acts as a wrapper for
`db_populator_manger`
"""
import sys

from database.db_action import DbAction
from database.db_populator_manager import PopulatorManager
from utils.config_interface import get_database_configs, get_all_projects
from database.create_atdd import create_atdd


def process_projects(db_action, targeted_tables, projects):
    for project in projects:
        if project.repo_name != 'test':
            project.assert_local_repository(update_if_exists=True)

        populator_runner = PopulatorManager()
        populator_runner.execute(project, targeted_tables, db_action)


def auto_populate(specific_project=None):
    if specific_project is not None:
        all_projects = [get_all_projects()[specific_project]]
    else:
        all_projects = get_all_projects().values()

    process_projects(DbAction(DbAction.GENERATE), [
        'PROJECTS',
        'PROJECT_VERSIONS',
        'GIT_COMMITS',
        'GIT_COMMIT_VERSION',
        'GIT_COMMIT_CHANGES',
        # 'GIT_COMMIT_JIRA',
        'JIRA_ISSUES',
        'REFACTORING_MINER',
        'DESIGNITE_SMELLS',
        'STATIC_METRICS'
    ], all_projects)

    process_projects(DbAction(DbAction.LOAD), [
        'PROJECTS',
        'PROJECT_VERSIONS',
        'GIT_COMMITS',
        'GIT_COMMIT_VERSION',
        'GIT_COMMIT_CHANGES',
        # 'GIT_COMMIT_JIRA',
        'JIRA_ISSUES',
        'REFACTORING_MINER',
        'DESIGNITE_SMELLS',
        'STATIC_METRICS'
    ], all_projects)

    process_projects(DbAction(DbAction.GENERATE), ['GIT_COMMIT_JIRA'], all_projects)
    process_projects(DbAction(DbAction.LOAD), ['GIT_COMMIT_JIRA'], all_projects)


def process_by_config():
    db_action, targeted_tables, projects_to_process = get_database_configs()
    process_projects(db_action, targeted_tables, projects_to_process.values())


class CmdLineDriver:
    """ Provides an interface for populating the database through the command line"""

    def __init__(self):
        """ Provides an interface for populating the database through the command line"""
        argv = sys.argv
        n = len(argv)

        if n == 1 or argv[1] == 'help':
            self.help()
            return

        flag = argv[1]
        # cmd_args = argv[2:]  # Exclude program name and flag

        if flag == '-autopopulate':
            project = None
            try:
                project = argv[2]
            except IndexError:
                pass
            auto_populate(specific_project=project)
        elif flag == '-config':
            process_by_config()
        elif flag == 'create_db':
            create_atdd()
        else:
            self.help()

    @staticmethod
    def help():
        """
        Prints help function for the command line driver
        """
        print(
            '\n'
            'Using root/cmd.bat, execute one the following: \n'
            ' > python src/main.py -autopopulate <project>\n'
            '      - Generates and loads all table data from all projects (or a specified project name) into database\n'
            ' > python src/main.py -config\n'
            '      - WARNING: Read database_processing yaml before choosing this option\n'
            '      - Performs data operations specified in root/configs/database_processing.yaml\n'
            ' > python src/main.py -create_db\n'
            '      -Creates an empty ATDD at root/database/augmented_tdd.db'
        )


if __name__ == "__main__":
    CmdLineDriver()
