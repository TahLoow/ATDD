from database.populator_helpers import RECORDS_UNTIL_CSV_SAVE, END_LOOP_FLAG, Populator
from internal_configs import version_getter
from pydriller import Repository


class GitCommitReleasePopulator(Populator):
    table_name = 'GIT_COMMIT_VERSION'
    backup_ext = 'csv'

    def _save_pydriller_commit(self, commit):
        release_record = (self.project.repo_name, commit.hash, commit.author_date, self.current_version.id)
        if len(self.records) >= RECORDS_UNTIL_CSV_SAVE:
            self.db_backup.save_records_to_csv(self.records)
            self.records = []
        else:
            self.records.append(release_record)

        # Move to next tag IF current commit is made after current tag
        while commit.author_date > self.current_version.author_date:
            try:
                self.current_version = next(self.version_iterator)
            except StopIteration:
                print('Encountered commits towards a non-existent version; flagging traverse_commits to break')
                return END_LOOP_FLAG

    def _execute_generate(self):
        all_versions = version_getter(repo_path=self.project.repo_path)
        # print([tag.author_date for tag in all_versions])
        # exit()
        self.version_iterator = iter(all_versions)
        self.current_version = next(self.version_iterator)
        self.records = []

        # print(list(version.author_date for version in all_versions))

        for commit in Repository(self.project.repo_path, order='').traverse_commits():
            result = self._save_pydriller_commit(commit)
            if result:
                break

        # Get any remaining commits
        self.db_backup.save_records_to_csv(self.records)

    def _execute_load(self):
        cmd = "INSERT INTO GIT_COMMIT_RELEASE(project_name, commit_hash, date, version) VALUES (?, ?, ?, ?)"

        csv_records = self.db_backup.read_csv_data()
        self.c.executemany(cmd, csv_records)
