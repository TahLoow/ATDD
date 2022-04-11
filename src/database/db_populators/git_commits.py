from database.populator_helpers import RECORDS_UNTIL_CSV_SAVE, Populator

from pydriller import Repository

class GitCommitsPopulator(Populator):
    table_name = 'GIT_COMMITS'
    backup_ext = 'csv'
    records = []

    def _save_pydriller_commit(self, commit):
        c_hash = commit.hash
        project = commit.project_name
        msg = commit.msg
        author_name = commit.author.name
        author_date = commit.author_date.strftime('%m/%d/%Y %H:%M:%S')
        author_timezone = commit.author_timezone
        commiter_name = commit.committer.name
        commiter_date = commit.committer_date.strftime('%m/%d/%Y %H:%M:%S')
        commiter_timezone = commit.committer_timezone
        in_main_branch = commit.in_main_branch
        merge = commit.merge
        parents = str(commit.parents)
        # Ignored data: branches, files, lines, insertions, deletions

        commit_record = (project, c_hash, msg, author_name, author_date, author_timezone, commiter_name,
                         commiter_date, commiter_timezone, in_main_branch, merge, parents)

        if len(self.records) >= RECORDS_UNTIL_CSV_SAVE:
            self.db_backup.save_records_to_csv(self.records)
            self.records = []
        else:
            self.records.append(commit_record)

    def _execute_generate(self):
        for commit in Repository(self.project.repo_path, order='').traverse_commits():
            self._save_pydriller_commit(commit)

        # Get any remaining commits
        self.db_backup.save_records_to_csv(self.records)


    def _execute_load(self):
        cmd = "INSERT INTO GIT_COMMITS(project_name, commit_hash, commit_message, author, author_date, author_timezone, " \
              "committer, committer_date, committer_timezone, in_main_branch, merge, parents) VALUES " \
              "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"

        csv_records = self.db_backup.read_csv_data()
        self.c.executemany(cmd, csv_records)
