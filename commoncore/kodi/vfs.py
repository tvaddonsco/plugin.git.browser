# -*- coding: utf-8 -*-

'''*
	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
*'''

import os
import sys
import re
import string
import unicodedata
import xbmc
import xbmcgui
import xbmcvfs
from xml.etree import ElementTree
root = '/'
debug = False

PY2 = sys.version_info[0] == 2  #: ``True`` for Python 2
PY3 = sys.version_info[0] == 3  #: ``True`` for Python 3

def _resolve_path(path):
	return path.replace('/', os.sep)	

def confirm(msg='', msg2='', msg3=''):
	dialog = xbmcgui.Dialog()
	return dialog.yesno(msg, msg2, msg3)

def _open(path, mode='r'):
	try:
		return xbmcvfs.File(path, mode)
	except Exception as e:
		xbmc.log('******** VFS error: %s' % e)
		return False

def read_file(path, soup=False, json=False, mode=''):
	try:
		if mode=='b':
			file = _open(path, 'rb')
		else:
			file = _open(path, 'r')
		content=file.read()
		file.close()
		if soup:
			from commoncore.beautifulsoup import BeautifulSoup
			soup = BeautifulSoup(content)
			return soup
		elif json:
			try: 
				import simplejson as json
			except ImportError: 
				import json
			return json.loads(content)
		else:
			return content
	except IOError as e:
		xbmc.log('******** VFS error: %s' % e)
		return None

def write_file(path, content, mode='w', json=False):
	try:
		if json: 
			import json
			content = json.dumps(content)

		if mode=='b':
			file = _open(path, 'wb')
		else:
			file = _open(path, 'w')
		if PY3 and type(content) is not str:
			content = str(content)
		file.write(content)
		file.close()
		return True
	except IOError as e:
		xbmc.log('******** VFS error: %s' % e)
		return False

def clean_file_name(filename):
	filename = unicode(filename)
	validFilenameChars = "-_.() %s%s" % (string.ascii_letters, string.digits)
	cleanedFilename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore')
	return ''.join(c for c in cleanedFilename if c in validFilenameChars)
	
def touch(path):
	try:
		if exists(path):
			_open(path, 'r')
			return True
		else:
			_open(path, 'w')
			return True
	except Exception as e:
		xbmc.log('******** VFS error: %s' % e)
		return False


def get_stat(path):
	return xbmcvfs.Stat(path)

def get_size(path):
	return xbmcvfs.Stat(path).st_size()

def get_mtime(path):
	return xbmcvfs.Stat(path).st_mtime()

def get_ctime(path):
	return xbmcvfs.Stat(path).st_ctime()

def get_atime(path):
	return xbmcvfs.Stat(path).st_atime()

def path_parts(path):
	from urlparse import urlparse
	temp = urlparse(path)
	filename, file_extension = os.path.splitext(temp[2])
	result = {"scheme": temp[0], "host": temp[1], "path": filename, "extension": file_extension.replace('.', '')}
	return result
	
def exists(path):
	return xbmcvfs.exists(path)

def dirname(path):
	return os.path.dirname(path)

def abspath(path):
	return os.path.abspath(path)

def basename(path):
	return os.path.basename(path)

def filename(path):
	return os.path.split(path)[-1]

def ls(path, pattern=None, inlcude_path=False):
	try:
		if pattern:
			s = re.compile(pattern)
			folders = []
			files = []
			temp = xbmcvfs.listdir(path)
			for test in temp[0]:
				if s.search(str(test)):
					if inlcude_path: test = join(path, test)
					folders.append(test)
			for test in temp[1]:
				if s.search(str(test)):
					if inlcude_path: test = join(path, test)
					files.append(test)
			return [folders, files]
		else:
			return xbmcvfs.listdir(path)
	except Exception as e:
		xbmc.log('******** VFS error: %s' % e)
		return False

def mkdir(path, recursive=False):
	if exists(path):
		if debug:
			xbmc.log('******** VFS mkdir notice: %s exists' % path)
		return False
	if recursive:
		try:
			return xbmcvfs.mkdirs(path)
		except Exception as e:
			xbmc.log('******** VFS error: %s' % e)
			return False
	else:
		try:
			return xbmcvfs.mkdir(path)
		except Exception as e:
			xbmc.log('******** VFS error: %s' % e)
			return False

def rmdir(path, quiet=False):
	if not exists(path):
		if debug:
			xbmc.log('******** VFS rmdir notice: %s does not exist' % path)
		return False
	if not quiet:
		msg = 'Remove Directory'
		msg2 = 'Please confirm directory removal!'
		if not confirm(msg, msg2, path): return False
	try:		
		xbmcvfs.rmdir(path)
	except Exception as e:
		xbmc.log('******** VFS error: %s' % e)

def rm(path, quiet=False, recursive=False):
	if not exists(path):
		if debug:
			xbmc.log('******** VFS rmdir notice: %s does not exist' % path)
		return False
	if not quiet:
		msg = 'Confirmation'
		msg2 = 'Please confirm directory removal!'
		if not confirm(msg, msg2, path): return False

	if not recursive:
		try:
			xbmcvfs.delete(path)
		except Exception as e:
			xbmc.log('******** VFS error: %s' % e)
	else:
		dirs,files = ls(path)
		for f in files:
			r = os.path.join(xbmc.translatePath(path), f)
			try:
				xbmcvfs.delete(r)
			except Exception as e:
				xbmc.log('******** VFS error: %s' % e)
		for d in dirs:
			subdir = os.path.join(xbmc.translatePath(path), d)
			rm(subdir, quiet=True, recursive=True)
		try:			
			xbmcvfs.rmdir(path)
		except Exception as e:
			xbmc.log('******** VFS error: %s' % e)
	return True

def rename(src, dest, quiet=False):
	if not quiet:
		msg = 'Confirmation'
		msg2 = 'Please confirm rename file!'
		if not confirm(msg, msg2, src): return False
	xbmcvfs.rename(src, dest)
	
def cp(src, dest):
	return xbmcvfs.copy(src, dest)

def mv(src, dest):
	c = cp(src, dest)
	if c:
		r = rm(src, quiet=True)
	else: return False
	return r

def translate_path(path):
	return xbmc.translatePath( path )

def join(path, filename, preserve=False):
	path = path.replace('/', os.sep)
	if filename.startswith('/'): filename=filename[1:]
	if not preserve:
		translatedpath = os.path.join(xbmc.translatePath( path ), ''+filename+'')
	else:
		translatedpath = os.path.join(path, ''+filename+'')
	return translatedpath

open = _open

