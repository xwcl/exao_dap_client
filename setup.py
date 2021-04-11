from setuptools import setup, find_packages
from os import path

HERE = path.abspath(path.dirname(__file__))
ORG = 'xwcl'
PROJECT = 'exao_dap_client'

with open(path.join(HERE, 'README.md'), encoding='utf-8') as f:
    LONG_DESCRIPTION = f.read()

with open(path.join(HERE, PROJECT, 'VERSION'), encoding='utf-8') as f:
    VERSION = f.read().strip()

extras = {
    'dev': [
        'pytest',
    ],
}
all_deps = set()
for _, deps in extras.items():
    for dep in deps:
        all_deps.add(dep)
extras['all'] = list(all_deps)

setup(
    name=PROJECT,
    version=VERSION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    python_requires='>=3.8, <4',
    install_requires=[
        'astropy>=4.2,<5',
        'python-dateutil>=2.8.1,<3',
        'orjson>=3.4.8,<4',
        'fsspec>=0.8.5,<0.9',
        'irods-fsspec',
    ],
    package_data={
        PROJECT: ['VERSION'],
    },
    entry_points={
        'console_scripts': [
            'dap=exao_dap_client.cli:main',
            'dap_normalize_fits=exao_dap_client.commands.normalize_fits:main',
            'dap_irods_sync=exao_dap_client.commands.irods_sync:main',
        ],
    },
    extras_require=extras,
    project_urls={
        'Bug Reports': f'https://github.com/{ORG}/{PROJECT}/issues',
    },
)
