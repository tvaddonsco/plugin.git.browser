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
import time
import json
import random
import hashlib
import zlib
import requests
import traceback
from sqlite3 import dbapi2 as database
from commoncore import kodi
from commoncore.filelock import FileLock
from commoncore import dom_parser
from commoncore.beautifulsoup import BeautifulSoup
	
vfs = kodi.vfs
CACHE = vfs.join(kodi.get_profile(), 'API_CACHE')
if not vfs.exists(CACHE): vfs.mkdir(CACHE, True)

try:
	from urllib.parse import urlencode
except ImportError:
	from urllib import urlencode

try:
	str_type = unicode
except:
	str_type = str

TYPES = kodi.enum(TEXT=str_type, STR=type(''), UTF8=type(u''), DICT=type({}), RESPONSE=requests.models.Response)
EXPIRE_TIMES = kodi.enum(FLUSH=-2, NEVER=-1, FIFTEENMIN=.25, THIRTYMIN=.5, HOUR=1, FOURHOURS=4, EIGHTHOURS=8, TWELVEHOURS=12, DAY=24, THREEDAYS=72, WEEK=168)

class baseException(Exception):
	pass

class connectionException(BaseException):
	pass

class responseException(BaseException):
	pass

class BASE_API():
	default_return_type = 'text'
	base_url = ''
	user_agent = ''
	accept = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
	requests = requests.Session()
	headers = {'Content-Type': 'text/html; charset=UTF-8', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'}
	timeout = 3
	def get_user_agent(self):
		if self.user_agent: return self.user_agent
		user_agent = kodi.get_property('user_agent')
		try: agent_refresh_time = int(kodi.get_property('agent_refresh_time'))
		except: agent_refresh_time = 0
		if not user_agent or agent_refresh_time < (time.time() - (7 * 24 * 60 * 60)):
			user_agent = self.generate_user_agent()
			kodi.set_property('user_agent', user_agent)
			kodi.set_property('agent_refresh_time', str(int(time.time())))
		return user_agent
	
	def generate_user_agent(self):
		BR_VERS = [
			['%s.0' % i for i in range(18, 43)],
			['41.0.2228.0', '41.0.2227.1', '41.0.2227.0', '41.0.2226.0', '40.0.2214.93', '37.0.2062.124'],
			['11.0'],
			['11.0']
		]
		WIN_VERS = ['Windows NT 10.0', 'Windows NT 7.0', 'Windows NT 6.3', 'Windows NT 6.2', 'Windows NT 6.1', 'Windows NT 6.0', 'Windows NT 5.1', 'Windows NT 5.0']
		FEATURES = ['; WOW64', '; Win64; IA64', '; Win64; x64', '']
		RAND_UAS = [
			'Mozilla/5.0 ({win_ver}{feature}; rv:{br_ver}) Gecko/20100101 Firefox/{br_ver}',
			'Mozilla/5.0 ({win_ver}{feature}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{br_ver} Safari/537.36',
			'Mozilla/5.0 ({win_ver}{feature}; Trident/7.0; rv:{br_ver}) like Gecko'
		]
		index = random.randrange(len(RAND_UAS))
		user_agent = RAND_UAS[index].format(win_ver=random.choice(WIN_VERS), feature=random.choice(FEATURES), br_ver=random.choice(BR_VERS[index]))
		
		return user_agent
	
	def set_user_agent(self, headers):
		ua = self.get_user_agent()
		if headers is None:
			headers = {}
		headers['User-Agent'] = ua
		if self.headers is None or not self.headers:
			self.headers = {}
		self.headers.update(headers)
	
	def build_url(self, uri, query, append_base):
		if append_base:
			url = self.base_url + uri
		else:
			url = uri
		if query is not None:
			url += '?' + urlencode(query, True)
		return url
	
	def authorize(self):
		pass
	
	def prepair_request(self):
		pass
	
	def prepair_query(self, query):
		return query
	
	def get_content(self, response):
		_type = type(response)
		if self.default_return_type == 'json':
			if _type in [TYPES.TEXT, TYPES.UTF8, TYPES.STR]:
				return json.loads(response)
		elif self.default_return_type == 'xml':
			import xml.etree.ElementTree as ET
			if type(response) == unicode:
				response = response.encode("utf-8", errors="ignore")
			return ET.fromstring(response)
		elif self.default_return_type == 'soup':
			return BeautifulSoup(response)
		elif self.default_return_type == 'html_dom':
			return dom_parser.parse_html(response)
		return response
	
	def get_response(self, response):	
		_type = type(response)
		if _type in [TYPES.TEXT, TYPES.UTF8]:
			return response
		elif _type == TYPES.RESPONSE:
				return response.text
		elif _type == TYPES.DICT:
			return str(response)
		return response

	def process_response(self, url, response, request_args, request_kwargs):
		return self.get_content(self.get_response(response))
	
	def handel_error(self, error, response, request_args, request_kwargs):
		kodi.log(error)
		if response is not None:
			kodi.log(response.url)
		traceback.print_stack()
		raise error
	
	def request(self, uri, query=None, data=None, append_base=True, headers=None, auth=None, method=None, timeout=None, encode_data=True):
		self.prepair_query(query)
		request_args = (uri,)
		request_kwargs = {"query": query, "data": data, "append_base": append_base, "headers": headers, "auth": auth, "method": method, "timeout": timeout, "encode_data": encode_data}
		self.set_user_agent(headers)
		if auth is not None:
			self.authorize()
		url = self.build_url(uri, query, append_base)
		self.prepair_request()
		if type(timeout) is not int or type(timeout) is not float: timeout = float(self.timeout)
		try:
			if data is None:
				if method == 'DELETE':
					response = self.requests.delete(url, headers=self.headers, timeout=timeout)
				else:
					response = self.requests.get(url, headers=self.headers, timeout=timeout)
			else:
				if encode_data: data = json.dumps(data)
				if method == 'PUT':
					response = self.requests.put(url, data=json.dumps(data), headers=self.headers, timeout=timeout)
				else:
					response = self.requests.post(url, data=data, headers=self.headers, timeout=timeout)
		except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.TooManyRedirects) as e:
			self.handel_error(connectionException(e), None, request_args, request_kwargs)
		if response.status_code == requests.codes.ok or response.status_code == 201:
			return self.process_response(url, response, request_args, request_kwargs)
		else:
			return self.handel_error(responseException(response.status_code), response, request_args, request_kwargs)
		
