import os
import re
import ast
from setuptools import setup


_root = os.path.abspath(os.path.dirname(__file__))
_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open(os.path.join(_root, 'gubed/__init__.py')) as fd:
    version = str(ast.literal_eval(_version_re.search(fd.read()).group(1)))

with open(os.path.join(_root, 'requirements.txt')) as fd:
    requirements = fd.readlines()

with open(os.path.join(_root, 'README.md')) as fd:
    readme = fd.read()

setup(
    name='gubed',
    version=version,
    description='a module born to debug',
    long_description=readme,
    url='https://github.com/Hanaasagi/gubed',
    author='Hanaasagi',
    author_email='ambiguous404@gmail.com',
    license='Apache 2.0',
    packages=['gubed'],
    install_requires=requirements,
)
