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
import json
import xbmc
import xbmcgui
from . import vfs
from .addon import get_path, get_name
from .constants import *

try:
	from urllib.parse import urlencode
except ImportError:
	from urllib import urlencode

def open_busy_dialog():
	xbmc.executebuiltin( "ActivateWindow(busydialog)" )

def close_busy_dialog():
	xbmc.executebuiltin( "Dialog.Close(busydialog)" )

def notify(heading, message, timeout=1500, image=vfs.join(get_path(), 'icon.png')):
	cmd = "XBMC.Notification(%s, %s, %s, %s)" % (heading, message, timeout, image)
	xbmc.executebuiltin(cmd)

def handel_error(heading, message, timeout=3000):
	image=vfs.join(ARTWORK, 'error.png')
	cmd = "XBMC.Notification(%s, %s, %s, %s)" % (heading, message, timeout, image)
	xbmc.executebuiltin(cmd)
	sys.exit()

def raise_error(self, title, m1='', m2=''):
	dialog = xbmcgui.Dialog()
	dialog.ok("%s ERROR!" % get_name(), str(title), str(m1), str(m2))


def dialog_ok(heading="", m1="", m2="", m3=""):
	dialog = xbmcgui.Dialog()
	return dialog.ok(heading, m1, m2, m3)

def dialog_info(listitem):
	return xbmcgui.Dialog().info(listitem)

def dialog_confirm(heading="", m1="", m2="", m3="", no="", yes="", delay=0):
	dialog = xbmcgui.Dialog()
	return dialog.yesno(heading, m1, m2, m3, no, yes, delay)

def dialog_input(heading, default='', type=xbmcgui.INPUT_ALPHANUM, option=0, delay=0):
	if type not in [xbmcgui.INPUT_ALPHANUM, xbmcgui.INPUT_NUMERIC, xbmcgui.INPUT_DATE, xbmcgui.INPUT_TIME, xbmcgui.INPUT_IPADDRESS, xbmcgui.INPUT_PASSWORD]: type = xbmcgui.INPUT_ALPHANUM
	dialog = xbmcgui.Dialog()
	return dialog.input(heading, default, type, option, delay)

def dialog_select(heading, options, delay=0, preselect=-1, detailed=False):
	dialog = xbmcgui.Dialog()
	index = dialog.select(heading, options, autoclose=delay, preselect=preselect, useDetails=detailed)
	if index >= 0:
		return index
	else: 
		return None

def dialog_multiselect(heading, options, delay=0, preselect=[], detailed=False):
	dialog = xbmcgui.Dialog()
	response = dialog.multiselect(heading, options, autoclose=delay, preselect=preselect, useDetails=detailed)
	if isinstance(response, list):
		return response
	return None

def dialog_textbox(heading, message, usemono=False):
	dialog = xbmcgui.Dialog()
	return dialog.textviewer(heading, message, usemono)

def dialog_context(options):
	dialog = xbmcgui.Dialog()
	index = dialog.contextmenu(options)
	if index >= 0:
		return index
	else: 
		return None

def dialog_browser(heading, type=BROWSER_TYPES.DIRECTORY, shares="", mask="", thumbs=False, force_folder=False, default="", multiple=False):
	if shares not in ["", "programs", "video", "pictures", "files", "games", "local"]: shares = ""
	return xbmcgui.Dialog().browse(type, heading, shares, mask, thumbs, force_folder, default, multiple)


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
		if percent: self._percent = int(percent)
		self.update(self._percent, self._heading, subheading, subheading2)
		
	def next(self, subheading, subheading2=""):
		if not self._silent:
			self._index = self._index + 1
			self._percent = int(self._index * 100 / self._total)
			self.update(self._percent, self._heading, subheading, subheading2)
	
	def is_canceled(self):
		return self.iscanceled()

progress_bar = ProgressBar


class ContextMenu:
	def __init__(self):
		self.commands = []

	def add(self, text, arguments={}, script=False, visible=True, mode=False, priority=50):
		if hasattr(visible, '__call__'):
			if visible() is False: return
		else:
			if visible is False: return
		if mode: arguments['mode'] = mode	
		cmd = self._build_url(arguments, script)
		self.commands.append((text, cmd, '', priority))
	
	def _build_url(self, arguments, script):
		for k,v in arguments.items():
			if type(v) is dict:
				arguments[k] = json.dumps(v)
		try:
			plugin_url =  "%s?%s" % (sys.argv[0], urlencode(arguments))
		except UnicodeEncodeError:
			for k in arguments:
				if isinstance(arguments[k], unicode):
					arguments[k] = arguments[k].encode('utf-8')
			plugin_url =  "%s?%s" % (sys.argv[0],  urlencode(arguments))
			
		if script:
			cmd = 'XBMC.RunPlugin(%s)' % (plugin_url)
		else:
			cmd = "XBMC.Container.Update(%s)" % plugin_url
		return cmd

	def get(self):
		return sorted(self.commands, key=lambda k: k[3])

context_menu = ContextMenu