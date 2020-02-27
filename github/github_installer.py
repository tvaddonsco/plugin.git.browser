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
import xbmc
import xbmcgui
import re
import shutil
import requests
import github
from . import downloader
from commoncore import kodi
from commoncore import zipfile
from commoncore.beautifulsoup import BeautifulSoup
from database import DB


class installerException(Exception):
	pass

tva_user = 'tvaddonsco'

# Define source types
SOURCES = kodi.enum(DEFAULT=0, REPO=1, ZIP=2)

def update_addons(quiet=True):
	from distutils.version import LooseVersion
	if not quiet: kodi.open_busy_dialog()
	sources = DB.query("SELECT addon_id, source FROM install_history")
	update_count = 0
	for source in sources:
		addon_id = source[0]
		source = json.loads(source[1])
		if kodi.get_condition_visiblity("System.HasAddon(%s)" % addon_id):
			if source['type'] == SOURCES.ZIP:
				url, filename, full_name, version = github.find_zip(source['user'], addon_id)
				current_version = kodi.get_addon(addon_id).getAddonInfo('version')
				if LooseVersion(version) > LooseVersion(current_version):
					GitHub_Installer(addon_id, url, full_name, kodi.vfs.join("special://home", "addons"), False, quiet)
					update_count += 1
			elif source['type'] == SOURCES.REPO:
				full_name = sources['user'] + '/' + sources['repo']
				xml_str = github.find_xml(full_name)
				xml = BeautifulSoup(xml_str)
				addon = xml.find('addon')
				current_version = kodi.get_addon(addon_id).getAddonInfo('version')
				if LooseVersion(addon['version']) > LooseVersion(current_version):
					GitHub_Installer(addon_id, source['url'], full_name, kodi.vfs.join("special://home", "addons"), True, quiet)
					update_count += 1

	if not quiet: kodi.close_busy_dialog()
	if update_count > 0:
		kodi.notify("Update complete",'Some addons may require restarting kodi.')
	else:
		kodi.notify("Update complete",'No updates found.')

