from setuptools import setup, find_packages
from pip.req import parse_requirements
import sys
import os

version = '0.0.1'

install_reqs = parse_requirements('./requirements.txt')
reqs = [str(ir.req) for ir in install_reqs]

setup(name='CA Distributor',
    version=version,
    description="CodeAnalytics Distributor",
    long_description="",
    classifiers=[],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='codeanalytics research',
    author='Ben Klein, Alan Grant',
    author_email='bklein3@vols.utk.edu',
    url='https://codeanalytics.unhexium.dev/',
    license='MIT',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data=True,
    zip_safe=False,
    install_requires=reqs,
    # scripts=[
    #   'cadistributor/__main__.py'
    # ],
    entry_points={
        'console_scripts': [
            'ca-distributor=cadistributor.__main__:main'
        ]
    },
)
