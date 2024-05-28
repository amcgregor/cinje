# encoding: utf-8

from __future__ import unicode_literals

from zlib import compress
from base64 import b64encode
from collections import deque

from ..util import py, Line


def red(numbers):
	"""Encode the deltas to reduce entropy."""
	
	line = 0
	deltas = []
	
	for value in numbers:
		deltas.append(value - line)
		line = value
	
	return b64encode(compress(b''.join(chr(i).encode('latin1') for i in deltas))).decode('latin1')



class Module(object):
	"""Module handler.
	
	This is the initial scope, and the highest priority to ensure its processing of the preamble happens first.
	"""
	
	priority = -100
	
	def match(self, context, line):
		return 'init' not in context.flag
	
	def __call__(self, context):
		input = context.input
		
		context.flag.add('init')
		context.flag.add('buffer')
		
		imported = False
		
		for line in input:
			if not line.stripped or line.stripped[0] == '#':
				if not line.stripped.startswith('##') and 'coding:' not in line.stripped:
					yield line
				continue
			
			input.push(line)  # We're out of the preamble, so put that line back and stop.
			break
		
		# After any existing preamble, but before other imports, we inject our own.
		
		if py == 2:
			yield Line(0, 'from __future__ import unicode_literals')
			yield Line(0, '')
		
		yield Line(0, 'import cinje')
		yield Line(0, 'from cinje.helpers import escape as _escape, bless as _bless, iterate, xmlargs as _args, _interrupt, _json')
		yield Line(0, '')
		yield Line(0, '')
		yield Line(0, '__tmpl__ = []  # Exported template functions.')
		yield Line(0, '')
		
		for i in context.stream:
			yield i
		
		if context.templates:
			yield Line(0, '')
			yield Line(0, '__tmpl__.extend(["' + '", "'.join(context.templates) + '"])')
			context.templates = []
		
		# Snapshot the line number mapping.
		mapping = deque(context.mapping)
		mapping.reverse()
		
		yield Line(0, '')
		
		#if __debug__:
		#	yield Line(0, '__mapping__ = [' + ','.join(str(i) for i in mapping) + ']')
		
		#yield Line(0, '__gzmapping__ = b"' + red(mapping).replace('"', '\"') + '"')
		
		context.flag.remove('init')
