import os

from database.populator_helpers import PerVersionPopulator
import lizard


class StaticMetricsPopulator(PerVersionPopulator):
    table_name = 'STATIC_METRICS'
    backup_ext = 'csv'

    def _execute_generate(self, repo_state):
        package_records = []
        print(repo_state.packages)
        print(repo_state.version.id)
        print(repo_state.version.hash_id)
        for package_path in repo_state.packages:
            local_path_flag = f'/{repo_state.project.repo_name}/'
            local_package_path = package_path[package_path.find(local_path_flag)+len(local_path_flag):]

            # NOTE: .JAV FILES DO NOT WORK, ONLY .JAVA
            analyzed_files = lizard.analyze([package_path], exclude_pattern=[os.path.join(package_path, '*/*')])
            n_files = 0
            n_loc = 0
            cc = 0
            n_tokens = 0
            # total_depth = 0
            for file_info in analyzed_files:
                n_files = n_files + 1
                n_loc = n_loc + file_info.nloc
                cc = cc + file_info.CCN
                n_tokens = n_tokens + file_info.token_count
                # total_depth = total_depth + file_info.ND

            if n_files <= 0:
                continue

            # git reset --hard
            # print(analyzed_files)
            # print(package_path)
            # print(local_package_path)
            # input()

            avg_n_loc = n_loc / n_files
            avg_tokens = n_tokens / n_files
            avg_cc = cc / n_files
            # average_depth = total_depth / total_files

            package_record = (repo_state.project.repo_name, local_package_path, repo_state.version.id,
                              n_files, n_loc, n_tokens, cc, avg_n_loc, avg_cc, avg_tokens)
            package_records.append(package_record)

        self.db_backup.save_records_to_csv(package_records)

    def _execute_load(self):
        cmd = "INSERT INTO STATIC_METRICS (project_name, package, version, pkg_files, pkg_loc, pkg_tokens, pkg_cc," \
              "pkg_average_loc, pkg_average_cc, pkg_average_tokens) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"

        metrics_records = (self.db_backup.read_csv_data())
        self.c.executemany(cmd, metrics_records)
        # self.conn.commit()
