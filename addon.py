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

import github
from github import *

@kodi.register('main')
def main():
	show_about()
	kodi.add_menu_item({'mode': 'search_menu', 'type': "username", 'title': "Search by GitHub Username"}, {'title': "Search by GitHub Username"}, icon='username.png')
	kodi.add_menu_item({'mode': 'search_menu', 'type': "repository", 'title': "Search by GitHub Repository Title"}, {'title': "Search by GitHub Repository Title [COLOR red](Advanced)[/COLOR]"}, icon='repository.png')
	kodi.add_menu_item({'mode': 'search_menu', 'type': "addonid",'title': "Search by Addon ID"}, {'title': "Search by Addon ID [COLOR red](Advanced)[/COLOR]"}, icon='addonid.png')
	kodi.add_menu_item({'mode': 'feed_menu'}, {'title': "Search Feeds"}, icon='search_feeds.png')
	kodi.add_menu_item({'mode': 'installer_menu'}, {'title': "Batch Installers"}, icon='batch_installer.png')
	kodi.add_menu_item({'mode': 'about'}, {'title': "About GitHub Installer"}, icon='about.png')
	kodi.add_menu_item({'mode': 'settings_menu'}, {'title': "Tools and Settings"}, icon='settings.png')

@kodi.register('settings_menu')
def settings_menu():
	kodi.add_menu_item({'mode': 'dependency_search'}, {'title': "Search for missing dependencies"}, icon='search_failed.png')
	kodi.add_menu_item({'mode': 'update_addons'}, {'title': "Check for Updates [COLOR red](Advanced)[/COLOR]"}, icon='update.png', visible=kodi.get_setting('enable_updates') == 'true')
	kodi.add_menu_item({'mode': 'addon_settings'}, {'title': "Addon Settings"}, icon='settings.png')

@kodi.register('search_menu')
def search_menu():
	menu = kodi.context_menu()
	menu.add('Search Filter', {"mode": "search_filter"})
	kodi.add_menu_item({'mode': 'void'}, {'title': "[COLOR darkorange]%s[/COLOR]" % kodi.arg('title')}, icon='null', menu=menu)
	kodi.add_menu_item({'mode': 'search', 'type': kodi.arg('type')}, {'title': "*** New Search ***"}, icon='null', menu=menu)
	results = DB.query_assoc("SELECT search_id, query FROM search_history WHERE search_type=? ORDER BY ts DESC LIMIT 25", [kodi.arg('type')], quiet=True)
	if results is not None:
		for result in results:
			menu = kodi.context_menu()
			menu.add('Search Filter', {"mode": "search_filter"})
			menu.add('Delete from search history', {"mode": "history_delete", "id": result['search_id']})
			kodi.add_menu_item({'mode': 'search', 'type': kodi.arg('type'), 'query': result['query']}, {'title': result['query']}, menu=menu, icon='null')

@kodi.register('dependency_search')
def dependency_search():
	results = DB.query("SELECT addon_id FROM failed_depends WHERE resolved=0 ORDER BY addon_id ASC")
	if results is not None:
		for result in results:
			if kodi.has_addon(result[0]):
				DB.execute("UPDATE failed_depends SET resolved=1 WHERE addon_id=?", [result[0]])
				DB.commit()
				continue
			kodi.add_menu_item({'mode': 'search', 'type': "addonid",'query': result[0]}, {'title': result[0]}, icon='addonid.png')

