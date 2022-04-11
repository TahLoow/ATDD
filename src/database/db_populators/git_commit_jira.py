from database.populator_helpers import Populator


class GitCommitJiraPopulator(Populator):
    table_name = 'GIT_COMMIT_JIRA'
    backup_ext = 'csv'

    def _execute_generate(self):
        # Get jira keys
        cmd = f"select key from JIRA_ISSUES where project_name = '{self.project.repo_name}'"
        self.c.execute(cmd)
        raw_keys = self.c.fetchall()
        raw_keys.reverse()
        keys = (key[0] for key in raw_keys)
        key_to_commit_records = []

        for key in keys:
            cmd = f"select commit_hash, commit_message from GIT_COMMITS where project_name = '{self.project.repo_name}' and " \
                  f"(commit_message REGEXP ('\\b{key}\\b'))"
            self.c.execute(cmd)
            commits = self.c.fetchall()
            commit_hashes = (commit[0] for commit in commits)

            # Create a record for each commit pertaining to a jira key
            for commit_hash in commit_hashes:
                record = (key, commit_hash)
                key_to_commit_records.append(record)

            print(f'Found {len(key_to_commit_records)} total commits')

        self.db_backup.save_records_to_csv(key_to_commit_records)

    def _execute_load(self):
        cmd = "INSERT INTO GIT_COMMIT_JIRA(key, commit_hash) VALUES (?, ?)"

        csv_records = self.db_backup.read_csv_data()
        self.c.executemany(cmd, csv_records)