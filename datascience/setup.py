#!/usr/bin/env python
# -*- coding:utf-8 -*-
from setuptools import setup, find_packages



REQUIREMENTS = [i.strip() for i in open("requirements.txt").readlines()]

classifiers = [
    "Framework :: Flask",
    'Development Status :: 3 - Alpha',
    'Environment :: Console',
    'Intended Audience :: Developers',
    'Natural Language :: English',
    'License :: OSI Approved :: BSD License',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: Implementation :: CPython',
    'Programming Language :: Python :: Implementation :: PyPy',
    'Topic :: Software Development']

description = "La Jauretche - Resultados elecciones 2017"

try:
    long_description = open('README.md').read()
except:
    long_description = description

url = 'https://gitlab.com/lajauretche/resultados'

setup(
    name='resultados',
    version=0.3,
    description=description,
    long_description=long_description,
    classifiers=classifiers,
    keywords='bigdata social programming',
    packages=find_packages('src'),
    package_dir={'':'src'},
    author="BigSocialData",
    author_email="info@bigsocialdata.es",
    url=url,
    download_url="{0}/tarball/master".format(url),
    license="MIT",
    install_requires=REQUIREMENTS,
    entry_points={
        'console_scripts': [
            "make_dataset = data.make_dataset:main",
            "runserver = web.app:do_runserver",
        ]
    },
    include_package_data=True,
    zip_safe=False
)