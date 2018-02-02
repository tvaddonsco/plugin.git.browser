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
import math
import json
import sys
import kodi
import urllib
import random
import dom_parser
from libs import requests
from enum import enum
from distutils.version import LooseVersion
from libs.database import DB

class githubException(Exception):
	pass

base_url = "https://api.github.com"
content_url = "https://raw.githubusercontent.com/%s/master/%s"
master_url = "https://github.com/%s/%s/archive/master.zip"
page_limit = 100

#SORT_ORDER = enum(REPO=100, PLUGIN=99, PROGRAM=98, SKIN=97, SERVICE=96, SCRIPT=95, OTHER=0)
SORT_ORDER = enum(REPO=0, PLUGIN=1, PROGRAM=2, SKIN=3, SERVICE=4, SCRIPT=5, OTHER=100)


def search(q, method=False):
	if method=='user':
		return call("/search/repositories", query={"per_page": page_limit, "q": "user:%s" % q})
	if method=='title':
		return call("/search/repositories", query={"per_page": page_limit, "q": "in:name+%s" % q})
	else:
		return call("/search/repositories", query={"per_page": page_limit, "q": q})

re_plugin = re.compile("^plugin\.", re.IGNORECASE)
re_service = re.compile("^service\.", re.IGNORECASE)
re_script = re.compile("^script\.", re.IGNORECASE)
re_repository = re.compile("^repository\.", re.IGNORECASE)
re_program = re.compile("^(program\.)|(plugin\.program)", re.IGNORECASE)
re_skin = re.compile("^skin\.", re.IGNORECASE)
re_version = re.compile("-([^zip]+)\.zip$")
re_split_version = re.compile("^(.+?)-([^zip]+)\.zip$")

def is_zip(filename):
	return filename.lower().endswith('.zip')

def split_version(name):
	try:
		match = re_split_version.search(name)
		addon_id, version = match.groups()
		return addon_id, version
	except:
		return False, False

def get_version_by_name(name):
	version = re_version.search(name)
	if version:
		return version.group(1)
	else:
		return '0.0.0'

def get_version_by_xml(xml):
	try:
		addon = xml.find('addon')
		version = addon['version']
	except:
		return False	

def sort_results(results):
	def sort_results(name):
		index = SORT_ORDER.OTHER
		version = get_version_by_name(name)
		version_index = LooseVersion(version)
		if re_program.search(name): index = SORT_ORDER.PROGRAM
		elif re_plugin.search(name): index = SORT_ORDER.PLUGIN
		elif re_repository.search(name): index = SORT_ORDER.REPO
		elif re_service.search(name): index = SORT_ORDER.SERVICE
		elif re_script.search(name): index = SORT_ORDER.SCRIPT
		return index, name.lower(), version_index

	return sorted(results, key=lambda x:sort_results(x['name']), reverse=False)
	#return sorted(temp, key=lambda x: x['name'])

def limit_versions(results):
	final = []
	temp = []
	sorted_results = sort_results(results['items'])
	for a in sorted_results:
		if not is_zip(a['name']): continue
		addon_id, version = split_version(a['name'])
		if addon_id in temp: continue
		final.append(a)
		temp.append(addon_id)
	results['items'] = final
	return results

def web_search(q):
	from HTMLParser import HTMLParser
	class MLStripper(HTMLParser):
		def __init__(self):
			self.reset()
			self.fed = []
		def handle_data(self, d):
			self.fed.append(d)
		def get_data(self):
			return ''.join(self.fed)

	def strip_tags(html):
		s = MLStripper()
		s.feed(html)
		return s.get_data()
	base_url = "https://github.com/search"
	q = "%s extension:zip language:Python path:addon.xml language:Python" % q
	params = {"q":q, "type":"Repositories", "ref":"advsearch"}
	results = {"items": []}
	r = requests.get(base_url, params=params)
	links = dom_parser.parse_dom(r.text, 'a', {"class": "v-align-middle"})
	for link in links:
		link = strip_tags(link)
		temp = link.split("/")
		results["items"] += [{"owner": {"login": temp[0]}, "name": temp[1], "full_name": link}]
	return results

def find_xml(full_name):
	return call(content_url % (full_name, 'addon.xml'), web=True)

def find_zips(user, repo=None):
	if repo is None:
		results = limit_versions(call("/search/code", query={"per_page": page_limit, "q":"user:%s+filename:*.zip" % user}, cache_limit=1))
	else:
		results = limit_versions(call("/search/code", query={"per_page": page_limit, "q":"user:%s+repo:%s+filename:*.zip" % (user, repo)}, cache_limit=1))
	return results

