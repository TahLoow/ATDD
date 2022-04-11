"""
Attempts to create database tables. If the database already exists, prompts user to delete database, and quits
"""
import os
import sqlite3

from internal_configs import all_refactoring_types
from .db_connection import DB_ABSPATH

all_refactoring_columns = ', '.join(f'"{w}"' for w in all_refactoring_types)


def create_tables(conn):
    """
    Creates all database tables
    :param conn: the connection to the database
    """
    create_projects = """
        CREATE TABLE PROJECTS (project_name, git_link, jira_link);
    """
    create_ref_miner = """
        CREATE TABLE REFACTORING_MINER (project_name, commit_hash, 
            refactoring_type, refactoring_detail, refactoring_path, package);
    """
    create_git_commits = """
        CREATE TABLE GIT_COMMITS(project_name, commit_hash, commit_message, 
            author, author_date, author_timezone, committer, committer_date, 
            committer_timezone, in_main_branch, merge, parents);
    """
    create_git_commits_changes = """
        CREATE TABLE GIT_COMMITS_CHANGES(project_name, commit_hash, old_path, 
            new_path, change_type, diff, lines_added, lines_removed, n_loc, 
            complexity, token_count, methods);
    """

    # create_jira_issues = """
    #     CREATE TABLE JIRA_ISSUES (project_name, "key", creation_date,
    #         resolution_date, update_date, due_date, resolution, type, priority,
    #         fix_versions, versions, time_spent DECIMAL, aggregated_time_spent,
    #         time_estimate, time_original_estimate, aggregate_time_estimate,
    #         progress_percent, component_name, component_description, description,
    #         summary, watch_count, votes, labels, creator_name, creator_active,
    #         assignee, reporter);
    # """

    create_jira_issues = """
        CREATE TABLE JIRA_ISSUES (project_name, key, creation_date, resolution_date, update_date, due_date, resolution, 
            type, priority, fix_versions, versions, time_spent DECIMAL, aggregated_time_spent, time_estimate, 
            aggregated_time_estimate, progress_percent, description, summary, watch_count, votes, creator_name, 
            assignee, reporter);
    """

    create_git_commit_release = """
        CREATE TABLE GIT_COMMIT_RELEASE (project_name, commit_hash, date, version);
    """

    create_git_commit_jira = """
        CREATE TABLE GIT_COMMIT_JIRA (key, commit_hash);
    """

    create_project_versions = """
        CREATE TABLE PROJECT_VERSIONS (project_name, version, commit_hash, author_date, previous_version)
    """

    create_designite_smells = """
        CREATE TABLE DESIGNITE_SMELLS (project_name, version, package, smell, cause)    
    """

    create_static_metrics = """
        CREATE TABLE STATIC_METRICS (project_name, package, version, pkg_files NUMERIC, pkg_loc NUMERIC, 
            pkg_tokens NUMERIC, pkg_cc NUMERIC, pkg_average_loc NUMERIC, pkg_average_cc NUMERIC, 
            pkg_average_tokens NUMERIC)
    """

    # create_designite_smells_wide = """
    #     CREATE TABLE DESIGNITE_SMELLS_WIDE (project_name, version, package, smell, cause);
    # """

    # create_ref_pivoted = """
    #     CREATE TABLE REFACTORING_MINER_WIDE ("project_name", "commit_hash", "refactoring_path", "release",
    #         "package", "add_attribute_annotation", "add_attribute_modifier", "add_class_annotation",
    #         "add_method_annotation", "add_method_modifier", "add_parameter", "add_parameter_annotation",
    #         "add_parameter_modifier", "add_thrown_exception_type", "add_variable_annotation", "add_variable_modifier",
    #         "change_attribute_access_modifier", "change_attribute_type", "change_method_access_modifier",
    #         "change_package", "change_parameter_type", "change_return_type", "change_thrown_exception_type",
    #         "change_variable_type", "encapsulate_attribute", "extract_and_move_method", "extract_attribute",
    #         "extract_class", "extract_interface", "extract_method", "extract_subclass", "extract_superclass",
    #         "extract_variable", "inline_method", "inline_variable", "merge_attribute", "merge_parameter",
    #         "merge_variable", "modify_attribute_annotation", "modify_class_annotation", "modify_method_annotation",
    #         "modify_parameter_annotation", "modify_variable_annotation", "move_and_inline_method",
    #         "move_and_rename_attribute", "move_and_rename_class", "move_and_rename_method", "move_attribute",
    #         "move_class", "move_method", "move_source_folder", "parameterize_attribute", "parameterize_variable",
    #         "pull_up_attribute", "pull_up_method", "push_down_attribute", "push_down_method",
    #         "remove_attribute_annotation", "remove_attribute_modifier", "remove_class_annotation",
    #         "remove_method_annotation", "remove_method_modifier", "remove_parameter", "remove_parameter_annotation",
    #         "remove_parameter_modifier", "remove_thrown_exception_type", "remove_variable_annotation",
    #         "remove_variable_modifier", "rename_attribute", "rename_class", "rename_method", "rename_parameter",
    #         "rename_variable", "reorder_parameter", "replace_attribute", "replace_attribute_with_variable",
    #         "replace_variable_with_attribute", "split_attribute", "split_parameter", "split_variable");
    # """

    conn.execute(create_projects)
    conn.execute(create_ref_miner)
    conn.execute(create_git_commits)
    conn.execute(create_git_commits_changes)
    conn.execute(create_jira_issues)
    conn.execute(create_git_commit_release)
    conn.execute(create_git_commit_jira)
    conn.execute(create_designite_smells)
    conn.execute(create_static_metrics)
    conn.execute(create_project_versions)
    # conn.execute(create_ref_pivoted)
    return


def tables_in_sqlite_db(conn):
    """
    Selects all table names from the database
    :param conn: the connection to the database
    :return: List of the table names
    :rtype: list
    """
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [
        v[0] for v in cursor.fetchall()
        if v[0] != "sqlite_sequence"
    ]
    cursor.close()
    return tables

def create_atdd():
    if not os.path.isfile(DB_ABSPATH):
        with sqlite3.connect(DB_ABSPATH) as conn:
            create_tables(conn)
            print(tables_in_sqlite_db(conn))

            conn.commit()
    else:
        print('Database filename "' + DB_ABSPATH + '" already exists! Please delete.')
        quit()

    print('Done!')

if __name__ == '__main__':
    create_atdd()
