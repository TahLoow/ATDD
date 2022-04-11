import os

top_level = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def _get_top_level_directory(dir_name):
    """
    Internal function. Gets the top level directory of passed directory name

    :param dir_name: directory name
    :type dir_name: str
    :return: top level directory
    :rtype: str
    """
    return os.path.join(top_level, dir_name)


database_directory = _get_top_level_directory('database')
etc_directory = _get_top_level_directory('etc')
repo_directory = _get_top_level_directory('repos')
src_directory = _get_top_level_directory('src')
tools_directory = _get_top_level_directory('tools')
configs_directory = _get_top_level_directory('configs')

if __name__ == '__main__':
    print('This module has no main-run functionality')
