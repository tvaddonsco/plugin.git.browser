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
import base64
import random
import requests
import traceback
from commoncore import kodi
from commoncore import dom_parser
from commoncore.baseapi import DB_CACHABLE_API as CACHABLE_API, EXPIRE_TIMES
from distutils.version import LooseVersion
try:
	from urllib.parse import urlencode
except ImportError:
	from urllib import urlencode
import github
from github import DB

class githubException(Exception):
	pass

default_branch = 'master'
base_url = "https://api.github.com"
content_url = "https://raw.githubusercontent.com/%s/%s/%s"
page_limit = 100

def get_token():
	dts= "" \
	"NzUxOTg0NjE5YWY3MTEzNmY2ZDM2ZGM4NzFkNzcxY2FjYzZlZG" \
	"ExNiBlNDQ5Zjc0MjM4ZTY1Mjc1ODIwYjk0Zjc1ZTAxOTE1Njhh" \
	"NDI3M2Q2IDdiMjFkMTJkMzgzOGFiODYzYzlhMzNhNzZkN2MxZj" \
	"k0N2M3NDFjMTcgNDhjMjlkN2FjMzUwMWRlM2JhYzU2ODk4NmI2" \
	"NjJkZWM1MDYyZDA5YyA0NTY3NWVkMzBhMmNkNmQ5MTM4YzQwOT" \
	"g3NGVhNzRlY2RjYWQ5ZDUzIDBmMmE1MzI0NWM5N2VmNjQ0MmFl" \
	"NzA0ZjQwYTMzYzUxODdkNzhiNzkgMDNlMDUwOGQxYzE0YjQwZG" \
	"ZmZmIwNDcwM2FlM2I3MzllNDZmMTQxNCAzM2RmZTk1OWRiNTYy" \
	"OWIzMTlkY2U3NzhmYjQwNjkwM2FkYTA4ZjMyIDg1ZDBmMDhhND" \
	"U5ZGM3YmQyNzg1YWJmMTU4M2NkNGVkYzBhM2YxNjMgM2U0NDY2" \
	"ZTkwYTZhM2Y0NmU1OWU5ZjI4ZDAzNjE5ZmNiMWE4YTMyMiA4OT" \
	"M4NWYyODg2OTA3NzA1ZWZmZGM4MjY1NmYxNmFhOTI4NDAzNjc1" \
	"IDJiMmIzN2VkNmU5YjQ3MGNmMGVlMjljNzI2YzFjZjRhZGFiYT" \
	"FlMmM="
	return random.choice(base64.b64decode(dts).split())

SORT_ORDER = kodi.enum(REPO=0, FEED=1, INSTALLER=2, PLUGIN=3, PROGRAM=4, SKIN=5, SERVICE=6, SCRIPT=7, OTHER=100)

#class GitHubWeb(CACHABLE_API):
#	default_return_type = 'text'
#	base_url = "https://github.com/search"

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
			query = urlencode(query)
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
		elif response.status_code == 422 and 'Only the first 1000' in response.text:
			kodi.handel_error('Result count exceeds API limit.', 'Try different search or result filter.')
			kodi.close_busy_dialog()
			traceback.print_stack()
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
re_repository = re.compile("[\.\-_]?repo(sitory)?[\.\-_]?", re.IGNORECASE)
re_feed = re.compile("(\.|-)*gitbrowser\.feed-", re.IGNORECASE)
re_installer = re.compile("(\.|-)*gitbrowser\.installer-", re.IGNORECASE)
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

def get_download_url(full_name, path):
	url = content_url % (full_name, default_branch, path)
	if github.test_url(url): return url
	# didn't work, need to get the branch name
	response = requests.get("https://api.github.com/repos/%s/branches" % full_name).json()
	for attempt in response:
		branch = attempt['name']
		url = content_url % (full_name, branch, path)
		if github.test_url(url): return url
	raise githubException('No available download link')

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

def version_sort(name):
	v = re_version.search(name)
	if v:
		return LooseVersion(v.group(1))
	else:
		return LooseVersion('0.0.0')

def sort_results(results, limit=False):
	def highest_versions(results):
		last = ""
		final = []
		for a in results:
			addon_id, version = split_version(a['name'])
			if addon_id == last: continue
			last = addon_id
			final.append(a)
		return final

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
		elif re_installer.search(name): index = SORT_ORDER.INSTALLER
		return index, name.lower(), version_index
	if limit:
		return highest_versions(sorted(results, key=lambda x:sort_results(x['name']), reverse=True))
	else:
		return sorted(results, key=lambda x:sort_results(x['name']), reverse=False)



def limit_versions(results):
	final = []
	sorted_results = sort_results(results['items'], True)
	for a in sorted_results:
		if not is_zip(a['name']): continue
		a['is_feed'] = True if re_feed.search(a['name']) else False
		a['is_installer'] = True if re_installer.search(a['name']) else False
		a['is_repository'] = True if re_repository.search(a['name']) else False
		final.append(a)
	results['items'] = final
	return results

