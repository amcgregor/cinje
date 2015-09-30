# encoding: utf-8

try:
	unicode = unicode
except:
	unicode = str

try:
	from markupsafe import Markup as bless, escape_silent as escape
except ImportError:
	bless = unicode
	from html import escape

from .util import iterate, xmlargs, interruptable as _interrupt


__all__ = ['unicode', 'bless', 'escape', 'iterate', 'xmlargs', '_interrupt']