class CACHABLE_API(BASE_API):
	
	def get_cached_response(self, url, cache_limit):
		
		cache_hash = hashlib.md5(kodi.stringify(url)).hexdigest()
		cache_file = vfs.join(CACHE, cache_hash)
		if vfs.exists(cache_file):
			temp = vfs.read_file(cache_file + '.ts')
			if (time.time() - vfs.get_stat(cache_file).st_ctime()) / 3600 > int(temp):
				vfs.rm(cache_file, quiet=True)
				vfs.rm(cache_file + '.ts', quiet=True)
				return False
			else:
				response = zlib.decompress(vfs.read_file(cache_file))
				return response
		return False
	
	def process_response(self, url, response, cache_limit, request_args, request_kwargs):
		self.cache_response(url, response.text, cache_limit)
		return self.get_content(self.get_response(response))
		
	def cache_response(self, url, response, cache_limit):
		if response and cache_limit:
			cache_hash = hashlib.md5(kodi.stringify(url)).hexdigest()
			cache_file = vfs.join(CACHE, cache_hash)
			response = kodi.bytefy(response)
			compressed = zlib.compress(response)
			vfs.write_file(cache_file, compressed)
			vfs.write_file(cache_file+'.ts', str(cache_limit))
	
	def request(self, uri, query=None, data=None, append_base=True, headers=None, auth=None, method=None, timeout=None, encode_data=True, cache_limit=0):
		query = self.prepair_query(query)
		request_args = (uri,)
		request_kwargs = {"query": query, "data": data, "append_base": append_base, "headers": headers, "auth": auth, "method": method, "timeout": timeout, "cache_limit": cache_limit, "encode_data": encode_data}
		self.set_user_agent(headers)
		if auth is not None:
			self.authorize()
		url = self.build_url(uri, query, append_base)
		cached = self.get_cached_response(url, cache_limit)
		if cached:
			return self.get_content(cached)
		if type(timeout) is not int or type(timeout) is not float: timeout = float(self.timeout)
		try:
			if data is None:
				if method == 'DELETE':
					response = self.requests.delete(url, headers=self.headers, timeout=timeout)
				else:
					response = self.requests.get(url, headers=self.headers, timeout=timeout)
			else:
				if encode_data: data = json.dumps(data)
				if method == 'PUT':
					response = self.requests.put(url, data=data, headers=self.headers, timeout=timeout)
				else:
					response = self.requests.post(url, data=data, headers=self.headers, timeout=timeout)
		except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.TooManyRedirects) as e:
			self.handel_error(connectionException(e), None, request_args, request_kwargs)
		if response.status_code == requests.codes.ok or response.status_code == 201:
			return self.process_response( url, response, cache_limit, request_args, request_kwargs)
		else:
			return self.handel_error(responseException(response.status_code), response, request_args, request_kwargs)

