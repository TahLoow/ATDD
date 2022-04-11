import json

from database.populator_helpers import Populator
from utils import shell_interface


class RefMinerPopulator(Populator):
    table_name = 'REFACTORING_MINER'
    backup_ext = 'json'

    def _execute_generate(self):
        # Refactoring Miner handles its own file saving -> json format
        response = shell_interface.run_ref_miner(
            self.project.repo_path, self.project.branch, self.db_backup.backup_file
        )
        print(response)

    def _execute_load(self):
        ref_file = open(self.db_backup.backup_file)
        refs_json = json.load(ref_file)
        ref_file.close()

        num_commits = 0
        num_empty_commits = 0
        for commit_refs in refs_json['commits']:
            num_commits = num_commits + 1
            if len(commit_refs['refactorings']) == 0:
                num_empty_commits = num_empty_commits + 1

            for ref_action in commit_refs['refactorings']:
                ref_type = ref_action['type']
                ref_detail = ref_action['description']
                ref_left_side = ref_action['leftSideLocations']

                ref_path = None
                ref_package = None
                if ref_left_side and len(ref_left_side) > 0:
                    ref_path = ref_left_side[0]['filePath']
                    ref_package = '/'.join(ref_path.split('/')[:-1])
                cmd = "INSERT INTO 'REFACTORING_MINER'(project_name,commit_hash," \
                      "refactoring_type,refactoring_detail,refactoring_path, package) VALUES (?, ?, ?, ?, ?, ?);"

                record = (self.project.repo_name, commit_refs['sha1'], ref_type, ref_detail, ref_path, ref_package)
                self.c.execute(cmd, record)
