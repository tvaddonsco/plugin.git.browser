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

import xbmcgui
from commoncore.kodi import enum

WINDOW_ACTIONS = enum(
	ACTION_PREVIOUS_MENU = 10,
	ACTION_NAV_BACK = 92,
	ACTION_MOVE_LEFT = 1,
	ACTION_MOVE_RIGHT = 2,
	ACTION_MOVE_UP = 3,
	ACTION_MOVE_DOWN = 4,
	ACTION_MOUSE_WHEEL_UP = 104,
	ACTION_MOUSE_WHEEL_DOWN = 105,
	ACTION_MOUSE_DRAG = 106,
	ACTION_MOUSE_MOVE = 107,
	ACTION_MOUSE_LEFT_CLICK = 100,
	ACTION_ENTER = 13,
	ACTION_SELECT_ITEM = 7,
	ACTION_SPACE = 12,
	ACTION_MOUSE_RIGHT_CLICK = 101,
	ACTION_SHOW_INFO = 11,
	ACTION_CONTEXT_MENU = 117,
)


class BaseWindow(xbmcgui.WindowXMLDialog):
	return_val = None
	
	def __init__(self, *args, **kwargs):
			xbmcgui.WindowXML.__init__(self)
	
	def show(self):
		self.doModal()
		return self.return_val
	
	def _close(self):
		self.close()
		
	def onInit(self):
		pass

	def onAction(self, action):
		action = action.getId()
		if action in [WINDOW_ACTIONS.ACTION_PREVIOUS_MENU, WINDOW_ACTIONS.ACTION_NAV_BACK]:
			self._close()
		
		try:
			if action in [WINDOW_ACTIONS.ACTION_SHOW_INFO, WINDOW_ACTIONS.ACTION_CONTEXT_MENU]:
				controlID = self.getFocus().getId()
				self.onContext(controlID)
		except:
			pass
		
		try:
			controlID = self.getFocus().getId()
			self.onEvent(action, controlID)
		except:
			pass
	
	def onEvent(self, event, controlID):
		pass
	
	def onContext(self, controlID):
		pass
		
	def onClick(self, controlID):
		pass

		
	def onFocus(self, controlID):
		pass