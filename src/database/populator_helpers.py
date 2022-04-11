from abc import ABC, abstractmethod

from database.db_connection import get_db_connection
from database.db_file_backup import DbBackup
from pydriller import Repository

RECORDS_UNTIL_CSV_SAVE = 200
END_LOOP_FLAG = -1


class Populator(ABC):
    def __init__(self, project, db_action):
        self.project = project
        self.conn, self.c = get_db_connection(use_regex=True)
        self.db_action = db_action

        # All Populator objects have a backup, but don't need to use it.
        self.db_backup = DbBackup(
            project_id=self.project.repo_name,
            file_identifier=self.table_name,
            file_ext=self.backup_ext,
            mode='w' if db_action.is_generate() else 'r'
        )

    backup_ext = ''

    @abstractmethod
    def table_name(self):
        pass

    def _execute_generate(self):
        pass

    def _execute_load(self):
        pass

    def execute(self, db_action):
        if db_action.is_generate():
            self._execute_generate()
        elif db_action.is_load():
            self._execute_load()

        self.conn.commit()
        self.conn.close()


class PerVersionPopulator(Populator):
    def table_name(self):
        pass

    # noinspection PyMethodOverriding
    def execute(self, repo_state=None):
        if self.db_action.is_generate():
            self._execute_generate(repo_state)
        elif self.db_action.is_load():
            self._execute_load()

        self.conn.commit()

    # noinspection PyMethodOverriding
    def _execute_generate(self, repo_state):
        pass

    per_version_saving = True

