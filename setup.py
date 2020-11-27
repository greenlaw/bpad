import setuptools
import pathlib
import os

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# Get the long description from the README file
with open(os.path.join(HERE, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setuptools.setup(
    name='bpad',
    license='CC0-1.0',
    author='Jason Greenlaw',
    author_email='jay.greenlaw@gmail.com',
    description='Build-Package-Apply-Deploy',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/greenlaw/bpad',
    packages=setuptools.find_packages(),
    version='0.1.0',  # Temporarily hard-code version until tags are created
    #use_scm_version=True,
    #setup_requires=['setuptools_scm'],
    install_requires=['docker', 'fire', 'pyaml'],
    entry_points={
        'console_scripts': ['bpad=bpad.cli:main'],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'Intended Audience :: Developers',
        'License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication',
        'Operating System :: OS Independent',
    ]
)