class DB_CACHABLE_API(CACHABLE_API):
	custom_tables = False
	DB = False
	connected = False
	create_statements = [
		"""CREATE TABLE IF NOT EXISTS "version" (
			"db_version" INTEGER DEFAULT 1 UNIQUE,
			PRIMARY KEY(db_version));
		""",
		"""CREATE TABLE IF NOT EXISTS "request_cache" (
			"request_id" INTEGER PRIMARY KEY AUTOINCREMENT,
			"url" TEXT UNIQUE,
			"response" TEXT,
			"headers" TEXT,
			"ts" TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
		""",
		"""CREATE VIEW IF NOT EXISTS "cached_requests" AS 
			SELECT request_cache.*, (strftime('%s','now') -  strftime('%s',ts))  AS age 
			FROM request_cache;
		""",
		"""INSERT INTO version(db_version) VALUES(1);"""
	]
	def __init__(self, DB_Object=None):
		if DB_Object is None:
			self.dbf = vfs.join(CACHE, 'cached.db')
			self.db_lock = FileLock(self.dbf + '.lock')
			self.dbc = False
			self.dbh = False
			self.connect()
		else:
			self.DB=DB_Object
			def cache_response(url, response, cache_limit):
				if cache_limit == 0:
					return False
				self.DB.execute("REPLACE INTO request_cache(url, response) VALUES(?,?)", [url, response])
				self.DB.commit()
			self.cache_response = cache_response
			def get_cached_response(url, cache_limit):
				if cache_limit == 0:
					return False
				else:
					cache_limit = float(cache_limit) * 3600
				if cache_limit == -1:
					results = self.DB.query("SELECT response FROM cached_requests WHERE url=?", [url], force_double_array=False)
				elif callable(cache_limit):
					if cache_limit():
						results = self.DB.query("SELECT response FROM cached_requests WHERE url=?", [url], force_double_array=False)
					else: return False
				else:
					results = self.DB.query("SELECT response FROM cached_requests WHERE age < ? AND url=?", [cache_limit, url], force_double_array=False)
				if results:
					return results[0]
				return False
			self.get_cached_response = get_cached_response
		
	def connect(self):
		self.dbh = database.connect(self.dbf, check_same_thread=False)
		self.dbc = self.dbh.cursor()
		with self.db_lock:
			try:
				self.query("SELECT db_version FROM version")
			except:
				if self.custom_tables:
					statements = self.create_statements + self.custom_tables
				else:
					statements = self.create_statements
				for SQL in statements:
					self.execute(SQL)
				self.commit()
		self.connected = True
	
	def commit(self):
		self.dbh.commit()
	
	def prepaire_sql(self, SQL):
		if SQL.upper().startswith('REPLACE INTO'): SQL = 'INSERT OR ' + SQL
		return SQL
		
	def query(self, SQL, data=[]):
		SQL = self.prepaire_sql(SQL)
		self.dbc.execute(SQL, data)
		return self.dbc.fetchall()

	def execute(self, SQL, data=[]):
		SQL = self.prepaire_sql(SQL)
		self.dbc.execute(SQL, data)
			
	def get_cached_response(self, url, cache_limit):
		if cache_limit == 0:
			return False
		else:
			cache_limit = float(cache_limit) * 3600
		with self.db_lock:
			if cache_limit == -1:
				self.execute("SELECT response FROM cached_requests WHERE url=?", [url])
			elif cache_limit == -2:
				self.execute("DELETE FROM cached_requests WHERE url=?", [url])
				self.commit()
				self.db_lock.release()
				return False
			elif callable(cache_limit):
				if cache_limit():
					self.execute("SELECT response FROM cached_requests WHERE url=?", [url])
					self.db_lock.release()
				else: return False
			else:
				self.execute("SELECT response FROM cached_requests WHERE age < ? AND url=?", [cache_limit, url])
			results = self.dbc.fetchone()
			if results:
				self.db_lock.release()
				return results[0]
		return False
	
	def cache_response(self, url, response, cache_limit):
		if cache_limit == 0:
			return False
		with self.db_lock:
			self.execute("REPLACE INTO request_cache(url, response) VALUES(?,?)", [url, response])
			self.commit()

