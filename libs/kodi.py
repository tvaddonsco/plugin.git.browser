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
import xbmc
import json
import random
import xbmcgui
import xbmcaddon
import xbmcplugin
import zlib
import urllib
import urlparse
import vfs
from logging import log

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
		except Exception, e:
			return None
	else:
		try:
			data = vfs.read_file(file)
			if compress:
				data = zlib.decompress(data)
			return json.loads(data)
		except Exception, e:
			log(e)
			return None

mode='main'
args = {}
__dispatcher = {}
__kargs = {}

addon = xbmcaddon.Addon()
__get_setting = addon.getSetting
__set_setting = addon.setSetting
show_settings = addon.openSettings
open_settings = show_settings
sleep = xbmc.sleep
get_condition_visiblity = xbmc.getCondVisibility
PLATFORM = sys.platform
ARTWORK = vfs.join(addon.getAddonInfo('path').decode('utf-8'), 'resources/artwork')
try:
	HANDLE_ID = int(sys.argv[1])
	ADDON_URL = sys.argv[0]
	PLUGIN_URL = sys.argv[0] + sys.argv[2]
except:
	HANDLE_ID = -1
	ADDON_URL = 'plugin://%s' % addon.getAddonInfo('name')
	PLUGIN_URL = 'plugin://%s' % addon.getAddonInfo('name')

def exit():
	sys.exit()

def get_addon(addon_id):
	return xbmcaddon.Addon(addon_id)

def get_setting(k, addon_id=None):
	if addon_id is None:
		return __get_setting(k)
	else:
		return xbmcaddon.Addon(addon_id).getSetting(k)

def set_setting(k, v, addon_id=None):
	if not isinstance(v, basestring): v = str(v)
	if addon_id is None:
		return __set_setting(k, v)
	else:
		return xbmcaddon.Addon(addon_id).setSetting(k, v)

def get_property(k):
	p = xbmcgui.Window(10000).getProperty(get_name() + '.' + k)
	if p.lower() == 'false': return False
	if p.lower() == 'true': return True
	return p
	
def set_property(k, v):
	xbmcgui.Window(10000).setProperty(get_name() + '.' + k, str(v))

def clear_property(k):
	xbmcgui.Window(10000).clearProperty(get_name() + '.' + k)

def parse_query(query, q={'mode': 'main'}):
	if query.startswith('?'): query = query[1:]
	queries = urlparse.parse_qs(query)
	for key in queries:
		if len(queries[key]) == 1:
			q[key] = queries[key][0]
		else:
			q[key] = queries[key]
	return q
try:
	args = parse_query(sys.argv[2])
	mode = args['mode']
except:
	args = {"mode": "main"}

def arg(k, default=None):
	if k in args:
		v = args[k]
		if v == '': return default
		if v == 'None': return default
		return v
	else:
		return default
	
def get_kodi_version():
	full_version_info = xbmc.getInfoLabel('System.BuildVersion')
	return int(full_version_info.split(".")[0])


def get_arg(k, default=None):
	return arg(k, default)

def get_current_url():
	return str(sys.argv[0]) + str(sys.argv[2])

def get_path():
	return addon.getAddonInfo('path').decode('utf-8')

def get_profile():
	return addon.getAddonInfo('profile').decode('utf-8')

def translate_path(path):
	return xbmc.translatePath(path).decode('utf-8')

def get_version():
	return addon.getAddonInfo('version')

def get_id():
	return addon.getAddonInfo('id')

def get_name():
	return addon.getAddonInfo('name')

def get_plugin_url(queries, addon_id=None):
	try:
		query = urllib.urlencode(queries)
	except UnicodeEncodeError:
		for k in queries:
			if isinstance(queries[k], unicode):
				queries[k] = queries[k].encode('utf-8')
		query = urllib.urlencode(queries)
	addon_id = sys.argv[0] if addon_id is None else addon_id
	return addon_id + '?' + query

def refresh(plugin_url=None):
	query = get_property('search.query')
	if query:
		set_property('search.query.refesh', query)
		clear_property('search.query')
		
	if plugin_url is None:
		xbmc.executebuiltin("Container.Refresh")
	else:
		xbmc.executebuiltin("Container.Refresh(%s)" % plugin_url)
		
def exit():
	exit = xbmc.executebuiltin("XBMC.ActivateWindow(Home)")
	return exit

def kodi_json_request(method, params):
	jsonrpc =  json.dumps({ "jsonrpc": "2.0", "method": method, "params": params, "id": 1 })
	response = json.loads(xbmc.executeJSONRPC(jsonrpc))
	return response

def run_command(cmd):
	return xbmc.executebuiltin(cmd)

def build_plugin_url(queries, addon_id=None):
	return "plugin://" + get_plugin_url(queries, addon_id)

def execute_url(plugin_url):
	cmd = 'XBMC.RunPlugin(%s)' % (plugin_url) 
	run_command(cmd)

def execute_script(script):
	cmd = 'XBMC.RunScript(%s)' % (script)
	run_command(cmd)

