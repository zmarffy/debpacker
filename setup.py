import re
from os.path import join as join_path

import setuptools

with open(join_path("debpacker", "__init__.py"), encoding="utf8") as f:
    version = re.search(r'__version__ = "(.*?)"', f.read()).group(1)

setuptools.setup(
    name='debpacker',
    version=version,
    author='Zeke Marffy',
    author_email='zmarffy@yahoo.com',
    packages=setuptools.find_packages(),
    url='https://github.com/zmarffy/debpacker',
    license='MIT',
    description='A tool to help pack projects as a DEB file',
    python_requires='>=3.6',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    install_requires=[
        'pytz',
        'tzlocal',
        'zmtools'
    ],
    entry_points={
        'console_scripts': [
            'debpack = debpacker.__main__:main',
        ],
    },
)
