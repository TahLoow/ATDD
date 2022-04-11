import csv
import io
import os
import sys
from datetime import datetime
from utils.top_level_paths import database_directory
import numpy as np

OUTPUT_DIR = os.path.join(database_directory, 'db_loadfiles')

FILE_TIME_FORMAT = '%Y-%m-%d_%H-%M-%S'
FILE_TIME_LENGTH = len(datetime.min.strftime(FILE_TIME_FORMAT))

# This section was taken from StackOverflow.
# It permits saving large CSV fields
maxInt = sys.maxsize
while True:
    # decrease the maxInt value by factor 10
    # as long as the OverflowError occurs.

    try:
        csv.field_size_limit(maxInt)
        break
    except OverflowError:
        maxInt = int(maxInt / 10)


def cleanup_all_save_files():
    for this_file in os.listdir(OUTPUT_DIR):
        this_file_path = os.path.join(OUTPUT_DIR, this_file)

        this_file_wo_ext = os.path.splitext(this_file)[0]
        this_file_prefix = this_file_wo_ext[:-FILE_TIME_LENGTH]
        file_to_keep = get_most_recent_file_with_prefix(this_file_prefix)
        if os.path.samefile(this_file_path, file_to_keep):
            print('Keeping file ' + this_file)
        else:
            print('Deleting file ' + this_file)
            os.remove(this_file_path)


def get_most_recent_file_with_prefix(file_prefix):
    # Get existing backup file
    most_recent_file = {
        'file_path': None,
        'file_datetime': datetime.min
    }

    # Loop to find most recent file belonging to project and table type
    for this_file in os.listdir(OUTPUT_DIR):
        file_path = os.path.join(OUTPUT_DIR, this_file)

        if this_file.startswith(file_prefix):
            this_file_wo_ext = os.path.splitext(this_file)[0]
            file_timestamp = this_file_wo_ext[len(file_prefix):]
            this_file_date = datetime.strptime(file_timestamp, FILE_TIME_FORMAT)

            if this_file_date > most_recent_file['file_datetime']:
                most_recent_file = {
                    'file_path': file_path,
                    'file_datetime': this_file_date
                }

    if most_recent_file['file_path']:
        return os.path.abspath(most_recent_file['file_path'])


class DbBackup:
    def __init__(self, project_id, file_identifier, file_ext, mode='r'):
        self.file_prefix = f'{project_id}_{file_identifier}_'
        self.file_ext = file_ext

        if mode == 'r':
            self.backup_file = get_most_recent_file_with_prefix(self.file_prefix)
        elif mode == 'w':
            self.backup_file = self.create_new_backup_file()

    def create_new_backup_file(self):
        # Create a new file to append into
        file_time = datetime.now().strftime(FILE_TIME_FORMAT)
        relative_path = os.path.join(OUTPUT_DIR, f'{self.file_prefix}{file_time}.{self.file_ext}')
        return os.path.abspath(relative_path)

    def backup_file_exists(self):
        return os.path.exists(self.backup_file)

    def save_record_to_csv(self, record):
        with io.open(self.backup_file, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter=',')
            writer.writerow(record)

    def save_records_to_csv(self, records):

        with io.open(self.backup_file, 'a', newline='', encoding='utf-8') as file:
            for record in records:
                writer = csv.writer(file, delimiter=',')
                writer.writerow(record)

    def read_csv_data(self):
        with io.open(self.backup_file, 'r', encoding='utf-8') as file:
            csv_reader = csv.reader((line.replace('\0', '') for line in file), delimiter=',')

            csv_data = [[col for col in row] for row in csv_reader]
        return csv_data


if __name__ == '__main__':
    cleanup_all_save_files()