def find_zip(user, addon_id):
	results = []
	response = call("/search/code", query={"q": "user:%s+filename:%s*.zip" % (user, addon_id)}, cache_limit=1)
	if response is None: return False, False, False
	if response['total_count'] > 0:
		test = re.compile("%s-.+\.zip$" % addon_id, re.IGNORECASE)
		def sort_results(name):
			version = get_version_by_name(name)
			return LooseVersion(version)
			
		response['items'].sort(key=lambda k: sort_results(k['name']), reverse=True)
		
		for r in response['items']:
			if test.match(r['name']):
				url = content_url % (r['repository']['full_name'], r['path'])
				version = get_version_by_name(r['path'])
				return url, r['name'], r['repository']['full_name'], version
	return False, False, False, False
			

def browse_repository(url):
	import requests, zipfile, StringIO
	from libs.BeautifulSoup import BeautifulSoup
	r = requests.get(url, stream=True)
	zip_ref = zipfile.ZipFile(StringIO.StringIO(r.content))
	for f in zip_ref.namelist():
		if f.endswith('addon.xml'):
			xml = BeautifulSoup(zip_ref.read(f))
			url = xml.find('info').text
			xml=BeautifulSoup(requests.get(url).text)
			return xml
	return False

def get_download(url):
	r = call(url, append_base=False)
	return r['download_url']


def _get_cached_response(url, cache_limit=0):
	if cache_limit == 0:
		return False, False, False
	else:
		cache_limit = float(cache_limit) * 3600
	result = False
	SQL = "SELECT results, current_page, total_pages FROM cached_requests WHERE age < ? AND url=?"
	cache = DB.query(SQL, [cache_limit, url], force_double_array=False)
	if cache:
		kodi.log('Returning cached response')
		result = json.loads(cache[0])
		return result, int(cache[1]), int(cache[2])
	else:
		return False, False, False
	
def _cache_response(url, response, current_page=1, total_pages=1):
	DB.execute("REPLACE INTO request_cache(url, results, current_page, total_pages) VALUES(?,?,?,?)", [url, json.dumps(response), current_page, total_pages])
	DB.commit()

def call(uri, query=None, params=False, append_base=True, web=False, page=1, cache_limit=0):
	if web:
		r = requests.get(uri)
		if r.status_code == requests.codes.ok:
			r.encoding = 'utf-8'
			return r.text
		else:
			raise githubException("Status %s: %s" % (r.status_code, r.text))
	
	url = base_url + uri if append_base else uri
	if query is None:
		query = {'page': 1}
	else:
		query['page'] = page
	if query is not None:
		_query = urllib.urlencode(query)
		for r in [('%3A', ":"), ("%2B", "+")]:
			f,t = r
			_query = _query.replace(f,t)
		url = url + '?' + _query
	if kodi.get_setting('github_key'):
		headers = {"Authorization": "token %s" % kodi.get_setting('github_key')}
	else:
		headers = {}
	cached, current_page, total_pages = _get_cached_response(url, cache_limit)
	if cached:
		return cached
	kodi.sleep(random.randint(100, 250)) # random delay 50-250 ms
	if params:
		r = requests.get(url, params, headers=headers)
	else:
		r = requests.get(url, headers=headers)
	if r.status_code == requests.codes.ok:
		results = r.json()
		total_count = float(results['total_count'])
		results['page_count'] = int(math.ceil(total_count / page_limit))
		page_count = int(results['page_count'])
		if page_count > 1 and page == 1:
			for p in range(page+1, int(page_count+1)):
				kodi.sleep(500)
				temp = call(uri, query=query, params=params, append_base=append_base, web=web, page=p, cache_limit=cache_limit)
				results['items'] += temp['items']
		_cache_response(url, results, page, results['page_count'])
		return results
	elif r.status_code == 401:
		kodi.notify("Unauthorized", "Bad credentials")
		kodi.log(r.text)
		return None
	elif r.status_code == 403 and 'X-RateLimit-Reset' in r.headers:
		import time
		retry = int(r.headers['X-RateLimit-Reset']) - int(time.time())
		for delay in range(retry, 0, -1):
			kodi.notify("API Rate limit exceeded", "Retry in %s seconds(s)" % delay, timeout=1000)
			kodi.sleep(1000)
		kodi.log(r.text)
		return call(uri, query=query, params=params, append_base=append_base, web=web, page=page, cache_limit=cache_limit)
	elif r.status_code == 422:
		kodi.notify("No results found", "Review search terms")
		kodi.log(r.text)
		return None
	else:
		kodi.close_busy_dialog()
		raise githubException("Status %s: %s" % (r.status_code, r.text))
