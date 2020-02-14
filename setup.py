from setuptools import setup, find_packages
import sys
import os

import cadistributor as mainmodule

setup(
    name='CA Distributor',
    version=mainmodule.__version__,
    description="CodeAnalytics Distributor",
    long_description=mainmodule.__doc__,
    classifiers=[],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='codeanalytics research',
    author='Ben Klein, Alan Grant',
    author_email='bklein3@vols.utk.edu',
    url='https://codeanalytics.unhexium.dev/',
    license='MIT',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "coloredlogs",
        "Flask",
        "pymongo",
        "toml",
        "Flask-HTTPAuth",
        "gunicorn",
        "requests",
        "pygit2"
    ],
    entry_points={
        'console_scripts': [
            'ca-worker=cadistributor.worker:__main__'
        ]
    },
)
