import os

import pandas as pd
from database.db_connection import get_db_connection
from utils.rq1_helpers import standardize_refactoring_columns, standardize_smells_columns
from utils.top_level_paths import repo_directory
from utils import shell_interface
from internal_configs import all_smell_types


class Project:
    github_owner = '',
    repo_name = '',
    repo_path = '',
    branch = '',
    github_link = '',
    jira_link = '',

    _cached_sql_results = None

    def __init__(self, github_owner, repo_name, branch, github_link, jira_link=''):
        """
        Multifunction class. Can create a project, or get information for a project, assuming that it is in the database

        :param github_owner: the owner of the github repo
        :type github_owner: str
        :param repo_name: name of the repo
        :type repo_name: str
        :param branch: branch of repo
        :type branch: str
        :param github_link: url link to repo hosted on github
        :type github_link: str
        :param jira_link: url link to repo on jira, optional
        :type jira_link: str
        """
        self.github_owner = github_owner
        self.repo_name = str.lower(repo_name)
        self.repo_path = os.path.join(repo_directory, repo_name)  # No guarantee that this is path exists
        self.branch = branch
        self.github_link = github_link
        self.jira_link = jira_link

        self._cached_sql_results = {}
        
        self.use_test_db = self.repo_name == 'test'

    def dump(self):
        """
        Dumps owner, repo name, repo path, branch, github link, and jira link for project

        :return: list of information in order
        :rtype: list[str, str, str, str, str, str]
        """
        return [self.github_owner, self.repo_name, self.repo_path, self.branch, self.github_link, self.jira_link]

    def dumps(self, sep=' '):
        """
        Joins `dump` method output into string using given separator

        :param sep: separator to use to join dump list
        :type sep: str
        :return: joined dump
        :rtype: str
        """
        return sep.join(self.dump())

    def to_json(self):
        """
        Unimplemented method, currently just returns repo name

        :return: the repo name
        :rtype: str
        """
        return self.repo_name

    def assert_local_repository(self, update_if_exists=False):
        if os.path.exists(self.repo_path):
            if update_if_exists:
                shell_interface.update_repository(self.repo_path)
        else:
            shell_interface.clone_repository(self.github_link, self.repo_path)

    def get_version_history(self, order='oldest_to_newest'):
        """
        Uses database to select all versions of project

        :param order: ordering, can be "oldest_to_newest" or "newest_to_oldest"
        :type order: str
        :return: list of orderings
        :rtype: list
        """
        conn, cursor = get_db_connection(test_db=self.use_test_db)
        df = pd.read_sql_query(f'SELECT DISTINCT version FROM GIT_COMMIT_RELEASE '
                               f'WHERE project_name=\'{self.repo_name}\'', conn)
        ret_val = df['version'].tolist()
        if order == 'oldest_to_newest':
            ret_val.reverse()
        elif order == 'newest_to_oldest':
            ret_val = ret_val
        else:
            raise Exception(f'Invalid order parameter {order}')
        return ret_val

    def get_issue_times(self):
        """
        Uses database to select all jira keys and time_spent values for given project, given that there is a time_spent,
        and it is not 0

        :return: pandas dataframe of query result
        :rtype: pandas.DataFrame
        """
        conn, cursor = get_db_connection(test_db=self.use_test_db)
        return pd.read_sql_query((
            'SELECT key, time_spent '
            'FROM JIRA_ISSUES '
            'WHERE project_name=\'?\' and time_spent != \'\' '
            'AND time_spent != 0 ORDER BY key ASC'
        ), conn, params=[self.repo_name])

    def get_packages_belonging_to_keys(self):
        """
        Selects packages which belong to keys

        :return: dataframe containing the project name, package name, and version
        :rtype: pandas.DataFrame
        """
        conn, cursor = get_db_connection(test_db=self.use_test_db)

        df = pd.read_sql_query((
            'SELECT REPLACE(GIT_COMMITS_CHANGES.new_path, "\\", "/") AS path, '
            'GIT_COMMIT_JIRA.[key], JIRA_ISSUES.time_spent, GIT_COMMIT_RELEASE.version '
            'FROM GIT_COMMIT_RELEASE '
            'INNER JOIN GIT_COMMITS_CHANGES ON GIT_COMMIT_RELEASE.commit_hash = GIT_COMMITS_CHANGES.commit_hash '
            'INNER JOIN GIT_COMMIT_JIRA ON GIT_COMMITS_CHANGES.commit_hash = GIT_COMMIT_JIRA.commit_hash '
            'INNER JOIN JIRA_ISSUES ON JIRA_ISSUES.[key] = GIT_COMMIT_JIRA.[key] '
            'WHERE GIT_COMMIT_RELEASE.project_name=\'?\' AND old_path != "" AND new_path != "" AND '
            'JIRA_ISSUES.time_spent != "" AND GIT_COMMIT_RELEASE.project_name=\'?\' AND path LIKE "%.java" '
            'GROUP BY GIT_COMMIT_JIRA.[key], GIT_COMMITS_CHANGES.old_path, GIT_COMMIT_RELEASE.version '
            'ORDER BY GIT_COMMIT_JIRA.[key] ASC'
        ), conn, params=[self.repo_name, self.repo_name])

        df['package'] = df['path'].apply(lambda path: path[:path.rfind('/')])
        df = df.drop('path', axis='columns')
        # df = df.drop_duplicates(subset=['package', 'version'])
        
        return df

    def get_all_pv_metrics(self):
        conn, cursor = get_db_connection(test_db=self.use_test_db)

        package_versions = pd.read_sql_query((
            'SELECT package, version, pkg_files, pkg_loc, pkg_tokens, pkg_cc, pkg_average_loc, pkg_average_cc, '
            'pkg_average_tokens '
            'FROM STATIC_METRICS WHERE project_name = \'?\''
        ), conn, params=[self.repo_name])

        package_versions['package'] = package_versions['package'].apply(
            lambda x: x[x.find(self.repo_name) + len(self.repo_name) + 1:]
        )

        return package_versions

    def get_issue_pv_metrics(self):
        """
        Returns a DF containing all keys and their aggregated package metrics

        NOTE: There may be NaN package-version metrics. This is because the package metrics are snapshotted per
        version, unlike refactorings which are snapshotted per commit. The package may exist at the time of the
        refactoring, but not by the end of the version.
        """
        keys_and_pv = self.get_packages_belonging_to_keys()
        static_pv_metrics = self.get_all_pv_metrics()

        joined_static_metrics = keys_and_pv.merge(
            static_pv_metrics,
            on=['package', 'version'],
            how='left',
        ).fillna(0)

        # Aggregate PV metrics by key
        issue_pv_metrics = joined_static_metrics.groupby('key')[[
            'pkg_files', 'pkg_loc', 'pkg_tokens', 'pkg_cc', 'pkg_average_loc', 'pkg_average_cc', 'pkg_average_tokens'
        ]].sum().reset_index()

        return issue_pv_metrics

    def get_issue_refactorings(self):
        conn, cursor = get_db_connection(test_db=self.use_test_db)

        df = pd.read_sql_query((
            'SELECT GIT_COMMIT_JIRA.[key], refactoring_type '
            'FROM REFACTORING_MINER '
            'INNER JOIN GIT_COMMIT_JIRA '
            'ON REFACTORING_MINER.commit_hash = GIT_COMMIT_JIRA.commit_hash '
            'INNER JOIN JIRA_ISSUES ON GIT_COMMIT_JIRA.[key] = JIRA_ISSUES.[key] '
            'WHERE REFACTORING_MINER.project_name=\'?\' AND '
            'JIRA_ISSUES.time_spent IS NOT "" '
            'ORDER BY GIT_COMMIT_JIRA.[key] ASC'
        ), con=conn, params=[self.repo_name])

        df = df.pivot_table(
            index='key',
            columns='refactoring_type',
            aggfunc=len
        ).fillna(0).reset_index()

        return standardize_refactoring_columns(df)

    def get_issue_smells(self):
        keys_and_pv = self.get_packages_belonging_to_keys()
        pv_smells = self.get_pv_smells()

        joined_smells = keys_and_pv.merge(
            pv_smells,
            on=['package', 'version'],
            how='left'
        ).fillna(0)

        # Aggregate PV smells by key
        key_static_metrics = joined_smells.groupby('key')[all_smell_types].sum().reset_index()

        return key_static_metrics

    def get_issue_commit_metrics(self):
        conn, cursor = get_db_connection(use_regex=True)

        key_commit_metrics = pd.read_sql_query((
            'SELECT GIT_COMMIT_JIRA.key, version, REPLACE(new_path, "\\", "/") AS path, '
            'lines_added AS commits_loc_added, lines_removed AS commits_loc_removed '
            'FROM (GIT_COMMIT_JIRA '
            'LEFT JOIN '
            'GIT_COMMIT_RELEASE ON GIT_COMMIT_JIRA.commit_hash = GIT_COMMIT_RELEASE.commit_hash '
            'LEFT JOIN '
            'GIT_COMMITS_CHANGES ON GIT_COMMIT_RELEASE.commit_hash = GIT_COMMITS_CHANGES.commit_hash) '
            'WHERE '
            'GIT_COMMIT_RELEASE.project_name = \'?\' AND PATH LIKE \'%.java\''
        ), conn, params=[self.repo_name]).fillna(0)

        key_commit_metrics = key_commit_metrics.astype({
            'commits_loc_added': 'int', 'commits_loc_removed': 'int'
        })

        key_commit_metrics['n_commits'] = 1
        key_commit_metrics['commits_code_churn'] = key_commit_metrics['commits_loc_added'] - key_commit_metrics[
            'commits_loc_removed']

        new_paths = [path[:path.rfind('/')] for path in key_commit_metrics.path]
        key_commit_metrics = key_commit_metrics.drop('path', axis='columns')
        key_commit_metrics['package'] = new_paths

        # Aggregate commit metrics from keys
        key_commit_metrics = key_commit_metrics.groupby(['key'])[
            ['commits_loc_added', 'commits_loc_removed', 'commits_code_churn', 'n_commits']].agg('sum').reset_index()

        return key_commit_metrics

    def get_pv_linked_refactorings(self):
        """
        Returns aggregated refactorings across all package-versions *WITH* time_spent values
        """
        conn, cursor = get_db_connection(test_db=self.use_test_db)
        df = pd.read_sql_query((
            'SELECT REFACTORING_MINER.refactoring_type, '
            'REFACTORING_MINER.package, GIT_COMMIT_RELEASE.version '
            'FROM REFACTORING_MINER '
            'INNER JOIN GIT_COMMIT_RELEASE '
            'ON REFACTORING_MINER.commit_hash = GIT_COMMIT_RELEASE.commit_hash '
            'INNER JOIN GIT_COMMIT_JIRA '
            'ON GIT_COMMIT_RELEASE.commit_hash = GIT_COMMIT_JIRA.commit_hash '
            'INNER JOIN JIRA_ISSUES '
            'ON GIT_COMMIT_JIRA.[key] = JIRA_ISSUES.[key] '
            'WHERE GIT_COMMIT_RELEASE.project_name=\'?\' AND '
            'JIRA_ISSUES.time_spent != ""'
        ), con=conn, params=[self.repo_name])

        df = df.pivot_table(
            index=['package', 'version'],
            columns='refactoring_type',
            aggfunc=len
        ).fillna(0)

        df.reset_index(inplace=True)

        return standardize_refactoring_columns(df)

    def get_pv_smells(self):
        conn, cursor = get_db_connection(test_db=self.use_test_db)

        df = pd.read_sql_query('SELECT version, package, smell FROM DESIGNITE_SMELLS WHERE project_name=\'?\'',
            conn, params=[self.repo_name])

        df = df.pivot_table(
            index=['version', 'package'],
            columns=['smell'],
            aggfunc=len
        ).fillna(0)

        df.reset_index(inplace=True)

        return standardize_smells_columns(df)


if __name__ == '__main__':
    project = projects_with_jira['hive']
    print(project.repo_name)
    print(project.get_issue_commit_metrics().to_string())
    #print(project.get_packages_belonging_to_keys().to_string())
    #print(project.get_wide_package_refactorings().to_string())
    # print(project.get_version_history())
    #
    # refs = project.query_linked_refactorings('wide')
    # values = refs['time_spent'].value_counts()
    # values = values.sort_index()
    #
    # min_val = min(values.index)  # values.iloc[0]
    # max_val = max(values.index)  # [-1]
    # intermediate_values = np.arange(min_val, max_val, 600)
    # null_series = pd.Series(index=intermediate_values, dtype='float64')
    # filled_series = null_series.combine_first(values).fillna(0)
    # #print(values.to_string())
    #
    # values.plot(kind='bar')
    # plt.show()

    # # print(values.head(40).to_string())
    # # print(filled_series.head(40).to_string())
    #
    # values.plot(kind='bar')
    # #print(values.to_string())
    # plt.show()

    # print(refs.head().to_string())
    # print(len(refs))
