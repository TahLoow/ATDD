from database.populator_helpers import RECORDS_UNTIL_CSV_SAVE, Populator

from pydriller import Repository

class GitCommitChangesPopulator(Populator):
    table_name = 'GIT_COMMIT_CHANGES'
    backup_ext = 'csv'
    records = []

    def _execute_generate(self):
        def _save_pydriller_commit(commit):
            for f in commit.modified_files:
                file_old_path = f.old_path
                if file_old_path:
                    file_old_path = file_old_path.replace('\\', '/')
                file_new_path = f.new_path
                if file_new_path:
                    file_new_path = file_new_path.replace('\\', '/')
                change_type = str(f.change_type)
                diff = f.diff
                lines_added = f.added_lines
                lines_deleted = f.deleted_lines
                # below 4 properties are slow __getitem__s
                number_loc = f.nloc
                complexity = f.complexity
                tokens = f.token_count
                methods = str(list(map(lambda method: method.name, f.methods)))

                commit_change_record = (commit.project_name, commit.hash, file_old_path, file_new_path, change_type,
                                        diff, lines_added, lines_deleted, number_loc, complexity, tokens, methods)

                if len(self.records) >= RECORDS_UNTIL_CSV_SAVE:
                    self.db_backup.save_records_to_csv(self.records)
                    self.records = []
                else:
                    self.records.append(commit_change_record)

        for commit in Repository(self.project.repo_path, order='').traverse_commits():
            _save_pydriller_commit(commit)

    def _execute_load(self):
        cmd = "INSERT INTO GIT_COMMITS_CHANGES(project_name, commit_hash, old_path, new_path, change_type, diff, " \
              "lines_added, lines_removed, n_loc, complexity, token_count, methods) VALUES " \
              "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"

        commit_records = (self.db_backup.read_csv_data())
        self.c.executemany(cmd, commit_records)