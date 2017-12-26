# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='htb',
    version='0.3.0',

    description='Hack the Box API',
    long_description=long_description,

    url='https://gitlab.com/kulinacs/htb',

    author='Nicklaus McClendon',
    author_email='nicklaus@kulinacs.com',

    license='ISC',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Programming Language :: Python :: 3.6',
    ],

    keywords='hackthebox',

    packages=find_packages(),

    install_requires=['bs4',
                      'requests'],
)
