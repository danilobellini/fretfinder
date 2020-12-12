#!/usr/bin/env python3
import ast
import os

import setuptools


setup_path = os.path.dirname(__file__)

# Get __version__ from the package __init__.py without importing it
with open(os.path.join(setup_path, "fretfinder", "__init__.py")) as dinit:
    assignment_node = next(el for el in ast.parse(dinit.read()).body
                           if isinstance(el, ast.Assign)
                           and el.targets[0].id == "__version__")
    version = ast.literal_eval(assignment_node.value)

with open(os.path.join(setup_path, "README.md")) as readme:
    long_description = readme.read()


setuptools.setup(
    name="fretfinder",
    version=version,
    author="Danilo de Jesus da Silva Bellini",
    author_email="danilo.bellini@gmail.com",
    url="https://github.com/danilobellini/fretfinder",
    description="Adaptive guitar fret finder algorithm implementation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(exclude=["tests"]),
    include_package_data=True,
    python_requires=">=3.7",
    install_requires=["audiolazy", "click"],
    entry_points={
        "console_scripts": ["fretfinder = fretfinder.__main__:main"]
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Multimedia :: Sound/Audio :: MIDI",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Operating System :: OS Independent",
    ],
)
