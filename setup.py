#!/usr/bin/env python
# -*- coding: utf-8 -*-
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'django>=1.8,<1.10',
    'djangorestframework>=3',
    'redis>=2.10.3',
    'websockets',
]

setup(
    name='tg-pubsub',
    version='0.1.0-dev',
    description="Easy pubsub for django",
    long_description=readme + '\n\n' + history,
    author="Thorgate",
    author_email='code@thorgate.eu',
    url='https://github.com/thorgate/tg-pubsub',
    packages=[
        'tg_pubsub',
    ],
    package_dir={'tg_pubsub': 'tg_pubsub'},
    include_package_data=True,
    install_requires=requirements,
    dependency_links=[
        # We currently use our own fork, and also created a PR: https://github.com/aaugustin/websockets/pull/98
        'git+https://github.com/Jyrno42/websockets.git@18d26ea1d48ecadf6fc49d526a27814fb4b16362#egg=websockets-3.0',
    ],
    license="ISCL",
    zip_safe=False,
    keywords='tg-pubsub,tg_pubsub,pubsub,pub,sub,django',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)