def execute_addon(addon_id):
	cmd = 'XBMC.RunAddon(%s)' % addon_id
	run_command(cmd) 

def navigate_to(query):
	plugin_url = build_plugin_url(query)
	go_to_url(plugin_url)

def go_to_url(plugin_url):
	cmd = "XBMC.Container.Update(%s)" % plugin_url
	xbmc.executebuiltin(cmd)

def install_addon(addon_id):
	cmd = "XBMC.InstallAddon(%s)" % addon_id
	run_command(cmd)

def play_url(plugin_url, isFolder=False):
	if isFolder:
		cmd = 'XBMC.PlayMedia(%s,True)' % (plugin_url)
	else:
		cmd = 'XBMC.PlayMedia(%s)' % (plugin_url)
	run_command(cmd)


def dialog_ok(title="", m1="", m2="", m3=""):
	dialog = xbmcgui.Dialog()
	dialog.ok(title, m1, m2, m3)

def open_busy_dialog():
	xbmc.executebuiltin( "ActivateWindow(busydialog)" )

def close_busy_dialog():
	xbmc.executebuiltin( "Dialog.Close(busydialog)" )

def notify(title, message, timeout=1500, image=vfs.join(get_path(), 'icon.png')):
	
	cmd = "XBMC.Notification(%s, %s, %s, %s)" % (title.encode('utf-8'), message.encode('utf-8'), timeout, image)
	xbmc.executebuiltin(cmd)

def dialog_input(title):
	kb = xbmc.Keyboard('', title, False)
	kb.doModal()
	if (kb.isConfirmed()):
		text = kb.getText()
		if text != '':
			return text
	return None	

def dialog_textbox(heading, content):
	TextBox().show(heading, content)

def dialog_select(heading, options):
	dialog = xbmcgui.Dialog()
	index = dialog.select(heading, options)
	if index >= 0:
		return index
	else: 
		return False

def dialog_confirm(title, m1='', m2='', m3='', yes='', no=''):
	dialog = xbmcgui.Dialog()
	return dialog.yesno(title, m1, m2, m3, no, yes)

def raise_error(self, title, m1='', m2=''):
	dialog = xbmcgui.Dialog()
	dialog.ok("%s ERROR!" % get_name(), str(title), str(m1), str(m2))

def _eod(cache_to_disc=True):
	xbmcplugin.endOfDirectory(HANDLE_ID, cacheToDisc=cache_to_disc)

def eod(view=None, content=None, viewid=None, clear_search=False):
	_eod()

def add_menu_item(query, infolabels, total_items=0, icon='', image='', fanart='', replace_menu=True, menu=None, visible=True, format=None):
	if 'display' in infolabels: infolabels['title'] = infolabels['display']
	if hasattr(visible, '__call__'):
		if visible() is False: return
	else:
		if visible is False: return
	if icon:
		image = vfs.join(ARTWORK, icon)
	if not fanart:
		fanart = get_path() + '/fanart.jpg'
	if format is not None:
		text = format % infolabels['title']
	else:
		text = infolabels['title']	
	listitem = xbmcgui.ListItem(text, iconImage=image, thumbnailImage=image)
	cast = infolabels.pop('cast', None)
	try:
		if cast is not None: listitem.setCast(cast)
	except: pass
	listitem.setInfo('video', infolabels)
	listitem.setProperty('IsPlayable', 'false')
	listitem.setProperty('fanart_image', fanart)
	if menu is None:
		menu = ContextMenu()
	menu.add("Addon Settings", {"mode": "addon_settings"}, script=True)
	listitem.addContextMenuItems(menu.get(), replaceItems=replace_menu)
	
	plugin_url = get_plugin_url(query)
	xbmcplugin.addDirectoryItem(HANDLE_ID, plugin_url, listitem, isFolder=True, totalItems=total_items)

def add_video_item(query, infolabels, total_items=0, icon='', image='', fanart='', replace_menu=True, menu=None, format=None):
	if 'display' in infolabels: infolabels['title'] = infolabels['display']
	if not fanart:
		fanart = get_path() + '/fanart.jpg'
	if format is not None:
		text = format % infolabels['title']
	else:
		text = infolabels['title']
	if icon:
		image = vfs.join(ARTWORK, icon)		
	listitem = xbmcgui.ListItem(text, iconImage=image, thumbnailImage=image)
	cast = infolabels.pop('cast', None)
	try:
		if cast is not None: listitem.setCast(cast)
	except: pass
	listitem.setInfo('video', infolabels)
	listitem.setProperty('IsPlayable', 'true')
	listitem.setProperty('fanart_image', fanart)
	query['rand'] = random.random()
	if menu is None:
		menu = ContextMenu()
	menu.add("Addon Settings", {"mode": "addon_settings"}, script=True)
	listitem.addContextMenuItems(menu.get(), replaceItems=replace_menu)
	plugin_url = get_plugin_url(query)
	xbmcplugin.addDirectoryItem(HANDLE_ID, plugin_url, listitem, isFolder=False, totalItems=total_items)
	 
