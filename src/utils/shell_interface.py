import subprocess
from utils import config_interface


def _run_process(cmd, check_out=False):
    response = None

    if check_out:
        response = subprocess.check_output(cmd, shell=False, stderr=subprocess.STDOUT).decode("utf-8")
    else:
        subprocess.run(cmd, shell=False, stderr=subprocess.STDOUT)

    return response


def run_designite(dir_to_analyze, output_path):
    """
    Runs designite on a project
        !!WARNING!! designite deletes whatever is in the folder before uploading results

    :param dir_to_analyze: the directory of project
    :type dir_to_analyze: str
    :param output_path: the path to send results.
    :type output_path: str
    :return: the response to the process being run
    """
    designite_config = config_interface.get_tool_path("designite")

    cmd = [
        'java', f'-Xmx{designite_config["max_allocation"]}', '-jar', designite_config["path"],
        '-i', dir_to_analyze,
        '-o', output_path
    ]
    return _run_process(cmd)


def run_ref_miner(repo_to_analyze, branch, output_file):
    """
    runs refactoring miner on a repo

    :param repo_to_analyze: the repository to analyze
    :type repo_to_analyze: str
    :param branch: the branch to analyze
    :type branch: str
    :param output_file: the location of the output
    :type output_file: str
    :return: the response to the process being run
    """
    ref_miner_config = config_interface.get_tool_path("refactoring_miner")

    cmd = [ref_miner_config["path"], '-a', repo_to_analyze, branch, '-json', output_file]
    return _run_process(cmd)


def run_weka_filter(filter_method, filter_options, input_file, output_file):
    """
    Runs the weka filter on a file

    :param filter_method: The filtering method
    :type filter_method: str
    :param filter_options: special options for the filter
    :type filter_options: str
    :param input_file: the file to run the filter on
    :type input_file: str
    :param output_file: the file containing the filtered results
    :type output_file: str
    :return: the response to the process being run
    """
    weka_config = config_interface.get_tool_path("weka")

    cmd = [
        'java', '-classpath', f'"{weka_config["path"]}"', filter_method,
        '-i', f'"{input_file}"',
        '-o', f'"{output_file}"', filter_options
    ]
    return _run_process(cmd)


def run_weka_classifier(classifier_method, classifier_options, input_path, model_output_path=None):
    """
    Runs the weka classifier on a file

    :param classifier_method: The classifying method
    :type classifier_method: str
    :param classifier_options: special options for the classifier
    :type classifier_options: str
    :param input_path: the path of the file to be classified
    :type input_path: str
    :param model_output_path: the path for the output of the classification
    :type model_output_path: str
    :return: the response to the process being run
    """
    weka_config = config_interface.get_tool_path("weka")

    model_arg = ''
    cmd = ['java', '-classpath', f'"{weka_config["path"]}"', classifier_method, '-t', f'"{input_path}"', '-o', '-v',
           classifier_options, model_arg]

    if model_output_path is not None:
        cmd.extend(['-d', model_output_path])
        # model_arg = f'-d {model_output_path}'

    return _run_process(cmd, check_out=True)


def load_and_run_weka_classifier(classifier_method, model_input_file, input_path):
    """
    Runs premade classifier on input file

    :param classifier_method: the classifier to run
    :type classifier_method: str
    :param model_input_file: the model path
    :type model_input_file: str
    :param input_path: the file path
    :type input_path: str
    :return: the response to the process being run
    """
    weka_config = config_interface.get_tool_path("weka")

    cmd = ['java', '-classpath', f'"{weka_config["path"]}"', classifier_method, '-l',
           f'"{model_input_file}"', '-T', f'"{input_path}"', '-p', '0']
    return _run_process(cmd, check_out=True)


def run_git_log_tags(repo_path):
    cmd = ['git', '-C', repo_path, 'log', '--no-walk', '--tags', '--reverse', '--date=iso-local', '--format=%H,%ad,%D']
    return _run_process(cmd, check_out=True)


def checkout_commit(repo_path, commit_hash):
    cmd = ['git', '-C', repo_path, 'checkout', '-f', commit_hash]
    return _run_process(cmd)


def update_repository(repo_path):
    cmd = ['git', '-C', repo_path, 'fetch', '--tags']
    _run_process(cmd)

    cmd = ['git', '-C', repo_path, 'fetch']
    _run_process(cmd)

    cmd = ['git', '-C', repo_path, 'merge']
    _run_process(cmd)


def clone_repository(github_link, repo_path):
    cmd = ['git', 'clone', github_link, repo_path]
    return _run_process(cmd)


if __name__ == '__main__':
    print('No main functionality')
