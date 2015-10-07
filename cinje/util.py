# encoding: utf-8

from __future__ import unicode_literals

"""Convienent utilities."""

# ## Imports

import sys

from inspect import isfunction, isclass
from collections import deque, namedtuple, Sized, Iterable
from xml.sax.saxutils import quoteattr


# ## Python Cross-Compatibility

try:  # pragma: no cover
	from types import StringTypes as stringy
	bytes = str
	str = unicode
	py = 2
except:
	stringy = str
	py = 3


# ## Type Definitions


Iteration = namedtuple('Iteration', ['first', 'last', 'index', 'total', 'value'])



# ## Simple Utility Functions


def interruptable(iterable):
	"""Allow easy catching of a generator interrupting operation when using "yield from"."""
	
	for i in iterable:
		if i is None:
			return
		
		yield i


def iterate(obj):
	"""Loop over an iterable and track progress, including first and last state.
	
	On each iteration yield an Iteration named tuple with the first and last flags, current element index, total
	iterable length (if possible to acquire), and value, in that order.
	
		for iteration in iterate(something):
			iteration.value  # Do something.
	
	You can unpack these safely:
	
		for first, last, index, total, value in iterate(something):
			pass
	
	If you want to unpack the values you are iterating across, you can by wrapping the nested unpacking in parenthesis:
	
		for first, last, index, total, (foo, bar, baz) in iterate(something):
			pass
	
	Even if the length of the iterable can't be reliably determined this function will still capture the "last" state
	of the final loop iteration.  (Basically: this works with generators.)
	
	This process is about 10x slower than simple enumeration on CPython 3.4, so only use it where you actually need to
	track state.  Use `enumerate()` elsewhere.
	"""
	
	total = len(obj) if isinstance(obj, Sized) else None
	iterator = iter(obj)
	first = True
	last = False
	i = 0
	
	try:
		value = next(iterator)
	except StopIteration:
		return
	
	while True:
		try:
			next_value = next(iterator)
		except StopIteration:
			last = True
		
		yield Iteration(first, last, i, total, value)
		if last: return
		
		value = next_value
		i += 1
		first = False


def xmlargs(_source=None, **values):
	from cinje.helpers import bless
	
	parts = []
	
	# If a data source is provided it overrides the keyword arguments which are treated as defaults.
	if _source:
		values.update(_source)
	
	for k in sorted(values):
		# We technically allow non-string values for keys.  They're just converted to strings first.
		key = str(k).rstrip('_').replace('__', ':').replace('_', '-')
		value = values[k]
		
		# We skip empty, None, False, and other falsy values other than zero.
		if k[0] == '_' or (not value and (value is False or value != 0)):  # False == 0, so, uh, work around that.
			continue
		
		if value is True:  # For explicitly True values, we don't have a value for the attribute.
			parts.append(key)
			continue
		
		# Non-string iterables (such as lists, sets, tuples, etc.) are treated as space-separated strings.
		if isinstance(value, Iterable) and not isinstance(value, stringy):
			value = " ".join(str(i) for i in value)
		
		parts.append(key + "=" + quoteattr(str(value)))
	
	return bless(" " + " ".join(parts)) if parts else ''


def chunk(text, delim=('', '${', '#{', '&{', '%{'), tag=('text', '_escape', '_bless', '_args', 'format')):
	"""Chunkify and "tag" a block of text into plain text and code sections.
	
	The first delimeter is blank to represent text sections, and keep the indexes aligned with the tags.
	
	Values are yielded in the form (tag, text).
	"""
	
	skipping = 0  # How many closing parenthesis will we need to skip?
	start = None  # Starting position of current match.
	last = 0
	
	i = 0
	
	while i < len(text):
		if start is not None:
			if text[i] == '{':
				skipping += 1
			
			elif text[i] == '}':
				if skipping:
					skipping -= 1
				else:
					yield tag[delim.index(text[start-2:start])], text[start:i]
					start = None
					last = i = i + 1
					continue
		
		elif text[i:i+2] in delim:
			if last is not None and last != i:
				yield tag[0], text[last:i]
				last = None
			
			start = i = i + 2
			continue
		
		i += 1
	
	if last < len(text):
		yield tag[0], text[last:]


def ensure_buffer(context):
	if 'text' in context.flag:
		return
	
	# TODO: Determine if the Python 2-required approach (reassignment) is faster than the .clear() approach.
	
	yield Line(0, "")
	yield Line(0, "_buffer = []")
	yield Line(0, "__w = _buffer.extend")
	yield Line(0, "")
	
	context.flag.add('text')



# ## Common Classes


class Line(object):
	"""A rich description for a line of input, allowing for annotation."""
	
	__slots__ = ('number', 'line', 'scope', 'kind', 'continued')
	
	def __init__(self, number, line, scope=None):
		self.number = number
		self.line = line
		self.scope = scope
		self.kind = None
		self.continued = self.stripped.endswith('\\')
		
		self.process()
		
		super(Line, self).__init__()
	
	def process(self):
		if self.stripped.startswith('#'):
			self.kind = 'comment'
		elif self.stripped.startswith(':'):
			self.kind = 'code'
			self.line = self.stripped[1:].lstrip()
		else:
			self.kind = 'text'
	
	@property
	def stripped(self):
		return self.line.strip()
	
	@property
	def partitioned(self):
		prefix, _, remainder = self.stripped.partition(' ')
		return prefix.rstrip(), remainder.lstrip()
	
	def __repr__(self):
		return '{0.__class__.__name__}({0.number}, {0.kind}, "{0.stripped}")'.format(self)
	
	def __bytes__(self):
		return str(self).encode('utf8')
	
	def __str__(self):
		if self.scope is None:
			return self.line
		
		return '\t' * self.scope + self.line.lstrip()
	
	if py == 2:  # pragma: no cover
		__unicode__ = __str__
		__str__ = __bytes__
		del __bytes__
	
	def clone(self, **kw):
		values = dict(
				number = self.number,
				line = self.line,
				scope = self.scope,
			)
		
		values.update(kw)
		
		instance = self.__class__(**values)
		
		return instance


