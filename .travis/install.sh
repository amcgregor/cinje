#!/bin/bash
set -e
set -x

git config --global user.email "alice+travis@gothcandy.com"
git config --global user.name "Travis: Marrow"

pip install --upgrade setuptools pytest
pip install tox
pip install python-coveralls
pip install pytest-cov
pip install pyflakes
pip install pytest_cagoule
pip install pytest-spec

if [ "${ACCELERATED}" = "1" ]; then
	pip install markupsafe
fi
