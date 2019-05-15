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

import json
import zlib
from . import vfs

try:
	import cPickle as _pickle
except:
	import pickle  as _pickle

pickle = _pickle.dumps

def unpickle(pickled):
	try:
		return _pickle.loads(pickled)
	except TypeError:
		return _pickle.loads(str(pickled))

def save_data(file, data, format='pickle', compress=False):
	if format == 'pickle':
		if compress:
			data =  zlib.compress(pickle(data))
		else:
			data = pickle(data)
		vfs.write_file(file, data, mode='b')
	else:
		data = json.dumps(data)
		if compress:
			data = zlib.compress(data)
		vfs.write_file(file, data)
		
def load_data(file, format='pickle', compress=False):
	if format == 'pickle':
		try:
			data = vfs.read_file(file, mode='b')
			if compress:
				data = zlib.decompress(data)
			return unpickle(data)
		except Exception as e:
			return None
	else:
		try:
			data = vfs.read_file(file)
			if compress:
				data = zlib.decompress(data)
			return json.loads()
		except Exception as e:
			return None	