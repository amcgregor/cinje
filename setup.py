#!/usr/bin/env python3

import os
import sys
import codecs

from setuptools import setup, find_packages


if sys.version_info < (2, 7):
	raise SystemExit("Python 2.7 or later is required.")
elif sys.version_info > (3, 0) and sys.version_info < (3, 2):
	raise SystemExit("CPython 3.3 or Pypy 3 (3.2) or later is required.")

version = description = url = author = author_email = ""  # Silence linter warnings.
exec(open(os.path.join("cinje", "release.py")).read())  # Actually populate those values.

here = os.path.abspath(os.path.dirname(__file__))

tests_require = [
		'pytest',  # test collector and extensible runner
		'pytest-cov',  # coverage reporting
		'pytest-flakes',  # syntax validation
	]

if 'ACCELERATED' not in os.environ or os.environ.get('ACCELERATED', '1') != '0':
	tests_require.append('markupsafe')  # Data safety helper.


setup(
	name = "cinje",
	version = version,
	description = description,
	long_description = codecs.open(os.path.join(here, 'README.rst'), 'r', 'utf8').read(),
	url = url,
	download_url = 'https://github.com/marrow/cinje/releases',
	author = author.name,
	author_email = author.email,
	license = 'MIT',
	keywords = ['template', 'source translation', 'dsl', 'streaming', 'chunked'],
	classifiers = [
			"Development Status :: 5 - Production/Stable",
			"Environment :: Console",
			"Environment :: Web Environment",
			"Intended Audience :: Developers",
			"License :: OSI Approved :: MIT License",
			"Operating System :: OS Independent",
			"Programming Language :: Python :: 3",
			"Programming Language :: Python :: 3.8",
			"Programming Language :: Python :: 3.9",
			"Programming Language :: Python :: 3.10",
			"Programming Language :: Python :: Implementation :: CPython",
			"Programming Language :: Python :: Implementation :: PyPy",
			"Programming Language :: Python",
			"Topic :: Internet :: WWW/HTTP :: Dynamic Content",
			"Topic :: Internet :: WWW/HTTP :: WSGI",
			"Topic :: Software Development :: Libraries :: Python Modules",
			"Topic :: Software Development :: Libraries",
			"Topic :: Utilities",
		],
	
	packages = find_packages(),
	include_package_data = True,
	package_data = {'': ['README.rst', 'LICENSE.txt']},
	namespace_packages = [],
	zip_safe = True,
	
	entry_points = {
			'cinje.translator': [
					# Block Translators
					'function = cinje.block.function:Function',
					'generic = cinje.block.generic:Generic',
					'module = cinje.block.module:Module',
					'using = cinje.block.using:Using',
					
					# Inline Translators
					'blank = cinje.inline.blank:Blank',
					'code = cinje.inline.code:Code',
					'comment = cinje.inline.comment:Comment',
					'flush = cinje.inline.flush:Flush',
					'require = cinje.inline.require:Require',
					'text = cinje.inline.text:Text',
					'use = cinje.inline.use:Use',
					'pragma = cinje.inline.pragma:Pragma',
				],
		},
	
	setup_requires = [
			'pytest-runner',
		] if {'pytest', 'test', 'ptr'}.intersection(sys.argv) else [],
	install_requires = [],
	tests_require = tests_require,
	extras_require = {
			'development': tests_require + ['pre-commit'],  # Development requirements are the testing requirements.
			'safe': ['markupsafe'],  # String safety.
		},
)

