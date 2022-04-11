"""
Gets all repo version information
"""

import csv
import os
import sys

from database.db_connection import get_db_connection
from utils import shell_interface
from utils.top_level_paths import etc_directory
from internal_configs import version_getter


project_processing_path = os.path.abspath(os.path.join(etc_directory, 'project_processing'))

maxInt = sys.maxsize

hash_omit_list = []

while True:
    # decrease the maxInt value by factor 10
    # as long as the OverflowError occurs.
    try:
        csv.field_size_limit(maxInt)
        break
    except OverflowError:
        maxInt = int(maxInt / 10)


class RepoState:
    """

    """

    def __init__(self, project, repo_path, version):
        self.project = project
        self.version = version
        self.java_files = self.find_files(directory=repo_path, extension='java')
        self.packages = self.get_packages_from_files(self.java_files)

    def find_files(self, directory='.', extension=''):
        """
        Finds files from starting directory
        :param directory: the directory to start in
        :type directory: str
        :param extension: file extension to find
        :type extension: str
        :return: A list of files
        :rtype: list
        """

        return_files = []
        extension = extension.lower()
        for dirpath, dirnames, files in os.walk(directory):
            for name in files:
                if extension and name.lower().endswith(extension):
                    file_path = os.path.join(dirpath, name).replace('\\', '/')
                    return_files.append(file_path)

        return return_files

    @staticmethod
    def get_packages_from_files(file_paths):
        """
        For every file, get the file path
        :param file_paths: the list of files, with the filename included
        :type file_paths: list
        :return: a list of file paths, without the file name
        :rtype: list
        """
        package_paths = [os.path.dirname(file_path) for file_path in file_paths]
        package_paths = set(package_paths)

        return package_paths

    def identify_macro_packages(self):
        java_files = self.java_files

        packages = []
        package_indicator = '/java/org/'
        for path in java_files:
            dir = os.path.dirname(path)
            package_rev_i = dir.rfind(package_indicator)
            if package_rev_i != -1:
                package = dir[:package_rev_i + len('/java/')]  # the /org/apache/project gets concatenated later
                packages.append(package)
            else:
                print('File found without proper package: ' + path)

        packages = set(packages)
        return packages


class RepoVersionWalker:
    def __init__(self, project):
        self.project = project

        self.processing_path = os.path.abspath(os.path.join(project_processing_path, f'{project.repo_name}_processing'))
        self.temp_repo = os.path.abspath(os.path.join(self.processing_path, f'temp_repo'))
        self.repo_path = os.path.join(self.temp_repo, project.repo_name)

        self._make_dirs()
        self._clone_repo(project)

        self.versions = version_getter(self.repo_path)

    def _make_dirs(self):
        """
        makes the necessary directory to clone a project into
        """
        if not os.path.exists(project_processing_path):
            os.mkdir(project_processing_path)

        if not os.path.exists(self.processing_path):
            os.mkdir(self.processing_path)

        if os.path.exists(self.temp_repo):
            os.system(f'rmdir /S /Q {self.temp_repo}')
        os.mkdir(self.temp_repo)

    def _clone_repo(self, project):
        """
        Clones specified repo from github

        :param project: The project to be copied
        :type project: utils.project.Project
        """
        print(f'Cloning temporary repo from {project.github_link}...')
        os.system(f'git clone  -v {project.github_link} {self.repo_path}')
        os.system(f'git -C {self.repo_path} config core.longpaths true')

    def walk(self):
        """
        Walks through all versions by using the :mod:`checkout_commit <RepoState._checkout_commit>` method

        :return: The repo state for a specific project at different versions
        """

        for version_i, version in enumerate(self.versions):
            if version.id in hash_omit_list:
                continue

            print(f'Moving head to {version.hash_id}...')

            shell_interface.checkout_commit(self.repo_path, version.hash_id)  # '7f0336380f9c1061834b41c671917e53a18332e0'

            yield RepoState(self.project, self.repo_path, version)

    def cleanup(self):
        """
        Removes projects after they are finished
        """
        # os.system(f'rmdir /S /Q {macro_packages_path}')
        pass


if __name__ == '__main__':
    conn, c = get_db_connection()


    # omit_list is used in case progress gets interrupted, and needs to be restarted without re-analyzing certain commits

    # save_smells_info(projects_with_jira['ambari'])

    # for project in projects_with_jira.values():
    #     save_smells_to_db(project)
    #     # if project.repo_name != 'zookeeper':
    #     #     continue
    #     # save_smells_info(project)

    def test_lizard():
        test_inputs = {
            'c:/users/plaul/documents/wvu/iv-v-wvu-research/etc/project_processing/temp_repo/ambari/client/src/main/java/org/apache/ambari/client',
            'c:/users/plaul/documents/wvu/iv-v-wvu-research/etc/project_processing/temp_repo/ambari/client/src/main/java/org/apache/ambari/common/rest/entities',
            'c:/users/plaul/documents/wvu/iv-v-wvu-research/etc/project_processing/temp_repo/ambari/client/src/main/java/org/apache/ambari/common/state',
            'c:/users/plaul/documents/wvu/iv-v-wvu-research/etc/project_processing/temp_repo/ambari/controller/src/main/java/org/apache/ambari/components',
            'c:/users/plaul/documents/wvu/iv-v-wvu-research/etc/project_processing/temp_repo/ambari/client/src/main/java/org/apache/ambari/event',
            'c:/users/plaul/documents/wvu/iv-v-wvu-research/etc/project_processing/temp_repo/ambari/controller/src/main/java/org/apache/ambari/components/impl',
            'c:/users/plaul/documents/wvu/iv-v-wvu-research/etc/project_processing/temp_repo/ambari/controller/src/main/java/org/apache/ambari/controller/rest/config',
            'c:/users/plaul/documents/wvu/iv-v-wvu-research/etc/project_processing/temp_repo/ambari/controller/src/main/java/org/apache/ambari/resource/statemachine',
            'c:/users/plaul/documents/wvu/iv-v-wvu-research/etc/project_processing/temp_repo/ambari/client/src/main/java/org/apache/ambari/common/util',
            'c:/users/plaul/documents/wvu/iv-v-wvu-research/etc/project_processing/temp_repo/ambari/client/src/main/java/org/apache/ambari/common/rest/entities/agent',
            'c:/users/plaul/documents/wvu/iv-v-wvu-research/etc/project_processing/temp_repo/ambari/controller/src/main/java/org/apache/ambari/controller',
            'c:/users/plaul/documents/wvu/iv-v-wvu-research/etc/project_processing/temp_repo/ambari/controller/src/main/java/org/apache/ambari/controller/rest/resources',
            'c:/users/plaul/documents/wvu/iv-v-wvu-research/etc/project_processing/temp_repo/ambari/controller/src/main/java/org/apache/ambari/controller/rest/agent'
        }

