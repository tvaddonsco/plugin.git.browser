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

import sys
import xbmcaddon
from .enum import enum
from . import vfs
__addon = xbmcaddon.Addon()
__get_setting = __addon.getSetting
__set_setting = __addon.setSetting

def get_setting(k, addon_id=None):
	if addon_id is None:
		return __get_setting(k)
	else:
		return xbmcaddon.Addon(addon_id).getSetting(k)

def set_setting(k, v, addon_id=None):
	if not isinstance(v, str): v = str(v)
	if addon_id is None:
		return __set_setting(k, v)
	else:
		return xbmcaddon.Addon(addon_id).setSetting(k, v)

try:
	HANDLE_ID = int(sys.argv[1])
	ADDON_URL = sys.argv[0]
	PLUGIN_URL = sys.argv[0] + sys.argv[2]
except:
	HANDLE_ID = -1
	ADDON_URL = 'plugin://%s' % sys.argv[0]
	PLUGIN_URL = 'plugin://%s' % sys.argv[0]

PLATFORM = sys.platform
ARTWORK = vfs.join(__addon.getAddonInfo('path'), 'resources/artwork')

try:
	client_host = '127.0.0.1'
	client_port = get_setting('control_port', 'service.fanart.proxy')
	client_protocol = get_setting('control_protocol', 'service.fanart.proxy')
	BASE_FANART_URL = '%s://%s:%s/api/images' % (client_protocol, client_host, client_port) 
except:
	BASE_FANART_URL = ''

DEFAULT_VIEW = 550	
DEFAULT_VIEWS = enum(
	DEFAULT= DEFAULT_VIEW, 
	LIST= int(get_setting('default_list_view')) if get_setting('default_list_view') else DEFAULT_VIEW, 
	FOLDER= int(get_setting('default_folder_view')) if get_setting('default_folder_view') else DEFAULT_VIEW, 
	MOVIES= int(get_setting('default_movie_view')) if get_setting('default_movie_view') else DEFAULT_VIEW, 
	SHOWS= int(get_setting('default_show_view')) if get_setting('default_show_view') else DEFAULT_VIEW, 
	SEASONS= int(get_setting('default_season_view')) if get_setting('default_season_view') else DEFAULT_VIEW, 
	EPISODES= int(get_setting('default_episode_view')) if get_setting('default_episode_view') else DEFAULT_VIEW,
	STREAMS= int(get_setting('default_stream_view')) if get_setting('default_stream_view') else DEFAULT_VIEW, 
	GAMES= int(get_setting('default_game_view')) if get_setting('default_game_view') else DEFAULT_VIEW, 
)

BROWSER_TYPES = enum(DIRECTORY=0, FILE=1, IMAGE=2, WRITEABLEDIRECTORY=3)
