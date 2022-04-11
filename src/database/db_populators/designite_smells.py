import csv
import os
import shutil

import pandas as pd
from database.populator_helpers import PerVersionPopulator
from database.repo_version_walker import project_processing_path
from utils import shell_interface

designite_files_to_save = ['ArchitectureSmells.csv', 'DesignSmells.csv', 'ImplementationSmells.csv']

"""
This populator stores intermediate data in root/etc/designite_processing

Designite is the most difficult populator to work with. Its output only stores the relative path of the 
java files it observed, as "java.org.apache.example_package". In reality, the package's true path may be 
"src/server/java/org/apache/package_a". This is problematic, because not only are we missing part of the
path, but there may also be a recursive "java/org/apache..." in the path name. So we had to do all this.  
"""


def join_path(*paths):
    return os.path.abspath(os.path.join(*paths))


class DesigniteProcessingEnvironment:
    def __init__(self, project):
        self.processing_path = join_path(project_processing_path, f'{project.repo_name}_processing')
        self.macro_packages_folder = join_path(self.processing_path, 'temp_macro_packages')
        self.processed_out_folder = join_path(self.processing_path, 'designite_processed_out')
        self.temp_repo_folder = join_path(self.processing_path, 'temp_repo', project.repo_name)

        self._make_dirs()

    def _make_dirs(self):
        if os.path.exists(self.macro_packages_folder):
            os.system(f'rmdir /S /Q {self.macro_packages_folder}')

        os.mkdir(self.macro_packages_folder)

    def make_version_out_folder(self, repo_state):
        version_out_folder = join_path(self.processed_out_folder, repo_state.version.id_os_friendly)

        if os.path.exists(version_out_folder):
            os.system(f'rmdir /S /Q {version_out_folder}')
        os.makedirs(version_out_folder, exist_ok=True)

        return version_out_folder

    def extract_macro_packages(self, macro_package_paths):
        """
        This function copies every package and puts it into a macro_packages_folder.
        Order matters; we copy deepest paths first, so we maintain more shallow '/java/' directories in the path
        """
        # Sort packages by depth in the file system
        package_dir_depths = [len(os.path.normpath(package_path).split(os.sep)) for package_path in macro_package_paths]
        _, sorted_macro_packages = zip(*sorted(zip(package_dir_depths, macro_package_paths), reverse=True))

        # Copy paths to macro_packages_folder, name them in-order of packages list
        for i, package_path in enumerate(sorted_macro_packages):
            shutil.move(package_path, os.path.join(self.macro_packages_folder, str(i)))

        return sorted_macro_packages


class DesigniteSmellsPopulator(PerVersionPopulator):
    table_name = 'DESIGNITE_SMELLS'
    backup_ext = 'csv'

    @staticmethod
    def _read_designite_output(package_path_prefix, designite_out_path):
        package_smells = pd.DataFrame(columns=['package', 'smell', 'cause'])

        with open(designite_out_path, newline='') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            first_row = True
            for file_row in csv_reader:
                if first_row:
                    row_headers = enumerate(file_row)
                    row_numbers = [num for num, row in row_headers if row != 'Type Name'
                                   and row != 'Method Name' and row != 'Project Name']
                    first_row = False
                else:
                    file_row = [file_row[i] for i in row_numbers]

                    package_smells = package_smells.append({
                        'package': file_row[0],
                        'smell': file_row[1],
                        'cause': file_row[2]
                    }, ignore_index=True)

        package_smells['package'] = package_smells['package'].apply(
            lambda local_package: f'{package_path_prefix}/{local_package.replace(".", "/")}'.replace("\\", "/")
        )

        return package_smells

    def _execute_generate(self, repo_state):
        # if repo_state.version.id != 'release-3.3.2':
        #     return

        environment = DesigniteProcessingEnvironment(repo_state.project)

        macro_packages = repo_state.identify_macro_packages()
        if len(macro_packages) <= 0:
            return

        extracted_macro_packages = environment.extract_macro_packages(macro_packages)
        version_out_path = environment.make_version_out_folder(repo_state)

        smells_in_version = pd.DataFrame(columns=['package', 'smell', 'cause'])
        for i, macro_package_true_path in enumerate(extracted_macro_packages):
            macro_package_path = os.path.join(version_out_path, str(i))
            relative_true_path = os.path.relpath(macro_package_true_path, environment.temp_repo_folder)
            faux_path = os.path.join(environment.macro_packages_folder, str(i))

            print(f'{macro_package_path=}')
            print(f'{relative_true_path=}')
            print(f'{faux_path=}')

            os.mkdir(macro_package_path)

            print(
                f'Starting Designite analysis on Package: {relative_true_path} '
                f'({str(i)} of {len(macro_packages) - 1})\n'
            )
            shell_interface.run_designite(faux_path, macro_package_path)
            print('\n\n')

            with open(os.path.join(macro_package_path, 'pkg_name.txt'), 'w') as f:
                f.write(relative_true_path)

            for designite_out_file in os.listdir(macro_package_path):
                if designite_out_file in designite_files_to_save:
                    designite_out_path = os.path.join(macro_package_path, designite_out_file)
                    smells_in_version = smells_in_version.append(
                        self._read_designite_output(relative_true_path, designite_out_path),
                        ignore_index=True
                    )

        smells_in_version['project_name'] = self.project.repo_name
        smells_in_version['version'] = repo_state.version.id
        smells_in_version = smells_in_version.reindex(
            columns=['project_name', 'version', 'package', 'smell', 'cause']
        )

        self.db_backup.save_records_to_csv(smells_in_version.to_numpy().tolist())

    def _execute_load(self):
        cmd = "INSERT INTO DESIGNITE_SMELLS VALUES (?, ?, ?, ?, ?)"
        commit_records = (self.db_backup.read_csv_data())
        self.c.executemany(cmd, commit_records)
