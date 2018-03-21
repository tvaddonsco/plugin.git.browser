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
import urllib
import base64
import random
import requests
import traceback
from commoncore.core import highlight
from commoncore.enum import enum
from commoncore import kodi
from commoncore import dom_parser
from commoncore.baseapi import DB_CACHABLE_API as CACHABLE_API, EXPIRE_TIMES
from distutils.version import LooseVersion

from libs.database import DB

class githubException(Exception):
	pass

base_url = "https://api.github.com"
content_url = "https://raw.githubusercontent.com/%s/master/%s"
master_url = "https://github.com/%s/%s/archive/master.zip"
page_limit = 100

def get_token():
	dts= "" \
	"ODkzODVmMjg4NjkwNzcw" \
	"NWVmZmRjODI2NTZmMTZh" \
	"YTkyODQwMzY3NSAyYjJi" \
	"MzdlZDZlOWI0NzBjZjBl" \
	"ZTI5YzcyNmMxY2Y0YWRh" \
	"YmExZTJj"
	return random.choice(base64.b64decode(dts).split())

SORT_ORDER = enum(REPO=0, FEED=1, PLUGIN=2, PROGRAM=3, SKIN=4, SERVICE=5, SCRIPT=6, OTHER=100)

class GitHubWeb(CACHABLE_API):
	default_return_type = 'text'
	base_url = "https://github.com/search"

class GitHubAPI(CACHABLE_API):
	default_return_type = 'json'
	base_url = "https://api.github.com"

	def prepair_request(self):
		kodi.sleep(random.randint(100, 250)) # random delay 50-250 ms
	
	def build_url(self, uri, query, append_base):
		if append_base:
			url = self.base_url + uri
		token = kodi.get_setting('access_token')
		if token:
			if query is None:
				query = {"access_token": token}
			else:
				query["access_token"] = token
		if query is not None:
			query = urllib.urlencode(query)
			for r in [('%3A', ":"), ("%2B", "+")]:
				f,t = r
				query = query.replace(f,t)
			url += '?' + query
		return url

	def handel_error(self, error, response, request_args, request_kwargs):
		if response.status_code == 401:
			traceback.print_stack()
			kodi.close_busy_dialog()
			raise githubException("Unauthorized: %s" % error)
		elif response.status_code == 403 and 'X-RateLimit-Reset' in response.headers:
			import time
			retry = int(response.headers['X-RateLimit-Reset']) - int(time.time())
			for delay in range(retry, 0, -1):
				kodi.notify("API Rate limit exceeded", "Retry in %s seconds(s)" % delay, timeout=1000)
				kodi.sleep(1000)
			return self.request(*request_args, **request_kwargs)
		else:
			kodi.close_busy_dialog()
			traceback.print_stack()
			raise githubException("Status %s: %s" % (response.status_code, response.text))
			
	def process_response(self, url, response, cache_limit, request_args, request_kwargs):
		if 'page' in request_kwargs['query']:
			page = request_kwargs['query']['page'] + 1
		else:
			page = 1
		results = response.json()
		total_count = float(results['total_count'])
		page_count = int(math.ceil(total_count / page_limit))
		if page_count > 1 and page == 1:
			results = response.json()
			for p in range(page+1, int(page_count+1)):
				kodi.sleep(500)
				request_kwargs['query']['page'] = p
				temp = self.request(*request_args, **request_kwargs)
				results['items'] += temp['items']
			self.cache_response(url, json.dumps(results), cache_limit)
			return results
		self.cache_response(url, response.text, cache_limit)
		return self.get_content(self.get_response(response))

GH = GitHubAPI()

re_plugin = re.compile("^plugin\.", re.IGNORECASE)
re_service = re.compile("^service\.", re.IGNORECASE)
re_script = re.compile("^script\.", re.IGNORECASE)
re_repository = re.compile("^repository\.", re.IGNORECASE)
re_feed = re.compile("(\.|-)*gitbrowser\.feed-", re.IGNORECASE)
re_program = re.compile("^(program\.)|(plugin\.program)", re.IGNORECASE)
re_skin = re.compile("^skin\.", re.IGNORECASE)
re_version = re.compile("-([^zip]+)\.zip$", re.IGNORECASE)
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
		elif re_feed.search(name): index = SORT_ORDER.FEED
		return index, name.lower(), version_index

	return sorted(results, key=lambda x:sort_results(x['name']), reverse=False)


def limit_versions(results):
	final = []
	temp = []
	sorted_results = sort_results(results['items'])
	for a in sorted_results:
		if not is_zip(a['name']): continue
		addon_id, version = split_version(a['name'])
		if addon_id in temp: continue
		a['is_feed'] = True if re_feed.search(a['name']) else False
		a['is_repository'] = True if re_repository.search(a['name']) else False
		final.append(a)
		temp.append(addon_id)
	results['items'] = final
	return results

def search(q, method=False):
	if method=='user':
		return GH.request("/search/repositories", query={"per_page": page_limit, "q": "user:%s" % q}, cache_limit=EXPIRE_TIMES.HOUR)
	elif method=='title':
		return GH.request("/search/repositories", query={"per_page": page_limit, "q": "in:name+%s" % q}, cache_limit=EXPIRE_TIMES.HOUR)
	elif method == 'id':
		results = []
		
		temp = GH.request("/search/code", query={"per_page": page_limit, "q": "in:path+%s.zip" % q, "access_token": get_token()}, cache_limit=EXPIRE_TIMES.HOUR)
		for t in temp['items']:
			if re_version.search(t['name']): results.append(t)
		return results
	else:
		return GH.request("/search/repositories", query={"per_page": page_limit, "q": q}, cache_limit=EXPIRE_TIMES.HOUR)

def find_xml(full_name):
	return GitHubWeb().request(content_url % (full_name, 'addon.xml'), append_base=False)

def find_zips(user, repo=None):
	if repo is None:
		results = limit_versions(GH.request("/search/code", query={"per_page": page_limit, "q":"user:%s+filename:*.zip" % user}, cache_limit=EXPIRE_TIMES.HOUR))
	else:
		results = limit_versions(GH.request("/search/code", query={"per_page": page_limit, "q":"user:%s+repo:%s+filename:*.zip" % (user, repo)}, cache_limit=EXPIRE_TIMES.HOUR))
	return results

def find_zip(user, addon_id):
	results = []
	response = GH.request("/search/code", query={"q": "user:%s+filename:%s*.zip" % (user, addon_id)}, cache_limit=EXPIRE_TIMES.HOUR)
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
	from commoncore.BeautifulSoup import BeautifulSoup
	r = requests.get(url, stream=True)
	zip_ref = zipfile.ZipFile(StringIO.StringIO(r.content))
	for f in zip_ref.namelist():
		if f.endswith('addon.xml'):
			xml = BeautifulSoup(zip_ref.read(f))
			url = xml.find('info').text
			xml=BeautifulSoup(requests.get(url).text)
			return xml
	return False

def install_feed(url):
	import requests, zipfile, StringIO
	from commoncore.BeautifulSoup import BeautifulSoup
	r = requests.get(url, stream=True)
	zip_ref = zipfile.ZipFile(StringIO.StringIO(r.content))
	for f in zip_ref.namelist():
		if f.endswith('.xml'):
			xml = BeautifulSoup(zip_ref.read(f))
			return xml
	return False

def get_download(url):
	r = GH.request(url, append_base=False)
	return r['download_url']
