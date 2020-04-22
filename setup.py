from setuptools import setup, find_packages

import cadistributor as mainmodule

with open("README.md", "r") as f:
    readme = f.read()

setup(
    name='CA Distributor',
    version=mainmodule.__version__,
    description="CodeAnalytics Distributor",
    long_description=readme,
    long_description_content_type="text/markdown",
    classifiers=[],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='codeanalytics research',
    author='Ben Klein, Alan Grant',
    author_email='bklein3@vols.utk.edu',
    url='https://ca-core.unhexium.dev/',
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
    python_requires='>=3.6'
)