def play_stream(url, metadata={"cover_url": "", "title": ""}):
	if args['media'] == 'tv':
		media = 'tv'
		resume_point = get_resume_point(media, metadata['show_tmdb'])
	else:
		media = 'movie'
		resume_point = get_resume_point(media, metadata['tmdb'])	
	listitem = xbmcgui.ListItem(metadata['title'], iconImage=metadata['cover_url'], thumbnailImage=metadata['cover_url'], path=url)
	listitem.setPath(url)
	listitem.setInfo("video", metadata)
	listitem.setProperty('IsPlayable', 'true')
	set_property('playing', "true")
	if resume_point:
		listitem.setProperty('totaltime', '999999')
		listitem.setProperty('resumetime', str(resume_point))
		set_property("playback.resume", str(resume_point))
	if HANDLE_ID > -1:
		xbmcplugin.setResolvedUrl(HANDLE_ID, True, listitem)
	else:
		xbmc.Player().play(url, listitem)
	while get_property('playing'):
		sleep(100)
	on_playback_stop()

def play_url(plugin_url, isFolder=False):
	if isFolder:
		cmd = 'XBMC.PlayMedia(%s,True)' % (plugin_url)
	else:
		cmd = 'XBMC.PlayMedia(%s)' % (plugin_url)
	xbmc.executebuiltin(cmd)

	

	
def _register(mode, target, kargs=None):
	if isinstance(mode, list):
		for foo in mode:
			__dispatcher[foo] = target
			__kargs[foo] = kargs
	else:
		__dispatcher[mode] = target
		__kargs[mode] = kargs

def register(mode):
	def func_decorator(func):
		_register(mode, func)
	return func_decorator


def first_run():
	log('setup run here')

def run():
	if args['mode'] == 'void': return
	if get_setting('setup_run') != 'true' and 'video' in get_id():
		first_run()
	if args['mode'] == 'addon_settings': 
		open_settings() 
		return
	if __kargs[args['mode']] is None:
		__dispatcher[args['mode']]()
	else:
		__dispatcher[args['mode']](*__kargs[args['mode']])
	log("Executing with args: %s" % args)

class TextBox:
	# constants
	WINDOW = 10147
	CONTROL_LABEL = 1
	CONTROL_TEXTBOX = 5
	def __init__( self, *args, **kwargs):
		# activate the text viewer window
		xbmc.executebuiltin( "ActivateWindow(%d)" % ( self.WINDOW, ) )
		# get window
		self.window = xbmcgui.Window( self.WINDOW )
		# give window time to initialize
		xbmc.sleep( 500 )
	def setControls( self ):
		#get header, text
		heading, text = self.message
		# set heading
		self.window.getControl( self.CONTROL_LABEL ).setLabel( "%s - %s v%s" % ( heading, get_name(), get_version()) )
		# set text
		self.window.getControl( self.CONTROL_TEXTBOX ).setText( text )
	def show(self, heading, text):
		# set controls
		self.message = heading, text
		self.setControls()

class ContextMenu:
	def __init__(self):
		self.commands = []

	def add(self, text, arguments={}, script=False, visible=True, priority=50):
		if hasattr(visible, '__call__'):
			if visible() is False: return
		else:
			if visible is False: return
		cmd = self._build_url(arguments, script)
		self.commands.append((text, cmd, '', priority))
	
	def _build_url(self, arguments, script):
		try:
			plugin_url =  "%s?%s" % (sys.argv[0], urllib.urlencode(arguments))
		except UnicodeEncodeError:
			for k in arguments:
				if isinstance(arguments[k], unicode):
					arguments[k] = arguments[k].encode('utf-8')
			plugin_url =  "%s?%s" % (sys.argv[0], urllib.urlencode(arguments))
			
		if script:
			cmd = 'XBMC.RunPlugin(%s)' % (plugin_url)
		else:
			cmd = "XBMC.Container.Update(%s)" % plugin_url
		return cmd

	def get(self):
		return sorted(self.commands, key=lambda k: k[3])	

class ProgressBar(xbmcgui.DialogProgress):
	def __init__(self, *args, **kwargs):
		xbmcgui.DialogProgress.__init__(self, *args, **kwargs)
		self._silent = False
		self._index = 0
		self._total = 0
		self._percent = 0
		
	def new(self, heading, total):
		if not self._silent:
			self._index = 0
			self._total = total
			self._percent = 0
			self._heading = heading
			self.create(heading)
			self.update(0, heading, '')
			
	def update_subheading(self, subheading, subheading2="", percent=False):
		if percent: self._percent = percent
		self.update(self._percent, self._heading, subheading, subheading2)
		
	def next(self, subheading, subheading2=""):
		if not self._silent:
			self._index = self._index + 1
			self._percent = self._index * 100 / self._total
			self.update(self._percent, self._heading, subheading, subheading2)
	
	def is_canceled(self):
		return self.iscanceled()
		