class GitHub_Installer():
	required_addons = []
	unmet_addons = []
	met_addons = []
	available_addons = []
	sources = {}
	install_error = False
	source_table = {}
	completed = []
	quiet = False

	def __init__(self, addon_id, url, full_name, destination, master=False, quiet=False, installed_list=[], batch=False):
		self.installed_list = installed_list
		self.quiet = quiet
		self.batch=batch
		if not self.quiet: kodi.open_busy_dialog()
		v = kodi.get_kodi_version()

		# Grab a list of KNOWN addons from the database. Unfortunately Jarvis requires direct database access for the installed flag
		if v >= 17:
			response = kodi.kodi_json_request("Addons.GetAddons", { "installed": False, "properties": ["path", "dependencies"]})
			for a in response['result']['addons']:
				self.available_addons += [a['addonid']]
				self.source_table[a['addonid']] = a['path']
		else:
			from sqlite3 import dbapi2
			dbf = kodi.vfs.join("special://profile/Database", "Addons20.db")
			with dbapi2.connect(dbf) as dbh:
				dbc = dbh.cursor()
				dbc.execute("SELECT addon.addonID, broken.addonID is Null AS enabled, addon.path FROM addon LEFT JOIN broken on addon.addonID=broken.addonID WHERE enabled=1")
				for a in dbc.fetchall():
					self.available_addons += [a[0]]
					self.source_table[a[0]] = a[2]
			dbh.close()
		self._addon_id = addon_id
		self._url = url
		self._full_name = full_name
		self._user, self.repo = full_name.split("/")
		self._master = master
		self._destination = destination

		# Add the final addon target to the sources list with type of zip
		# Initiate install routine
		self.install_addon(addon_id, url, full_name, master)


		completed = list(reversed(self.completed))
		if not quiet:
			pb = kodi.ProgressBar()
			pb.new('Enabling Addons', len(completed)+1)
			pb.update_subheading('Building Addon List')
		kodi.run_command("XBMC.UpdateLocalAddons()")
		kodi.sleep(500)
		for addon_id in completed:
			if not quiet:
				#percent = 100* (completed.index(addon_id) / len(completed))
				#pb.update(percent, "Enabling Addons", addon_id, '')
				pb.next(addon_id)
				kodi.sleep(100)
			self.enable_addon(addon_id)

		if not quiet: pb.next("Looking for Updates", "")
		kodi.sleep(500)
		kodi.run_command('XBMC.UpdateAddonRepos')

		# Enable installed addons
		if not self.quiet:
			pb.close()
			kodi.close_busy_dialog()
			if self.install_error:
				kodi.notify("Install failed", self._addon_id)
			else:
				kodi.notify("Install complete", self._addon_id)

	def build_dependency_list(self, addon_id, url, full_name, master):
		#if test in ['xbmc.python', 'xbmc.gui'] or kodi.get_condition_visiblity('System.HasAddon(%s)' % addon_id) == 1: return True
		if addon_id in self.installed_list:
			kodi.log('Dependency is already installed: %s' % addon_id)
			return True
		user, repo = full_name.split("/")
		kodi.log('Finding dependencies for: %s' % addon_id)
		if master:
			self.sources[addon_id] = {"type": SOURCES.REPO, "url": url, "user": user, "repo": repo, "version": ""}
			xml_str = github.find_xml(full_name)
			self.sources[addon_id]['version'] = github.get_version_by_xml(BeautifulSoup(xml_str))
		else:
			version = downloader.download(url, addon_id, self._destination, True, self.quiet)
			src_file = kodi.vfs.join("special://home/addons", addon_id)
			kodi.vfs.join(src_file, "addon.xml")
			xml = kodi.vfs.read_file(kodi.vfs.join(src_file, "addon.xml"), soup=True)
			self.save_source(addon_id, {"type": SOURCES.ZIP, "url": url, "user": user, "repo": repo, "version": version})

		for dep in xml.findAll('import'):
			test = dep['addon']
			try:
				if dep['optional'].lower() == 'true':
					if kodi.get_setting('install_optional') == 'false':
						continue
					elif kodi.get_setting('prompt_optional') == "true":
						c = kodi.dialog_confirm("Install Optional Dependency", dep['name'], dep['addon'])
						if not c: continue
			except:
				pass
			if test in ['xbmc.python', 'xbmc.gui'] or kodi.get_condition_visiblity('System.HasAddon(%s)' % test) == 1 or test in self.installed_list:
				kodi.log('Dependency is already installed: %s' % test)
				continue
			self.required_addons += [test]
			if test not in self.available_addons:
				self.unmet_addons += [test]
			else:
				self.sources[test] = {"type": SOURCES.DEFAULT, "url": self.source_table[test]}
				kodi.log("%s dependency met in %s" % (test, self.source_table[test]))

		def user_resolver(user, unmet):
			dep_url, dep_filename, dep_full_name, version = github.find_zip(user, unmet)
			if dep_url:
				kodi.log("%s found in %s repo" % (unmet, user))
				self.met_addons.append(unmet)
				user, repo = dep_full_name.split("/")
				self.sources[unmet] = {"type": SOURCES.ZIP, "url": dep_url, "user": user, "repo": repo, "version": ""}
				kodi.log("%s dependency met in %s" % (unmet, dep_url))
				return True
			return False

		def	github_resolver(unmet):
			results = github.web_search(unmet)
			c = kodi.dialog_select("GitHub Search Results for %s" % unmet, [r['full_name'] for r in results['items']])
			if c is not False:
				dep = results['items'][c]
				dep_url = url = "https://github.com/%s/archive/master.zip" % (dep['full_name'])
				self.met_addons.append(unmet)
				dep_filename = "%s.zip" % unmet
				self.sources[unmet] = {"type": SOURCES.REPO, "url": dep_url, "user": user, "repo": repo, "version": ""}
				kodi.log("%s dependency met in %s" % (unmet, dep_url))
				self.install_addon(unmet, dep_url, dep['full_name'], master=True)

				return True
			return False

		for unmet in self.unmet_addons:
			# Now attempt to locate dependencies from available sources
			# The addons that can be found in any enabled repos will be installed at the end.

			# check if this exists in users root repo
			if kodi.get_setting('source_user') == 'true':
				if user_resolver(user, unmet): continue

			# check if this exists in tva root repo
			if kodi.get_setting('source_tva') == 'true':
				if user_resolver(tva_user, unmet): continue

			# check if this exists on github
			if kodi.get_setting('source_github') == 'true':
				if github_resolver(unmet): continue

		self.unmet_addons = list(set(self.unmet_addons) - set(self.met_addons))
		if len(self.unmet_addons):
			self.install_error = True
			if not self.quiet:
				kodi.close_busy_dialog()
				kodi.raise_error("", "Unmet Dependencies:", "See log or install manually", ','.join(self.unmet_addons))
			kodi.log("Unmet Dependencies for addon install: %s" % addon_id)  # % self.addon_id)
			kodi.log(','.join(self.unmet_addons))
			inserts = [(a, ) for a in self.unmet_addons]
			DB.execute_many("INSERT INTO failed_depends(addon_id) VALUES(?)", inserts)
			DB.commit()
		self.completed.append(addon_id)

	def install_addon(self, addon_id, url, full_name, master):
		self.required_addons += [addon_id]
		self.build_dependency_list(addon_id, url, full_name, master)
		self.required_addons = list(set(self.required_addons))
		self.unmet_addons = list(set(self.unmet_addons))
		sources = self.sources
		self.sources = {}
		for addon_id in sources:
			source = sources[addon_id]
			if source['type'] == SOURCES.DEFAULT:
				self.install_addon(addon_id, source['url'], self._full_name, False)
			elif source['type'] == SOURCES.ZIP:
				full_name = '/'.join([source['user'], source['repo']])
				self.install_addon(addon_id, source['url'], full_name, False)
			elif source['type'] == SOURCES.REPO:
				full_name = '/'.join([source['user'], source['repo']])
				self.install_addon(addon_id, source['url'], full_name, True)
			self.save_source(addon_id, source)
			self.completed.append(addon_id)
			self.installed_list.append(addon_id)

	def save_source(self, addon_id, source):
		DB.execute("REPLACE INTO install_history(addon_id, source) VALUES(?,?)", [addon_id, json.dumps(source)])
		DB.commit()

	def enable_addon(self, addon_id):
		try:
			if addon_id in ['xbmc.python', 'xbmc.gui'] or kodi.get_condition_visiblity('System.HasAddon(%s)' % addon_id) == 1: return True
			kodi.log("Enable Addon: %s" % addon_id)
			kodi.kodi_json_request("Addons.SetAddonEnabled", {"addonid": addon_id, "enabled": True})
		except: pass
