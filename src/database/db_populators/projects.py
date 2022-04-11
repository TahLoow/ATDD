from database.populator_helpers import Populator


class ProjectInfoPopulator(Populator):
    table_name = 'PROJECTS'

    def _execute_load(self):
        cmd = 'INSERT INTO PROJECTS (project_name, git_link, jira_link) VALUES (?, ?, ?)'
        self.c.execute(cmd, (self.project.repo_name, self.project.github_link, self.project.jira_link))