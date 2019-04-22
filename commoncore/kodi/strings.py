import sys
import inspect

PY2 = sys.version_info[0] == 2  #: ``True`` for Python 2
PY3 = sys.version_info[0] == 3  #: ``True`` for Python 3

def stringify(obj, encoding='utf-8'):
	if not isinstance(obj, str):
		obj = str(obj)
	if PY2 and isinstance(obj, unicode):
		obj = obj.encode(encoding)
	elif PY3:
		obj = obj.encode(encoding)
	return obj

def bytefy(obj, encoding='utf8'):
	if PY3 and isinstance(obj, str):
		obj = obj.encode(encoding)
	elif PY2 and isinstance(obj, unicode):
		obj = obj.encode(encoding)
	return obj

def str_decode(obj, encoding='utf8'):
	if PY3:
		import xbmc
		xbmc.log(str(type(obj)), xbmc.LOGNOTICE)
		obj = str(encoding)
	return obj
	