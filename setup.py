#!/usr/bin/env python
from setuptools import setup, find_packages
from tint import version

setup(
    name="tint",
    version=version,
    description="Tint is an experimental communications network that enables friend-to-friend (F2F) communication via a simple protocol.",
    author="Brian Muller",
    author_email="bamuller@gmail.com",
    license="MIT",
    url="http://github.com/bmuller/tint",
    packages=find_packages(),
    requires=["twisted", "umsgpack"],
    install_requires=['twisted>=12.0', "u-msgpack-python>=1.5"]
)