@kodi.register('search')
def search():
	q = kodi.arg('query') if kodi.arg('query') else kodi.dialog_input('Search GitHub')
	if q in [None, False, '']: return False
	DB.execute('REPLACE INTO search_history(search_type, query) VALUES(?,?)', [kodi.arg('type'), q])
	DB.commit()

	@dispatcher.register('username')
	def username():
		rtype = 'api'
		response = github.find_zips(q)
		if response is None: return
		for r in github.sort_results(response['items']):
			url = github.get_download_url(r['repository']['full_name'], r['path'])
			menu = kodi.context_menu()
			if r['is_repository']:
				menu.add('Browse Repository Contents', {"mode": "browse_repository", "url": url, "file": r['name'], "full_name": "%s/%s" % (q, r['repository']['name'])})
			if r['is_feed']:
				r['display'] = "[COLOR yellow]%s[/COLOR]" % r['name']
				kodi.add_menu_item({'mode': 'install_feed', "url": url}, {'title': r['name'], 'display': r['display']}, menu=menu, icon='null')
			elif r['is_installer']:
				r['display'] = "[COLOR orange]%s[/COLOR]" % r['name']
				kodi.add_menu_item({'mode': 'install_batch', "url": url}, {'title': r['name'], 'display': r['display']}, menu=menu, icon='null')
			else:
				kodi.add_menu_item({'mode': 'github_install', "url": url, "user": q, "file": r['name'], "full_name": "%s/%s" % (q, r['repository']['name'])}, {'title': r['name']}, menu=menu, icon='null')

	@dispatcher.register('repository')
	def repository():
		rtype = 'api'
		results = github.search(q, 'title')
		if results is None: return
		for i in results['items']:
			user = i['owner']['login']
			response = github.find_zips(user)
			if response is None: continue
			for r in github.sort_results(response['items']):
				url = github.get_download_url(r['repository']['full_name'], r['path'])
				menu = kodi.context_menu()
				if r['is_repository']:
					menu.add('Browse Repository Contents', {"mode": "browse_repository", "url": url, "file": r['name'], "full_name": "%s/%s" % (q, r['repository']['name'])})
				if r['is_feed']:
					r['display'] = "[COLOR yellow]%s[/COLOR]" % r['name']
					kodi.add_menu_item({'mode': 'install_feed', "url": url}, {'title': r['name']}, menu=menu, icon='null')
				elif r['is_installer']:
					r['display'] = "[COLOR orange]%s[/COLOR]" % r['name']
					kodi.add_menu_item({'mode': 'install_batch', "url": url}, {'title': r['name'], 'display': r['display']}, menu=menu, icon='null')
				else:
					kodi.add_menu_item({'mode': 'github_install', "url": url, "user": q, "file": r['name'], "full_name": "%s/%s" % (q, r['repository']['name'])}, {'title': r['name']}, menu=menu, icon='null')

	@dispatcher.register('addonid')
	def addonid():
		rtype = 'api'
		results = github.search(q, 'id')
		if results is None: return
		results.sort(key=lambda x:github.version_sort(x['name']), reverse=True)

		for i in results:
			menu = kodi.context_menu()
			r = i['repository']
			full_name = r['full_name']
			title = kodi.highlight("%s/%s" % (full_name, i['name']), q, 'yellow')
			url = github.get_download_url(full_name, i['path'])
			menu.add("Search Username", {'mode': 'search', 'type': 'username', 'query': r['owner']['login']})
			kodi.add_menu_item({'mode': 'github_install', "url": url, "file": i['name'], "full_name": full_name}, {'title': title}, menu=menu, icon='null')
	dispatcher.run(kodi.arg('type'))

@kodi.register('search_filter', False)
def search_filter():
	options = display =['None', 'Repository', 'Feed', 'Music Plugin', 'Video Plugin', 'Script']
	filter = kodi.get_property('search.filter')
	if filter in options:
		index = options.index(filter)
		display[index] = kodi.format_color(display[index], 'yellow')
	else:
		display[0] = kodi.format_color(display[0], 'yellow')

	c = kodi.dialog_select("Filter Results by:", display)
	if c is not False:
		if c is 0:
			kodi.set_property('search.filter', '')
		else:
			kodi.set_property('search.filter', options[c])

@kodi.register('feed_menu')
def feed_menu():
	kodi.add_menu_item({'mode': 'install_local_feed'}, {'title': "*** Local Search Feed File ***"}, icon='install_feed_local.png')
	#kodi.add_menu_item({'mode': 'search', 'query': 'gitbrowser.feed', 'type': 'addonid'}, {'title': "*** Search for Feeds ***"}, icon='null')
	feeds = DB.query_assoc("SELECT feed_id, name, url, enabled FROM feed_subscriptions")
	for feed in feeds:
		menu = kodi.ContextMenu()

		name = feed['name'] if feed['name'] else feed['url']
		if not feed['enabled']:
			title = "[COLOR darkred]%s[/COLOR]" % name
		else: title = name
		menu.add('Delete Feed', {"mode": "delete_feed", "title": title, "id": feed['feed_id']})
		kodi.add_menu_item({'mode': 'list_feed', 'url': feed['url']}, {'title': title}, menu=menu, icon='null')

@kodi.register('installer_menu')
def installer_menu():
	kodi.add_menu_item({'mode': 'browse_local'}, {'title': "*** Install From Local File ***"}, icon='install_batch_local.png')
	#kodi.add_menu_item({'mode': 'search', 'query': 'gitbrowser.installer', 'type': 'addonid'}, {'title': "*** Search for Batch Installers ***"}, icon='null')