class MYSQL_CACHABLE_API(DB_CACHABLE_API):
	custom_tables = False
	connected = False
	db_lock = True
	create_statements = [
		"""SET autocommit=0;""",
		"""START TRANSACTION;""",
		"""CREATE TABLE IF NOT EXISTS `version` (
			`db_version` int(11) NOT NULL DEFAULT 1,
			PRIMARY KEY(`db_version`));
		""",
		"""CREATE TABLE IF NOT EXISTS `request_cache` (
			`request_id` int(11) NOT NULL AUTO_INCREMENT,
			`url` VARCHAR(1024) NOT NULL UNIQUE,
			`response` LONGBLOB,
			`headers` LONGBLOB,
			`ts` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
			PRIMARY KEY(`request_id`));
		""",
		"""CREATE OR REPLACE VIEW `cached_requests` AS 
			SELECT request_cache.*, 
			timestampdiff(SECOND, `request_cache`.`ts`, NOW()) AS `age`
			FROM request_cache;
		""",
		"""INSERT INTO version(db_version) VALUES(1);""",
	]
	def __init__(self, db_host, db_name, db_user, db_pass, db_port=3306):
		self.dsn = {
				"database": db_name,
				"host": db_host,
				"port": int(db_port),
				"user": str(db_user),
				"password": str(db_pass),
				"buffered": True
		}
		self.connect()
		
	def connect(self):
		import mysql.connector as database
		self.dbh = database.connect(**self.dsn)
		self.dbc = self.dbh.cursor()
		try:
			self.query("SELECT db_version FROM version")
		except:
			if self.custom_tables:
				statements = self.create_statements + self.custom_tables + ["COMMIT;", "SET autocommit=1;"]
			else:
				statements = self.create_statements
			for SQL in statements:
				self.execute(SQL)
				
			self.commit()
		self.connected = True
	
	def prepaire_sql(self, SQL):
		SQL = SQL.replace('?', '%s')
		return SQL
	
	def get_cached_response(self, url, cache_limit):
		if cache_limit == 0:
			return False
		else:
			cache_limit = float(cache_limit) * 3600
		if cache_limit == -1:
			self.execute("SELECT response FROM cached_requests WHERE url=?", [url])
		elif callable(cache_limit):
			if cache_limit():
				self.execute("SELECT response FROM cached_requests WHERE url=?", [url])
			else: return False
		else:
			self.execute("SELECT response FROM cached_requests WHERE age < ? AND url=?", [cache_limit, url])
		results = self.dbc.fetchone()
		if results:
			return results[0]
		return False
	
	def cache_response(self, url, response, cache_limit):
		if cache_limit == 0:
			return False
		self.execute("REPLACE INTO request_cache(url, response) VALUES(?,?)", [url, response])
		self.commit()	

