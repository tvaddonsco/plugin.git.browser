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

import kodi
from xbmc import log as __log
from xbmc import LOGDEBUG, LOGERROR, LOGFATAL, LOGINFO, LOGNONE, LOGNOTICE, LOGSEVERE, LOGWARNING

def log(msg, level=LOGNOTICE):
	try:
		if isinstance(msg, unicode):
			msg = msg.encode('utf-8')
		__log('%s: %s' % (kodi.get_name(), msg), level)
	except Exception as e:
		try: __log('Logging Failure: %s' % (e), level)
		except: pass  # just give up