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


from commoncore import kodi

@kodi.register('main')
def main():
	kodi.add_menu_item({'mode': 'search_menu', 'type': "username", 'title': "Search by GitHub Username"}, {'title': "Search by GitHub Username"}, icon='username.png')
	kodi.add_menu_item({'mode': 'search_menu', 'type': "repository", 'title': "Search by GitHub Repository Title"}, {'title': "Search by GitHub Repository Title"}, icon='repository.png')
	kodi.add_menu_item({'mode': 'search_menu', 'type': "addonid",'title': "Search by Addon ID"}, {'title': "Search by Addon ID"}, icon='addonid.png')
	kodi.add_menu_item({'mode': 'feed_menu'}, {'title': "Search Feeds"}, icon='feeds.png', visible=int(kodi.get_setting('installed_feeds')) > 0)
	kodi.add_menu_item({'mode': 'update_addons'}, {'title': "Check for Updates"}, icon='update.png', visible=kodi.get_setting('enable_updates') == 'true')
	kodi.add_menu_item({'mode': 'about'}, {'title': "About GitHub Installer"}, icon='about.png')
	kodi.add_menu_item({'mode': 'addon_settings'}, {'title': "Tools and Settings"}, icon='settings.png')
	kodi.eod()
		
	
@kodi.register('search_menu')
def search_menu():
	from libs.database import DB
	kodi.add_menu_item({'mode': 'void'}, {'title': "[COLOR darkorange]%s[/COLOR]" % kodi.arg('title')}, icon='null')
	kodi.add_menu_item({'mode': 'search', 'type': kodi.arg('type')}, {'title': "*** New Search ***"}, icon='null')
	results = DB.query_assoc("SELECT search_id, query FROM search_history WHERE search_type=? ORDER BY ts DESC LIMIT 10", [kodi.arg('type')], quiet=True)
	if results is not None:
		for result in results:
			menu = kodi.ContextMenu()
			menu.add('Delete from search history', {"mode": "history_delete", "id": result['search_id']})
			kodi.add_menu_item({'mode': 'search', 'type': kodi.arg('type'), 'query': result['query']}, {'title': result['query']}, menu=menu, icon='null')
	kodi.eod()
	
@kodi.register('search')
def search():
	from commoncore.dispatcher import dispatcher
	from libs.database import DB
	from libs import github
	q = kodi.arg('query') if kodi.arg('query') else kodi.dialog_input('Search GitHub')
	if q in [None, False, '']: return False
	DB.execute('INSERT INTO search_history(search_type, query) VALUES(?,?)', [kodi.arg('type'), q])
	DB.commit()
	
	@dispatcher.register('username')
	def username():
		rtype = 'api'
		response = github.find_zips(q)
		if response is None: return
		for r in github.sort_results(response['items']):
			url = github.content_url % (r['repository']['full_name'], r['path'])
			menu = kodi.ContextMenu()
			if r['is_repository']:
				menu.add('Browse Repository Contents', {"mode": "browse_repository", "url": url, "file": r['name'], "full_name": "%s/%s" % (q, r['repository']['name'])})
			if r['is_feed']:
				kodi.add_menu_item({'mode': 'install_feed', "url": url}, {'title': r['name']}, menu=menu, icon='null')
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
				url = github.content_url % (r['repository']['full_name'], r['path'])
				menu = kodi.ContextMenu()
				if r['is_repository']:
					menu.add('Browse Repository Contents', {"mode": "browse_repository", "url": url, "file": r['name'], "full_name": "%s/%s" % (q, r['repository']['name'])})
				if r['is_feed']:
					kodi.add_menu_item({'mode': 'install_feed', "url": url}, {'title': r['name']}, menu=menu, icon='null')
				else:
					kodi.add_menu_item({'mode': 'github_install', "url": url, "user": q, "file": r['name'], "full_name": "%s/%s" % (q, r['repository']['name'])}, {'title': r['name']}, menu=menu, icon='null')
	
	@dispatcher.register('addonid')
	def addonid():
		from commoncore.core import highlight
		from libs.github import re_version, content_url
		from distutils.version import LooseVersion
		rtype = 'api'
		results = github.search(q, 'id')
		if results is None: return

		def version_sort(name):
			v = re_version.search(name)
			if v:
				return LooseVersion(v.group(1))
			else: 
				return LooseVersion('0.0.0')
		
		results.sort(key=lambda x:version_sort(x['name']), reverse=True)
			
		for i in results:
			menu = kodi.ContextMenu()
			r = i['repository']
			full_name = r['full_name']
			title = highlight("%s/%s" % (full_name, i['name']), q, 'yellow')
			url = content_url % (full_name, i['path'])
			menu.add("Search Username", {'mode': 'search', 'type': 'username', 'query': r['owner']['login']})
			kodi.add_menu_item({'mode': 'github_install', "url": url, "file": i['name'], "full_name": full_name}, {'title': title}, menu=menu, icon='null')
	dispatcher.run(kodi.arg('type'))
	kodi.eod()

