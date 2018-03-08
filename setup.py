"""
setup.py

setuptools control

"""
 
import re
from setuptools import setup
 
version = re.search(
    '^__version__\s*=\s*"(.*)"',
    open('xssmap/XssMap.py').read(),
    re.M
    ).group(1)

with open('README.md', 'rb') as f:
    long_descr = f.read().decode('utf-8')
 
setup(
    name = 'xssmap',
    packages = ['xssmap'],
    entry_points = {
        'console_scripts' : ['xssmap = xssmap.xssmap:main']
        },
    version = version,
    description = 'Intelligent tool for XSS attacks based on DHS research.',
    long_description = long_descr,
    author = 'Secure Decisions / Aspect Security / EY',
    author_email = '',
    url = 'https://github.com/gingeleski/xssmap'
    )
