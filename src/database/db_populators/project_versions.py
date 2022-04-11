from database.populator_helpers import Populator
from internal_configs import version_getter


class ProjectVersionsPopulator(Populator):
    table_name = 'PROJECT_VERSIONS'

    def _execute_load(self):
        cmd = 'INSERT INTO PROJECT_VERSIONS ' \
              '(project_name, version, commit_hash, author_date, previous_version) ' \
              'VALUES (?, ?, ?, ?, ?)'

        previous_version = None
        for version_info in version_getter(self.project.repo_path):
            self.c.execute(cmd, (self.project.repo_name, version_info.id, version_info.hash_id, version_info.author_date, previous_version))
            previous_version = version_info.id