def search(q, method=False):
	if method=='user':
		return GH.request("/search/repositories", query={"per_page": page_limit, "q": "user:%s" % q}, cache_limit=EXPIRE_TIMES.HOUR)
	elif method=='title':
		return GH.request("/search/repositories", query={"per_page": page_limit, "q": "in:name %s" % q}, cache_limit=EXPIRE_TIMES.HOUR)
	elif method == 'id':
		results = []
		temp = GH.request("/search/code", query={"per_page": page_limit, "q": "in:path %s.zip" % q, "access_token": get_token()}, cache_limit=EXPIRE_TIMES.HOUR)
		for t in temp['items']:
			if re_version.search(t['name']): results.append(t)
		return results
	else:
		return GH.request("/search/repositories", query={"per_page": page_limit, "q": q}, cache_limit=EXPIRE_TIMES.HOUR)

#def find_xml(full_name):
#	return GitHubWeb().request(content_url % (full_name, default_branch, 'addon.xml'), append_base=False)

def find_zips(user, repo=None):
	filters = {'Repository': '*repository*.zip', 'Feed': '*gitbrowser.feed*.zip', 'Installer': '*gitbrowser.installer*.zip', 'Music Plugin': '*plugin.audio*.zip', 'Video Plugin': '*plugin.video*.zip', 'Script': '*script*.zip'}
	filter = kodi.get_property('search.filter')
	if filter in filters:
		q = filters[filter]
	else:
		q = '*.zip'
	if repo is None:
		results = limit_versions(GH.request("/search/code", query={"per_page": page_limit, "q":"user:%s filename:%s" % (user, q)}, cache_limit=EXPIRE_TIMES.HOUR))
	else:
		results = limit_versions(GH.request("/search/code", query={"per_page": page_limit, "q":"user:%s repo:%s filename:%s" % (user, repo, q)}, cache_limit=EXPIRE_TIMES.HOUR))
	return results

def find_zip(user, addon_id):
	results = []
	response = GH.request("/search/code", query={"q": "user:%s filename:%s*.zip" % (user, addon_id)}, cache_limit=EXPIRE_TIMES.HOUR)
	if response is None: return False, False, False
	if response['total_count'] > 0:
		test = re.compile("%s(-.+\.zip|\.zip)$" % addon_id, re.IGNORECASE)
		def sort_results(name):
			version = get_version_by_name(name)
			return LooseVersion(version)

		response['items'].sort(key=lambda k: sort_results(k['name']), reverse=True)

		for r in response['items']:
			if test.match(r['name']):
				url = get_download_url(r['repository']['full_name'], r['path'])
				version = get_version_by_name(r['path'])
				return url, r['name'], r['repository']['full_name'], version
	return False, False, False, False


def browse_repository(url):
	import requests
	from commoncore import zipfile
	from commoncore.beautifulsoup import BeautifulSoup
	r = requests.get(url, stream=True)
	if kodi.strings.PY2:
		import StringIO
		zip_ref = zipfile.ZipFile(StringIO.StringIO(r.content))
	else:
		from io import BytesIO
		zip_ref = zipfile.ZipFile(BytesIO(r.content))
	for f in zip_ref.namelist():
		if f.endswith('addon.xml'):
			xml = BeautifulSoup(zip_ref.read(f))
			url = xml.find('info').text
			xml=BeautifulSoup(requests.get(url).text)
			return xml
	return False

def install_feed(url, local=False):
	import requests
	from commoncore import zipfile
	if kodi.strings.PY2:
		from StringIO import StringIO as byte_reader
	else:
		from io import BytesIO as byte_reader

	from commoncore.beautifulsoup import BeautifulSoup
	if local:
			r = kodi.vfs.open(url, "r")
			if kodi.strings.PY2:
				zip_ref = zipfile.ZipFile(byte_reader(r.read()))
			else:
				zip_ref = zipfile.ZipFile(byte_reader(r.readBytes()))
	else:
		r = requests.get(url, stream=True)
		zip_ref = zipfile.ZipFile(byte_reader(r.content))

	for f in zip_ref.namelist():
		if f.endswith('.xml'):
			xml = BeautifulSoup(zip_ref.read(f))
			return xml
	return False

def batch_installer(url, local=False):
	import requests
	from commoncore import zipfile
	if kodi.strings.PY2:
		from StringIO import StringIO as byte_reader
	else:
		from io import BytesIO as byte_reader
	from commoncore.beautifulsoup import BeautifulSoup
	if local:
			r = kodi.vfs.open(url, "r")
			if kodi.strings.PY2:
				zip_ref = zipfile.ZipFile(byte_reader(r.read()))
			else:
				zip_ref = zipfile.ZipFile(byte_reader(r.readBytes()))
	else:
		r = requests.get(url, stream=True)
		zip_ref = zipfile.ZipFile(byte_reader(r.content))
	xml = BeautifulSoup(zip_ref.read('manifest.xml'))
	return xml, zip_ref

#def get_download(url):
#	r = GH.request(url, append_base=False)
#	return r['download_url']
