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

import re
def _getDOMContent(html, name, match, ret):  # Cleanup
	endstr = u"</" + name  # + ">"

	start = html.find(match)
	end = html.find(endstr, start)
	pos = html.find("<" + name, start + 1)

	while pos < end and pos != -1:  # Ignore too early </endstr> return
		tend = html.find(endstr, end + len(endstr))
		if tend != -1:
			end = tend
		pos = html.find("<" + name, pos + 1)

	if start == -1 and end == -1:
		result = u""
	elif start > -1 and end > -1:
		result = html[start + len(match):end]
	elif end > -1:
		result = html[:end]
	elif start > -1:
		result = html[start + len(match):]

	if ret:
		endstr = html[end:html.find(">", html.find(endstr)) + 1]
		result = match + result + endstr

	return result

def _getDOMAttributes(match, name, ret):
	lst = re.compile('<' + name + '.*?' + ret + '=([\'"].[^>]*?[\'"])>', re.M | re.S).findall(match)
	if len(lst) == 0:
		lst = re.compile('<' + name + '.*?' + ret + '=(.[^>]*?)>', re.M | re.S).findall(match)
	ret = []
	for tmp in lst:
		cont_char = tmp[0]
		if cont_char in "'\"":
			# Limit down to next variable.
			if tmp.find('=' + cont_char, tmp.find(cont_char, 1)) > -1:
				tmp = tmp[:tmp.find('=' + cont_char, tmp.find(cont_char, 1))]

			# Limit to the last quotation mark
			if tmp.rfind(cont_char, 1) > -1:
				tmp = tmp[1:tmp.rfind(cont_char)]
		else:
			if tmp.find(" ") > 0:
				tmp = tmp[:tmp.find(" ")]
			elif tmp.find("/") > 0:
				tmp = tmp[:tmp.find("/")]
			elif tmp.find(">") > 0:
				tmp = tmp[:tmp.find(">")]

		ret.append(tmp.strip())
	return ret

def _getDOMElements(item, name, attrs):
	lst = []
	for key in attrs:
		lst2 = re.compile('(<' + name + '[^>]*?(?:' + key + '=[\'"]' + attrs[key] + '[\'"].*?>))', re.M | re.S).findall(item)
		if len(lst2) == 0 and attrs[key].find(" ") == -1:  # Try matching without quotation marks
			lst2 = re.compile('(<' + name + '[^>]*?(?:' + key + '=' + attrs[key] + '.*?>))', re.M | re.S).findall(item)

		if len(lst) == 0:
			lst = lst2
			lst2 = []
		else:
			test = range(len(lst))
			test.reverse()
			for i in test:  # Delete anything missing from the next list.
				if not lst[i] in lst2:
					del(lst[i])

	if len(lst) == 0 and attrs == {}:
		lst = re.compile('(<' + name + '>)', re.M | re.S).findall(item)
		if len(lst) == 0:
			lst = re.compile('(<' + name + ' .*?>)', re.M | re.S).findall(item)

	return lst

def parse_dom(html, name=u"", attrs={}, ret=False):

	if isinstance(name, str):  # Should be handled
		try:
			name = name   # .decode("utf-8")
		except:
			pass

	if isinstance(html, str):
		try:
			html = [html.decode("utf-8")]  # Replace with chardet thingy
		except:
			html = [html]
	elif isinstance(html, unicode):
		html = [html]
	elif not isinstance(html, list):
		return u""

	if not name.strip():
		return u""

	ret_lst = []
	for item in html:
		temp_item = re.compile('(<[^>]*?\n[^>]*?>)').findall(item)
		for match in temp_item:
			item = item.replace(match, match.replace("\n", " "))

		lst = _getDOMElements(item, name, attrs)

		if isinstance(ret, str):
			lst2 = []
			for match in lst:
				lst2 += _getDOMAttributes(match, name, ret)
			lst = lst2
		else:
			lst2 = []
			for match in lst:
				temp = _getDOMContent(item, name, match, ret).strip()
				item = item[item.find(temp, item.find(match)) + len(temp):]
				lst2.append(temp)
			lst = lst2
		ret_lst += lst

	return ret_lst

def get_attribute(html, name):
	lst = re.compile(name + '\s*=\s*"([^"]+)"', re.IGNORECASE).findall(html)
	if len(lst) == 0:
		lst = re.compile(name + "\s*=\s*'([^']+)'", re.IGNORECASE).findall(html) # Try with single quotes
	if len(lst) == 0: return ""
	else: return lst
		
class DomParserException(Exception):
	pass

