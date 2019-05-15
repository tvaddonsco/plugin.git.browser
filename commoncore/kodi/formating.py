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
import sys
import time

def utf8(string):
	try: 
		string = u'' + string
	except UnicodeEncodeError:
		string = u'' + string.encode('utf-8')
	except UnicodeDecodeError:
		string = u'' + string.decode('utf-8')
	return string

def format_size(num, suffix='B', split=False):
	num = float(num)
	for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
		if abs(num) < 1024.0:
			if split: return num, unit, suffix
			return "%3.1f %s%s" % (num, unit, suffix)
		num /= 1024.0
	if split: return num, unit, suffix
	return "%.1f %s%s" % (num, 'Y', suffix)

def size_to_bytes(num, unit='B'):
	unit = unit.upper()
	if unit.endswith('B'): unit = unit[:-1]
	units = ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']
	try: mult = pow(1024, units.index(unit))
	except: mult = sys.maxint
	return int(float(num) * mult)

def format_time(seconds, long=False):
	seconds = int(seconds)
	minutes, seconds = divmod(seconds, 60)
	if minutes > 60 or long:
		hours, minutes = divmod(minutes, 60)
		return "%02d:%02d:%02d" % (hours, minutes, seconds)
	else:
		return "%02d:%02d" % (minutes, seconds)

re_color = re.compile("(\[COLOR\s+[a-zA-Z]+\]|\[\/COLOR\])")
def format_color(string, color):
	string = re_color.sub('', string)
	return "[COLOR %s]%s[/COLOR]" % (color, string)

def highlight(string, subject, color):
	formated = "[COLOR %s]%s[/COLOR]" % (color, subject)
	return re.sub(subject, formated, string, re.IGNORECASE)

def format_trailer(trailer_url):
	if not trailer_url: return trailer_url
	match = re.search('\?v=(.*)', trailer_url)
	if match:
		return 'plugin://plugin.video.youtube/?action=play_video&videoid=%s' % (match.group(1))	