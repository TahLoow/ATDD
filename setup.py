from setuptools import setup, find_packages

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='atdd',
    version='1',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    install_requires=required,
    setup_requires=['wheel']
)
