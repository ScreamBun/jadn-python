import json

from setuptools import setup, find_packages

with open('version.json', 'r') as version:
    versionData = json.loads(version.read())

setup(
    name=versionData['name'],

    version='{major}.{minor}.{bugfix}'.format(**versionData['version']['number']),

    # author='G2-Inc.',
    # author_email='screaming_bunny@g2-inc.com',

    description='JADN Schema/Message Translator & Validator',
    # long_description="",
    # long_description_content_type="text/markdown",

    # url="https://github.com/oasis-open/jadn",

    install_requires=[d.replace('\n', '') for d in open('requirements.txt', 'r').readlines()],

    packages=find_packages(),

    classifiers=[
        "Development Status :: 5 - Development/Beta",
        "Intended Audience :: Developers",
        "License :: Apache 2.0 License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Security :: Translation :: Validation"
    ],

    # Python 3.6+ but not 4
    python_requires='>=3.6, <4',

    package_data={
        str(versionData['name']): [
            './{}/*'.format(versionData['pkg_name'])
        ]
    },

    include_package_data=True,

    # CLI usage
    entry_points=dict(
        console_scripts=[
            'jadnschema=jadnschema.cli:main'
        ],
    )
)
