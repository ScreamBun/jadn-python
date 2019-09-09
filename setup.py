import json

from setuptools import setup

with open('version.json', 'r') as version:
    versionData = json.loads(version.read())

setup(
    use_scm_version=True,
    version='{major}.{minor}.{bugfix}'.format(**versionData['version']['number']),

    # author='G2-Inc.',
    # author_email='screaming_bunny@g2-inc.com',
    # url="https://github.com/oasis-open/jadn",
    # Python 3.6+ but not 4
    # python_requires='>=3.6, <4',

    package_data={
        str(versionData['name']): [
            './{}/*'.format(versionData['pkg_name'])
        ]
    },

    include_package_data=True,
)