@kodi.register(['install_feed', 'install_local_feed'], False)
def install_feed():
	if kodi.mode == 'install_feed':
		url = kodi.arg('url')
		xml = github.install_feed(url)
	else:
		url = kodi.dialog_browser('Select a feed file',type=kodi.BROWSER_TYPES.FILE, mask='.zip')
		if not github.re_feed.search(url): return
		xml = github.install_feed(url, True)
	if not kodi.dialog_confirm('Install Feed?', "Click YES to proceed."): return

	try:
		for f in xml.findAll('feeds'):
			name = f.find('name').text
			url = f.find('url').text
			DB.execute("INSERT INTO feed_subscriptions(name, url) VALUES(?,?)", [name, url])
		DB.commit()
		count = DB.query("SELECT count(1) FROM feed_subscriptions")
		kodi.set_setting('installed_feeds', str(count[0][0]))
		kodi.notify("Install Complete",'Feed Installed')
	except:
		kodi.notify("Install failed",'Invalid Format.')

def feed_count():
	try:
		count = DB.query("SELECT count(1) FROM feed_subscriptions")[0][0]
	except:
		count = 0
	return count


@kodi.register(['install_batch', 'browse_local'], False)
def install_batch():
	import xbmcgui
	if kodi.mode == 'install_batch':
		url = kodi.arg('url')
		xml, zip_ref = github.batch_installer(url)
	else:
		url = kodi.dialog_browser('Select a install file', type=kodi.BROWSER_TYPES.FILE, mask='.zip')
		if not github.re_installer.search(url): return
		xml, zip_ref = github.batch_installer(url, True)
	if not kodi.dialog_confirm('Batch Installer?', "Click YES to proceed.", "This will install a list of addons.", "Some configuration files and settings may be overwritten."): return
	if not xml: return
	# Install each addon as instructed
	installed_list = []
	failed_list = []
	count = 0
	for a in xml.findAll('addon'):
		count +=1
	PB = kodi.ProgressBar()
	PB.new('Batch Installer - Progress', count)

	for a in xml.findAll('addon'):
		addon_id = a.find('addon_id')
		username = a.find('username')
		if addon_id is None or username is None: continue
		username = username.text
		addon_id = addon_id.text
		PB.next(addon_id)
		if not kodi.has_addon(addon_id):
			if PB.is_canceled(): return
			kodi.log("Batch install " + addon_id)
			url, filename, full_name, version = github.find_zip(username, addon_id)
			if url:
				installed_list += github_installer.GitHub_Installer(addon_id, url, full_name, kodi.vfs.join("special://home", "addons"), quiet=True, batch=True, installed_list=installed_list).installed_list
				kodi.sleep(1000)
			else:
				failed_list.append(addon_id)

	# Look for config files.
	# Need to add error checking for missing config files
	configs= xml.find('configs')
	if configs is not None and 'dir' in configs.attrs[0]:
		config_dir = configs['dir']
		for config in configs.findAll('config'):
			source = config.find('source')
			destination = config.find('destination')
			if source is None or destination is None: continue
			source = source.text
			destination = destination.text
			if not kodi.vfs.exists(destination): kodi.vfs.mkdir(destination, True)
			kodi.vfs.write_file(kodi.vfs.join(destination, source), zip_ref.read(config_dir + '/' + source))

	# Now look for individual setting key and value pairs
	# Set them as instructed
	settings= xml.find('settings')
	if settings is not None:
		for setting in settings.findAll('setting'):
			if 'addon_id' in setting.attrs[0]:
				addon_id = setting['addon_id']
				k = setting.find('key')
				v = setting.find('value')
				if k is None or v is None: continue
				kodi.set_setting(k.text, v.text, addon_id)

	builtins= xml.find('builtins')
	if builtins is not None:
		for cmd in builtins.findAll('command'):
			cmd = cmd.text
			kodi.run_command(cmd)

	jsonrpc= xml.find('jsonrpc')
	if jsonrpc is not None:
		from ast import literal_eval
		for cmd in jsonrpc.findAll('command'):
			method = cmd.find('method').text
			params = literal_eval(cmd.find('params').text)
			id = cmd.find('id').text
			kodi.kodi_json_request(method, params, id)

	# Now clean up
	zip_ref.close()
	PB.close()
	if len(failed_list):
		kodi.dialog_ok("Batch Error", "One or more Addons failed to install", "See log for list")
		kodi.log("Failed list: %s" % ",".join(failed_list))
	r = kodi.dialog_confirm(kodi.get_name(), 'Click Continue to install more addons or', 'Restart button to finalize addon installation', yes='Restart', no='Continue')
	if r:
		import sys
		import xbmc
		if sys.platform in ['linux', 'linux2', 'win32']:
			xbmc.executebuiltin('RestartApp')
		else:
			xbmc.executebuiltin('ShutDown')


