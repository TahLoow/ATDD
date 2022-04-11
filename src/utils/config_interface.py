import os

import yaml
import json

from database.db_action import DbAction
from utils.top_level_paths import configs_directory


def get_database_configs():
    """
    This function extracts YAML declarations from configs/database_processing.yaml and converts them into
    usable objects for calling programs

    Returns the following:
        database_action: A DBAction object describing the database process (LOAD or GENERATE)
        targeted_tables: A list of strings, where each string describes one of the tables from the ATDD
        projects_to_process: A list of Project objects
    """

    all_projects = get_all_projects()

    with open(configs_directory + '/database_processing.yaml', 'r') as file:
        database_processing_declarations = yaml.safe_load(file)
        # print(json.dumps(configs_directory, indent=2))

        database_action = DbAction(database_processing_declarations['database_action'])
        targeted_tables = database_processing_declarations['targeted_tables']
        projects_to_process = {}
        for project_name in database_processing_declarations['projects_to_process']:
            try:
                projects_to_process[project_name] = all_projects[project_name]
            except KeyError:
                raise KeyError(f'{project_name} not declared in configs/projects.yaml')

    return database_action, targeted_tables, projects_to_process


def get_tool_path(desired_tool):
    """
    The calling function requests a particular tool by name. This function extracts the requested tool data from
    configs/tools.yaml, ensures that it exists, and returns the tool's data

    Returns the following:
        tool: A Dict that consists of at least {'path': <existing_path_string>}
    """
    with open(configs_directory + '/tools.yaml', 'r') as file:
        tool_declarations = yaml.safe_load(file)
        # print(json.dumps(tools_raw_data, indent=2))

    try:
        tool = tool_declarations[desired_tool]
    except KeyError:
        raise KeyError(f'{desired_tool} not declared in configs/tools.yaml')

    if not os.path.exists(tool['path']):
        raise FileNotFoundError(f'{tool["path"]} from in configs/tools.yaml does not exist')

    tool = tool_declarations[desired_tool]

    return tool


def get_all_projects(include_test=False):
    """
    This function extracts YAML declarations from configs/projects.yaml and converts them into Project objects

    Returns the following:
        all_projects: A list of Project objects
    """

    from utils.project import Project
    all_projects = {}

    with open(configs_directory + '/projects.yaml', 'r') as file:
        project_declarations = yaml.safe_load(file)
        # print(json.dumps(projects_raw_data, indent=2))

        for project_declaration in project_declarations:
            project_name = project_declaration['project_name']

            all_projects[project_name] = Project(
                github_owner=project_declaration['repo_owner'],
                repo_name=project_name,
                branch=project_declaration['repo_main_branch'],
                github_link=project_declaration['repo_link'],
                jira_link=project_declaration['jira_link']
            )

    if include_test:
        all_projects['TEST'] = Project('ME', 'TEST', 'master', 'TEST_NO_URL', 'TEST_NO_URL')

    return all_projects


if __name__ == '__main__':
    print(get_database_configs())
    # print(get_tool_path('refactoring_miner_2.1.0'))
