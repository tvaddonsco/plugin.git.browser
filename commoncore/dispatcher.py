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

from .kodi.logger import log

class FunctionDispatcher():
	__functions = {}
	__args = {}
	__kwargs = {}

	def register(self, mode, args=[], kwargs={}):
		def decorator(target):
			for foo in args:
				args[args.index(foo)] = self.__coerce(foo)
			for foo in kwargs:
				kwargs[foo] = self.__coerce(kwargs[foo])
			if isinstance(mode, list):
				for foo in mode:
					self.__functions[foo] = target
					self.__args[foo] = args
					self.__kwargs[foo] = kwargs
			else:
				self.__functions[mode] = target
				self.__args[mode] = args
				self.__kwargs[mode] = kwargs
			return target
		return decorator
	
	def __coerce(self, v):
		test = v.lower()
		if test == 'none': return None
		if test == 'false': return False
		if test == "true": return True
		return v
	
	def error(self):
		pass
	
	def run(self, mode='default', condition=None):
		if mode is None or mode == '' or mode is False:
			mode = 'default'
		if mode in self.__functions:
			if condition is not None and condition is False: return
			args = self.__args[mode]
			kwargs = self.__kwargs[mode]
			return self.__functions[mode](*args, **kwargs)
		else:
			log( "Illegal mode: %s" % mode)
			self.error()

class WeightedDispatcher():
	__functions = {}
	__args = {}
	__kwargs = {}
	__fail_result = ''
	__high_first = True
	
	def register(self, weight, args=[], kwargs={}):
		def decorator(target):
			for foo in args:
				args[args.index(foo)] = self.__coerce(foo)
			for foo in kwargs:
				kwargs[foo] = self.__coerce(kwargs[foo])
			if weight in self.__functions:
				self.__functions[weight] += [target]
				self.__args[weight] += [args]
				self.__kwargs[weight] += [kwargs]
			else:
				self.__functions[weight] = [target]
				self.__args[weight] = [args]
				self.__kwargs[weight] = [kwargs]
			return target
		return decorator
	
	def __coerce(self, v):
		test = v.lower()
		if test == 'none': return None
		if test == 'false': return False
		if test == "true": return True
		return v
	
	def validate_result(self, ret):
		if ret is '' or ret is None or ret is False:
			return False
		return True
	
	def run(self):
		for index in sorted(self.__functions.iterkeys(), reverse=self.__high_first):
			container = self.__functions[index]
			for foo in container:
				args = tuple(self.__args[index][container.index(foo)])
				kwargs = self.__kwargs[index][container.index(foo)]
				ret = foo(*args, **kwargs)
				if self.validate_result(ret): return ret
		return self.__fail_result
dispatcher = FunctionDispatcher()