@kodi.register('new_feed')
def new_feed():
	url = kodi.dialog_input('Feed URL')
	if not url: return
	DB.execute("INSERT INTO feed_subscriptions(url) VALUES(?)", [url])
	DB.commit()
	kodi.refresh()

@kodi.register('delete_feed', False)
def delete_feed():
	if not kodi.dialog_confirm('Delete Feed?', kodi.arg('title'), "Click YES to proceed."): return
	DB.execute("DELETE FROM feed_subscriptions WHERE feed_id=?", [kodi.arg('id')])
	DB.commit()
	kodi.refresh()

@kodi.register('list_feed')
def feed_list():
	from commoncore.baseapi import CACHABLE_API, EXPIRE_TIMES
	class FeedAPI(CACHABLE_API):
		base_url = ''
		default_return_type = 'xml'
	try:
		xml = FeedAPI().request(kodi.arg('url')) #, cache_limit=EXPIRE_TIMES.EIGHTHOURS)
		for r in xml.iter('repository'):
			name = r.find('name').text
			username = r.find('username').text
			desc = r.find('description').text
			title = "%s: %s" % (name, desc)
			kodi.add_menu_item({'mode': 'search', 'type': 'username', 'query': username}, {'title': title, 'plot': desc}, icon='null')
		kodi.eod()
	except Exception as e:
		kodi.log(e)

@kodi.register('github_install', False)
def github_install():
	import re
	from github import github_installer
	c = kodi.dialog_confirm("Confirm Install", kodi.arg('file'), yes="Install", no="Cancel")
	if not c: return
	addon_id = re.sub("-[\d\.]+zip$", "", kodi.arg('file'))
	github_installer.GitHub_Installer(addon_id, kodi.arg('url'), kodi.arg('full_name'), kodi.vfs.join("special://home", "addons"))
	r = kodi.dialog_confirm(kodi.get_name(), 'Click Continue to install more addons or', 'Restart button to finalize addon installation', yes='Restart', no='Continue')
	if r:
		import sys
		import xbmc
		if sys.platform in ['linux', 'linux2', 'win32']:
			xbmc.executebuiltin('RestartApp')
		else:
			xbmc.executebuiltin('ShutDown')

@kodi.register('about', False)
def about():
	try:
		import xbmc
		KODI_LANGUAGE = xbmc.getLanguage()
	except:
		KODI_LANGUAGE = 'English'
	path = kodi.vfs.join(kodi.get_path(), 'resources/language/%s/github_help.txt', KODI_LANGUAGE)
	if not kodi.vfs.exists(path):
		path = kodi.vfs.join(kodi.get_path(), 'resources/language/English/github_help.txt')
	text = kodi.vfs.read_file(path)
	kodi.dialog_textbox('GitHub Browser Instructions', text)

def show_about():
	if kodi.get_setting('disable_about') == 'true': return
	interval = int(kodi.get_setting('last_about'))
	if interval == 0:
		interval = 5
		try:
			import xbmc
			KODI_LANGUAGE = xbmc.getLanguage()
		except:
			KODI_LANGUAGE = 'English'
		path = kodi.vfs.join(kodi.get_path(), 'resources/language/%s/github_help.txt', KODI_LANGUAGE)
		if not kodi.vfs.exists(path):
			path = kodi.vfs.join(kodi.get_path(), 'resources/language/English/github_help.txt')
		text = kodi.vfs.read_file(path)
		kodi.dialog_textbox('GitHub Browser Instructions', text)
	else:
		interval -= 1
	kodi.set_setting('last_about', interval)

@kodi.register('browse_repository', False)
def browse_repository():
	xml = github.browse_repository(kodi.arg('url'))
	heading = "%s/%s" % (kodi.arg('full_name'), kodi.arg('file'))
	options = []
	if xml:
		for addon in xml.findAll('addon'):
			options.append("%s (%s)" % (addon['name'], addon['version']))

		kodi.dialog_select(heading, sorted(options))


@kodi.register('history_delete', False)
def history_delete():
	if not kodi.arg('id'): return
	DB.execute("DELETE FROM search_history WHERE search_id=?", [kodi.arg('id')])
	DB.commit()
	kodi.refresh()

@kodi.register('update_addons', False)
def update_addons():
	from github import github_installer
	quiet = True if kodi.arg('quiet') == 'quiet' else False
	if not quiet:
		c = kodi.dialog_confirm("Confirm Update", "Check for updates", yes="Update", no="Cancel")
		if not c: return
	github_installer.update_addons(quiet)

if __name__ == '__main__': kodi.run()
