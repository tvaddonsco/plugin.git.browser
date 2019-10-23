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

import xbmc
import time
from commoncore import kodi

test = xbmc.__version__.split('.')
is_depricated = True if int(test[1]) < 19  else False
enable_updates = kodi.get_setting('enable_updates') == 'true'
class UpdateService():
	last_run = False
	update_interval = 86400	# every 24 hours
	def update(self):
		if enable_updates:
			if not self.last_run or time.time() - self.last_run > self.update_interval:
				self.last_run = time.time()
				plugin_url = kodi.build_plugin_url({"mode": "update_addons", "quiet": "quiet"}, kodi.get_id())
				kodi.execute_url(plugin_url)

	def start(self):

		enable_updates
		class Monitor(xbmc.Monitor):
			def onSettingsChanged(self):
				global enable_updates
				enable_updates = kodi.get_setting('enable_updates') == 'true'
		monitor = Monitor()
		kodi.log("Service Starting...")


		if is_depricated:
			while not xbmc.abortRequested:
				kodi.sleep(1000)
				self.update()
		else:
			while not monitor.abortRequested():
				if monitor.waitForAbort(10):
					break
				self.update()

		self.shutdown()


	def shutdown(self):
		kodi.log("Service Stopping...")


if __name__ == '__main__':
	server = UpdateService()
	server.start()