class DomObject(object):
	_html = ''
	def __init__(self, html):
		self._html = html
	
	def __str__(self):
		return self.html()

	def html(self):
		return self._html.encode('utf-8')

	def find_all(self, name=u"", attrs={}):
		lst = self._parse_dom(self._html, name, attrs, True)
		return lst
	
	def find(self, name=u"", attrs={}):
		lst = self._parse_dom(self._html, name, attrs, True)
		if len(lst) == 0 : return u""
		return lst[0]

	def content(self, name=u""):
		if not name:
			name = re.search("<(\w+)[^>]*>", self._html).group(1)
		lst = self._parse_dom(self._html, name, {}, False)
		if len(lst) == 0 : return u""
		return lst[0].html()

	def attribute(self, name):
		lst = re.compile(name + '\s*=\s*"([^"]+)"', re.IGNORECASE).findall(self._html)
		if len(lst) == 0:
			lst = re.compile(name + "\s*=\s*'([^']+)'", re.IGNORECASE).findall(self._html) # Try with single quotes
		if len(lst) == 0: return ""
		else: return lst[0]

	def _parse_dom(self, html, name=u"", attrs={}, ret=False):

		if isinstance(name, str):  # Should be handled
			try:
				name = name   # .decode("utf-8")
			except:
				pass

		if isinstance(html, str):
			try:
				html = [html.decode("utf-8")]  # Replace with chardet thingy
			except:
				html = [html]
		elif isinstance(html, unicode):
			html = [html]
		elif not isinstance(html, list):
			return u""

		if not name.strip():
			return u""

		ret_lst = []
		for item in html:
			temp_item = re.compile('(<[^>]*?\n[^>]*?>)', re.I).findall(item)
			for match in temp_item:
				item = item.replace(match, match.replace("\n", " "))

			lst = self._getDOMElements(item, name, attrs)

			if isinstance(ret, str):
				lst2 = []
				for match in lst:
					lst2 += self._getDOMAttributes(match, name, ret)
				lst = lst2
			else:
				lst2 = []
				for match in lst:
					temp = self._getDOMContent(item, name, match, ret) #.strip()
					item = item[item.find(temp, item.find(match)) + len(temp):]
					lst2.append(temp)
				lst = lst2
			ret_lst += lst

		return [DomObject(l) for l in ret_lst]

	def _getDOMContent(self, html, name, match, ret):  # Cleanup
		endstr = u"</" + name  # + ">"

		start = html.find(match)
		end = html.find(endstr, start)
		pos = html.find("<" + name, start + 1)

		while pos < end and pos != -1:  # Ignore too early </endstr> return
			tend = html.find(endstr, end + len(endstr))
			if tend != -1:
				end = tend
			pos = html.find("<" + name, pos + 1)

		if start == -1 and end == -1:
			result = u""
		elif start > -1 and end > -1:
			result = html[start + len(match):end]
		elif end > -1:
			result = html[:end]
		elif start > -1:
			result = html[start + len(match):]

		if ret:
			endstr = html[end:html.find(">", html.find(endstr)) + 1]
			result = match + result + endstr

		return result

	def _getDOMAttributes(self, match, name, ret):
		lst = re.compile('<' + name + '.*?' + ret + '=([\'"].[^>]*?[\'"])>', re.M | re.S).findall(match)
		if len(lst) == 0:
			lst = re.compile('<' + name + '.*?' + ret + '=(.[^>]*?)>', re.M | re.S).findall(match)
		ret = []
		for tmp in lst:
			cont_char = tmp[0]
			if cont_char in "'\"":
				# Limit down to next variable.
				if tmp.find('=' + cont_char, tmp.find(cont_char, 1)) > -1:
					tmp = tmp[:tmp.find('=' + cont_char, tmp.find(cont_char, 1))]

				# Limit to the last quotation mark
				if tmp.rfind(cont_char, 1) > -1:
					tmp = tmp[1:tmp.rfind(cont_char)]
			else:
				if tmp.find(" ") > 0:
					tmp = tmp[:tmp.find(" ")]
				elif tmp.find("/") > 0:
					tmp = tmp[:tmp.find("/")]
				elif tmp.find(">") > 0:
					tmp = tmp[:tmp.find(">")]

			ret.append(tmp.strip())
		return ret

	def _getDOMElements(self, item, name, attrs):
		lst = []
		for key in attrs:
			lst2 = re.compile('(<' + name + '[^>]*?(?:' + key + '=[\'"]' + attrs[key] + '[\'"].*?>))', re.M | re.S).findall(item)
			if len(lst2) == 0 and attrs[key].find(" ") == -1:  # Try matching without quotation marks
				lst2 = re.compile('(<' + name + '[^>]*?(?:' + key + '=' + attrs[key] + '.*?>))', re.M | re.S).findall(item)

			if len(lst) == 0:
				lst = lst2
				lst2 = []
			else:
				test = range(len(lst))
				test.reverse()
				for i in test:  # Delete anything missing from the next list.
					if not lst[i] in lst2:
						del(lst[i])

		if len(lst) == 0 and attrs == {}:
			lst = re.compile('(<' + name + '>)', re.M | re.S).findall(item)
			if len(lst) == 0:
				lst = re.compile('(<' + name + ' .*?>)', re.M | re.S).findall(item)

		return lst

def parse_html(html):
	return DomObject(html)	
		