class Lines(object):
	"""Iterate input lines of source, with the ability to push lines back."""
	
	__slots__ = ['Line', 'source', 'buffer']
	
	def __init__(self, input=None, Line=Line):
		self.Line = Line
		
		if input is None:
			self.source = None
			self.buffer = deque()
		
		elif hasattr(input, 'readlines'):
			self.source = list(self.Line(i + 1, j) for i, j in enumerate(input.readlines()))
			self.buffer = deque(self.source)
		
		else:
			self.source = list(self.Line(i + 1, j) for i, j in enumerate(input.split('\n')))
			self.buffer = deque(self.source)
		
		super(Lines, self).__init__()
	
	@property
	def count(self):
		return len(self.buffer)
	
	def __len__(self):
		return self.count
	
	def __repr__(self):
		return 'Lines({0.count})'.format(self)
	
	def __iter__(self):
		return self
	
	def __next__(self):
		return self.next()
	
	def __str__(self):
		return "\n".join(str(i) for i in self)
	
	def next(self):
		if not self.buffer:
			raise StopIteration()
		
		return self.buffer.popleft()
	
	def peek(self):
		return self.buffer[0] if self.buffer else None
	
	def push(self, *lines):
		self.buffer.extendleft((i if isinstance(i, self.Line) else self.Line(self.buffer[0].number if self.buffer else 0, i)) for i in reversed(lines))
	
	def reset(self):
		self.buffer = deque(self.source)
	
	def append(self, *lines):
		self.buffer.extend((i if isinstance(i, self.Line) else self.Line(self.buffer[-1].number if self.buffer else 0, i)) for i in lines)


class Context(object):
	"""The processing context for translating cinje source into Python source.
	
	This is the primary entry point for translation.
	"""
	
	__slots__ = ('input', 'scope', 'flag', '_handler')
	
	handlers = []
	
	def __init__(self, input):
		self.input = Lines(input.decode('utf8') if hasattr(input, 'decode') else input)
		self.scope = 0
		self.flag = set()
		self._handler = []
	
	def __repr__(self):
		return "Context({!r}, {}, {})".format(self.input, self.scope, self.flag)
	
	@classmethod
	def register(cls, handler):
		"""Register a line transformer class with the processing context."""
		
		assert isclass(handler), "Must supply handler class for registration, not instance."
		
		cls.handlers.append(handler)
		
		return handler  # Allow certain types of chaining, i.e. use as a decorator.
	
	def prepare(self):
		"""Prepare the ordered list of transformers and reset context state to initial."""
		self.scope = 0
		self._handler = [i() for i in sorted(self.handlers, key=lambda handler: handler.priority)]
	
	@property
	def stream(self):
		"""The workhorse of cinje: transform input lines and emit output lines.
		
		After constructing an instance with a set of input lines iterate this property to generate the template.
		"""
		
		if 'init' not in self.flag:
			self.prepare()
		
		for line in self.input:
			handler = self.classify(line)
			
			if line.kind == 'code' and line.stripped == 'end':  # Exit the current child scope.
				return
			
			assert handler, "Unable to identify handler for line; this should be impossible!"
			
			self.input.push(line)  # Put it back so it can be consumed by the handler.
			
			for line in handler(self):  # This re-indents the code to match, if missing explicit scope.
				if line.scope is None:
					line = line.clone(scope=self.scope)
				
				yield line
	
	def classify(self, line):
		"""Identify the correct handler for a given line of input."""
		
		for handler in self._handler:
			if handler.match(self, line):
				return handler
		
		return None


class Pipe(object):
	"""An object representing a pipe-able callable, optionally with preserved arguments.
	
	Using this you can custruct custom subclasses (define a method named "callable") or use it as a decorator:
	
		@Pipe
		def s(text):
			return str(text)
	
	"""
	
	__slots__ = ('callable', 'args', 'kwargs')
	
	def __init__(self, callable, *args, **kw):
		super(Pipe, self).__init__()
		
		self.callable = callable
		self.args = args if args else ()
		self.kwargs = kw if kw else {}
	
	def __ror__(self, other):
		"""The main machinery of the Pipe, calling the chosen callable with the recorded arguments."""
		
		return self.callable(*(self.args + (other, )), **self.kwargs)
	
	def __call__(self, *args, **kw):
		"""Allow for the preserved args and kwargs to be updated, returning a mutated copy.
		
		This allows for usage with arguments, as in the following example:
		
			"Hello!" | encode('utf8')
		
		This also allows for easy construction of custom mutated copies for use later, a la:
		
			utf8 = encode('utf8')
			"Hello!" | utf8
		"""
		
		return self.__class__(self.callable, *args, **kw)
