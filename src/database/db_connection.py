'''
Created on Apr 5, 2020

@author: Samir Deeb
'''
import os
import re
import sqlite3
import warnings

from utils.top_level_paths import database_directory

DB_ABSPATH = os.path.join(database_directory, 'augmented_tdd.db')
TEST_DB_ABSPATH = os.path.join(database_directory, 'mock_tdd.db')

test_warning_debounce = False

# Regex function for SQLite3 regex queries
def re_fn(expr, item):
    reg = re.compile(expr, re.I)
    return reg.search(item) is not None


def get_db_connection(use_regex=False, test_db=False):
    global test_warning_debounce

    if not test_db:
        conn = sqlite3.connect(DB_ABSPATH)
    else:
        if test_warning_debounce:
            warnings.warn('!!! Using TEST dataset !!!\nDisable USE_TEST in db_connection to use augmented_tdd')
        conn = sqlite3.connect(TEST_DB_ABSPATH)
        test_warning_debounce = True

    if use_regex:
        conn.create_function("REGEXP", 2, re_fn)
    cursor = conn.cursor()

    return conn, cursor
