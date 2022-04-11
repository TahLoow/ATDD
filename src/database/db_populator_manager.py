"""
Generates or loads db table data, based on `populate_db_all_repositories`
"""

from .db_populators.designite_smells import DesigniteSmellsPopulator
from .db_populators.git_commit_changes import GitCommitChangesPopulator
from .db_populators.git_commit_jira import GitCommitJiraPopulator
from .db_populators.git_commit_version import GitCommitReleasePopulator
from .db_populators.git_commits import GitCommitsPopulator
from .db_populators.jira_issues import JiraIssuesPopulator
from .db_populators.project_versions import ProjectVersionsPopulator
from .db_populators.projects import ProjectInfoPopulator
from .db_populators.refactoring_miner import RefMinerPopulator
from .db_populators.static_metrics import StaticMetricsPopulator

import pandas as pd
from database.db_action import DbAction
from database.repo_version_walker import RepoVersionWalker
from utils.project import Project

pd.options.display.max_colwidth = 300
# Each populator can save or loads a table's worth of project-specific information
table_populators = {
    'PROJECTS': ProjectInfoPopulator,
    'PROJECT_VERSIONS': ProjectVersionsPopulator,
    'GIT_COMMITS': GitCommitsPopulator,
    'GIT_COMMIT_VERSION': GitCommitReleasePopulator,
    'GIT_COMMIT_CHANGES': GitCommitChangesPopulator,
    'GIT_COMMIT_JIRA': GitCommitJiraPopulator,
    'JIRA_ISSUES': JiraIssuesPopulator,
    'REFACTORING_MINER': RefMinerPopulator,
    'DESIGNITE_SMELLS': DesigniteSmellsPopulator,
    'STATIC_METRICS': StaticMetricsPopulator
}


class PopulatorManager:
    """
    Does the heavy lifting in populating the database
    """

    def __init__(self):
        """
        Does the heavy lifting in populating the database
        """
        pass

    def execute(self, project, targeted_tables, db_action):
        """

        :param project: the project to be saved/loaded
        :type project: Project
        :param targeted_tables: What populators to run
        :type targeted_tables: list
        :param db_action: whether the data will be saved or loaded
        :type db_action: DbAction
        """
        requested_populators = []
        requested_versioned_populators = []

        for table_name in targeted_tables:
            populator_class = table_populators.get(table_name)
            populator = populator_class(project, db_action)

            if hasattr(populator, 'per_version_saving') and db_action.is_generate():
                requested_versioned_populators.append(populator)
            else:
                requested_populators.append(populator)

        for populator in requested_populators:
            print(populator.table_name)
            populator.execute(db_action)

        # Process versioned populators (Clone repository, )
        if len(requested_versioned_populators) > 0:
            repo_version_walker = RepoVersionWalker(project)

            for repo_state in repo_version_walker.walk():
                for populator in requested_versioned_populators:
                    print(populator.table_name)
                    populator.execute(repo_state)
