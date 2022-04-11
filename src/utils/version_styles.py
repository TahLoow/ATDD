import re
from datetime import timedelta

from dateutil import parser as date_parser
from pydriller import Repository
from utils import shell_interface

TAG_STR_REGEX = re.compile('.*?tag: (.+?)(,|$)')


class Version:
    id = None
    hash_id = None
    author_date = None

    def __init__(self, version_id, version_hash, author_date):
        self.id = version_id
        self.id_os_friendly = version_id.replace('/', '-')

        self.hash_id = version_hash
        self.author_date = author_date

    def to_string(self):
        return 'version: {:<32}   |   hash: {:<40}   |   date: {}'\
            .format(self.id, self.hash_id, self.author_date)


def interval_versions(repo_path, version_interval=60):
    """
    Gets versions in various intervals

    :param repo_path: path to repository
    :type repo_path: str
    :param version_interval: how many days the interval should be for each version
    :type version_interval: int
    :return: list of versions
    :rtype: list[Version]
    """
    all_versions = []
    target_date = None
    version_counter = 1

    for commit in Repository(repo_path, order='').traverse_commits():
        acknowledge_version = False

        if len(all_versions) == 0:
            acknowledge_version = True
        elif commit.author_date.date() > target_date:
            acknowledge_version = True

        if acknowledge_version:
            # Append version
            version = Version(str(version_counter), commit.hash, commit.author_date)
            all_versions.append(version)

            # Set next target date to be days_per_version after this commit
            target_date = commit.author_date.date() + timedelta(version_interval)

            version_counter += 1

    return all_versions


def git_tags(repo_path):
    """
    Uses git tags as versions

    :param repo_path: path to the repository
    :type repo_path: str
    :return: list of versions
    :rtype: list[Version]
    """
    all_versions = []
    all_tag_lines_bytestring = shell_interface.run_git_log_tags(repo_path)
    all_tag_lines = all_tag_lines_bytestring.strip().split('\n')

    for tag_info_line in all_tag_lines:
        tag_info_delimited = tag_info_line.split(',')
        tag_hash = tag_info_delimited[0]
        tag_date = date_parser.parse(tag_info_delimited[1])
        regex_result = TAG_STR_REGEX.match(tag_info_line)
        tag_str = regex_result.group(1)

        version = Version(tag_str, tag_hash, tag_date)
        all_versions.append(version)

    return all_versions


if __name__ == '__main__':
    hist = git_tags('../../repos/ambari')
    for x in hist:
        print(x.to_string())

    print('-------')
    hist = interval_versions('../../repos/ambari')
    for x in hist:
        print(x.to_string())

    print('-------')
    v1 = Version('A11111', 'B', 'C')
    v2 = Version('A11', 'B444', 'D')
    print(v1.to_string())
    print(v2.to_string())
