import sys
import os

from setuptools import setup, find_packages

setup(
    name = 'freecad_gear',
    version = '0.3',
    packages = ["freecad_gear", "freecad_gear/freecad/", "freecad_gear/gearfunc/"],
    include_package_data=True,
    description = 'Some gears for freecad',
    author = 'Lorenz L',
    author_email = 'sppedflyer@gmail.com',
    url = 'https://github.com/looooo/FCGear',
    download_url = 'https://github.com/looooo/FCGear/tarball/0.3',
    keywords = ['gear', 'freecad'],
    classifiers = [],
)