@kodi.register('feed_menu')
def feed_menu():
	from libs.database import DB
	kodi.add_menu_item({'mode': 'new_feed'}, {'title': "*** New Search Feed ***"}, icon='null')
	feeds = DB.query_assoc("SELECT feed_id, name, url, enabled FROM feed_subscriptions")
	for feed in feeds:
		menu = kodi.ContextMenu()
		
		name = feed['name'] if feed['name'] else feed['url']
		if not feed['enabled']:
			title = "[COLOR darkred]%s[/COLOR]" % name
		else: title = name
		menu.add('Delete Feed', {"mode": "delete_feed", "title": title, "id": feed['feed_id']})
		kodi.add_menu_item({'mode': 'list_feed', 'url': feed['url']}, {'title': title}, menu=menu, icon='null')
	kodi.eod()

@kodi.register('install_feed')
def install_feed():
	if not kodi.dialog_confirm('Install Feed?', "Click YES to proceed."): return
	from libs.database import DB
	from libs import github
	xml = github.install_feed(kodi.arg('url'))
	try:
		name = xml.find('name').text
		url = xml.find('url').text
		DB.execute("INSERT INTO feed_subscriptions(name, url) VALUES(?,?)", [name, url])
		DB.commit()
		count = DB.query("SELECT count(1) FROM feed_subscriptions")
		kodi.set_setting('installed_feeds', str(count[0][0]))
		kodi.notify("Install Complete",'Feed Installed')
	except:
		kodi.notify("Install failed",'Invalid Format.')	


@kodi.register('new_feed')
def new_feed():
	from libs.database import DB
	url = kodi.dialog_input('Feed URL')
	if not url: return
	DB.execute("INSERT INTO feed_subscriptions(url) VALUES(?)", [url])
	DB.commit()
	count = DB.query("SELECT count(1) FROM feed_subscriptions")
	kodi.set_setting('installed_feeds', str(count[0][0]))
	kodi.refresh()

@kodi.register('delete_feed')
def delete_feed():
	if not kodi.dialog_confirm('Delete Feed?', kodi.arg('title'), "Click YES to proceed."): return
	from libs.database import DB
	DB.execute("DELETE FROM feed_subscriptions WHERE feed_id=?", [kodi.arg('id')])
	DB.commit()
	count = DB.query("SELECT count(1) FROM feed_subscriptions")
	kodi.set_setting('installed_feeds', str(count[0][0]))
	kodi.refresh()
	
@kodi.register('list_feed')
def feed_list():
	from commoncore.baseapi import CACHABLE_API, EXPIRE_TIMES
	class FeedAPI(CACHABLE_API):
		base_url = ''
		default_return_type = 'xml'
		
	try:
		xml = FeedAPI().request(kodi.arg('url'), cache_limit=EXPIRE_TIMES.EIGHTHOURS)
		for r in xml.findAll('repository'):
			name = r.find('name').text
			username = r.find('username').text
			desc = r.find('description').text
			title = "%s: %s" % (name, desc)
			kodi.add_menu_item({'mode': 'search', 'type': 'username', 'query': username}, {'title': title, 'plot': desc}, icon='null')
		kodi.eod()	
	except:pass
	
@kodi.register('github_install')
def github_install():
	import re
	from libs import github_installer
	from libs import github
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

@kodi.register('about')
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

@kodi.register('browse_repository')
def browse_repository():
	from libs import github
	xml = github.browse_repository(kodi.arg('url'))
	heading = "%s/%s" % (kodi.arg('full_name'), kodi.arg('file'))
	options = []
	if xml:
		for addon in xml.findAll('addon'):
			options.append("%s (%s)" % (addon['name'], addon['version']))

		kodi.dialog_select(heading, sorted(options))


@kodi.register('history_delete')
def history_delete():
	if not kodi.arg('id'): return
	from libs.database import DB
	DB.execute("DELETE FROM search_history WHERE search_id=?", [kodi.arg('id')])
	DB.commit()	
	kodi.refresh()

@kodi.register('update_addons')
def update_addons():
	from libs import github_installer
	quiet = True if kodi.arg('quiet') == 'quiet' else False
	if not quiet:
		c = kodi.dialog_confirm("Confirm Update", "Check for updates", yes="Update", no="Cancel")
		if not c: return
	github_installer.update_addons(quiet)
	
if __name__ == '__main__': kodi.run()
