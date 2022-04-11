import numpy as np
import requests
from datetime import datetime
import re
from bs4 import BeautifulSoup

from database.db_connection import DB_ABSPATH
from database.populator_helpers import Populator


desired_jira_attributes = {
    'issuekey': 'key',
    'created': 'creation_date',
    'resolutiondate': 'resolution_date',
    'updated': 'update_date',
    'duedate': 'due_date',
    'resolution': 'resolution',
    'issuetype': 'type',
    'priority': 'priority',
    'fixVersions': 'fix_versions',
    'versions': 'versions',
    'timespent': 'time_spent',
    'aggregatetimespent': 'aggregated_time_spent',
    'timeestimate': 'time_estimate',
    'aggregatetimeestimate': 'aggregated_time_estimate',
    'progress': 'progress_percent',
    'description': 'description',
    'summary': 'summary',
    'watches': 'watch_count',
    'votes': 'votes',
    'creator': 'creator_name',
    'assignee': 'assignee',
    'reporter': 'reporter'
}


attributes_to_listify = [
    'fixVersions', 'versions',
]

attributes_to_dateify = [
    'created', 'resolutiondate', 'updated', 'duedate'
]

class JiraIssuesPopulator(Populator):
    table_name = 'JIRA_ISSUES'
    backup_ext = 'csv'

    def _execute_generate(self):
        r = requests.get(f'{self.project.jira_link}/rest/api/2/search?jql=project={self.project.repo_name}' \
                         f'+ORDER+BY+createdDate+DESC&maxResults=1&fields=updated')

        # extracting data in json format
        request_json = r.json()
        latest_issue = request_json['issues'][0]
        latest_key = latest_issue['key']
        last_key_number = int(latest_key[latest_key.find('-')+1:])

        last_iteration = False
        step_size = 1000
        key_1 = 1
        key_2 = 1000

        while not last_iteration:
            if key_2 > last_key_number:
                key_2 = last_key_number
                last_iteration = True

            request_str = f'{self.project.jira_link}' \
                          f'/sr/jira.issueviews:searchrequest-html-all-fields/temp/SearchRequest.html?jqlQuery=' \
                          f'project%3D{self.project.repo_name}' \
                          f'%20AND%20key%3E%3D{self.project.repo_name}-{str(key_1)}' \
                          f'%20AND%20key%3C%3D{self.project.repo_name}-{str(key_2)}'

            r = requests.get(request_str)

            # If key_1 or key_2 is a moved key, we'll get an error. so we'll get the next key and try again
            if r.status_code == 400 and r.text.find('moved issue'):
                regex_str = f'{self.project.repo_name.upper()}\\-(\\d+)'
                problematic_key = re.search(regex_str, r.text).groups()[0]
                problematic_key = int(problematic_key)

                # Edge case: key_1 gets incremented to key_2 due to 1000 moves.........
                if problematic_key == key_1:
                    key_1 = key_1 + 1
                    key_2 = key_2 + 1
                elif problematic_key == key_2:
                    key_2 = key_2 + 1

                continue


            parsed_html = BeautifulSoup(r.text, 'html.parser')
            parsed_html = parsed_html.find('tbody')

            thousand_keys = []
            for tr in parsed_html.find_all('tr'):
                key_attributes = []
                for i, html_attribute in enumerate(desired_jira_attributes.keys()):
                    value = tr.find('td', attrs={'class': html_attribute})

                    if value is None:
                        value = ''
                    else:
                        value = value.get_text(strip=True)

                    if html_attribute in attributes_to_listify:
                        value = value.split()
                    elif html_attribute in attributes_to_dateify and value != '':
                        value_time_obj = None
                        try:
                            value_time_obj = datetime.strptime(value, '%d/%b/%y %H:%M')
                        except:
                            value_time_obj = datetime.strptime(value, '%d/%b/%y')
                        value = str(value_time_obj)

                    key_attributes.append(value)
                thousand_keys.insert(0, key_attributes)

            key_1 = key_2 + 1
            key_2 = key_2 + step_size

            self.db_backup.save_records_to_csv(thousand_keys)


    def _execute_load(self):
        cmd = f"INSERT INTO JIRA_ISSUES(project_name, {', '.join(desired_jira_attributes.values())}) VALUES (?, {', '.join(['?']*len(desired_jira_attributes))})"
        print(cmd)
        csv_records = self.db_backup.read_csv_data()
        csv_records = [[self.project.repo_name] + record for record in csv_records]
        #csv_records = np.asarray(csv_records)
        # print(csv_records[:5])
        # csv_records.push(0, [self.project.repo_name])
        self.c.executemany(cmd, csv_records)

# 'https://issues.apache.org/jira/sr/jira.issueviews:searchrequest-html-all-fields/temp/SearchRequest.html?jqlQuery=project+%3D+AMBARI+AND+key+%3E%3D+AMBARI-1+AND+key+%3C%3D+AMBARI-1000'