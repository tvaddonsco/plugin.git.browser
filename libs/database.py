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
import re
import xbmc
import xbmcaddon
import threading
import os
import kodi
IGNORE_UNIQUE_ERRORS = True


class DatabaseClass:
	__lock = False
	__connected = False
	autoconnect = True
	
	def __init__(self, quiet=False, version=1):
		self.quiet=quiet
		self._unique_str = 'column (.)+ is not unique$'
		self.db_version = version

	def disconnect(self):
		if self.db_type == 'sqlite':
			self.DBC.close()
		else:
			self.DBC.close()
		self.__connected = False

	def connect(self):
		if self.__connected is False: 
			self._connect()

	def commit(self):
		if self.db_type == 'sqlite' and self.quiet is False:
			kodi.log("Commiting to %s" % self.db_file)
		elif self.quiet is False:
			kodi.log("Commiting to %s on %s" % (self.dbname, self.host))
		self.DBH.commit()

	def check_version(self, previous, current):
		if not re.search('\d+\.\d+\.\d+', str(previous)): return True
		p = previous.split('.')
		c = current.split('.')
		if int(p[0]) < int(c[0]): return True
		if int(p[1]) < int(c[1]): return True
		if int(p[2]) < int(c[2]): return True
		return False
	
	def do_init(self):
		do_init = True
		try:	
			test = self.query("SELECT 1 FROM version WHERE db_version >= ?", [self.db_version], force_double_array=False, silent=True)
			if test:
				kodi.set_setting("database.version", self.db_version)
				do_init = False
		except:
			do_init = True
		return do_init
	
	def dict_factory(self, cursor, row):
		d = {}
		for idx, col in enumerate(cursor.description):
			d[col[0]] = row[idx]
		return d

	def query(self, SQL, data=None,force_double_array=True, silent=False):
		try:
			if data:
				self.DBC.execute(SQL, data)
			else:
				self.DBC.execute(SQL)
			rows = self.DBC.fetchall()
			if(len(rows)==1 and not force_double_array):
				return rows[0]
			else:
				return rows
		except Exception, e:
			if silent is False and 'no such table: version' not in str(e).lower():
				kodi.raise_error("Database error", e)
			kodi.log("Database error: %s" % e)

	def query_assoc(self, SQL, data=None, force_double_array=True, silent=False):
		try:
			self.DBH.row_factory = self.dict_factory
			cur = self.DBH.cursor()
			if data:
				cur.execute(SQL, data)
			else:
				cur.execute(SQL)
			rows = cur.fetchall()
			cur.close()
			if(len(rows)==1 and not force_double_array):
				return rows[0]
			else:
				return rows
		except Exception, e:
			if silent is False and 'no such table: version' not in str(e).lower():
				kodi.raise_error("Database error", e)
			kodi.log("Database error: %s" % e)
		
	def execute(self, SQL, data=[], silent=False):
		if SQL.startswith('REPLACE INTO'): SQL = 'INSERT OR ' + SQL
		try:
			if data:
				self.DBC.execute(SQL, data)
			else:
				self.DBC.execute(SQL)
			try:
				self.lastrowid = self.DBC.lastrowid
			except:
				self.lastrowid = None
		except Exception, e:
			if silent is False and IGNORE_UNIQUE_ERRORS and re.match(self._unique_str, str(e)):
				kodi.raise_error("Database error", e)
				kodi.log(SQL)
				kodi.log("Database error: %s" % e)

	def execute_many(self, SQL, data, silent=False):
		if SQL.startswith('REPLACE INTO'): SQL = 'INSERT OR ' + SQL
		try:
			self.DBC.executemany(SQL, data)
		except Exception, e:
			if silent is False and IGNORE_UNIQUE_ERRORS and re.match(self._unique_str, str(e)):
				kodi.raise_error("Database error", e)
				kodi.log(SQL)
				kodi.log("Database error: %s" % e)
	
	def run_script(self, sql_file, commit=True):
		if kodi.vfs.exists(sql_file):
			full_sql = kodi.vfs.read_file(sql_file)
			sql_stmts = full_sql.split(';')
			for SQL in sql_stmts:
				if SQL is not None and len(SQL.strip()) > 0:
					self.execute(SQL, silent=True)
					print SQL
			if commit: self.commit()
			return True
		else:
			return False
				
class SQLiteDatabase(DatabaseClass):
	__lock = threading.Lock()
	
	def __init__(self, db_file='', version=1, quiet=False, connect=True, check_version=True):
		self.quiet=quiet
		self._unique_str = 'column (.)+ is not unique$'
		self.db_type = 'sqlite'
		self.lastrowid = None
		self.db_file = db_file
		self.db_version = version
		self.verify_version = check_version
		if connect: self._connect()
		if self.do_init(): self._initialize()
	
	def commit(self):
		if self.quiet is False:
			kodi.log("Commiting to %s" % self.db_file)
		self.__lock.acquire(True)
		self.DBH.commit()
		self.__lock.release()


	def query(self, SQL, data=None,force_double_array=True, silent=False):
		self.__lock.acquire(True)
		try:
			if data:
				self.DBC.execute(SQL, data)
			else:
				self.DBC.execute(SQL)
			rows = self.DBC.fetchall()
			if(len(rows)==1 and not force_double_array):
				self.__lock.release()
				return rows[0]
			else:
				self.__lock.release()
				return rows
		except Exception, e:
			kodi.log(e)
			kodi.log(silent)
			err = str(e).lower()
			if silent is False and 'no such table: version' not in err:
				kodi.raise_error("Database error", e)
			kodi.log(SQL)	
			kodi.log("Database error: %s" % e)
		self.__lock.release()
			
	def query_assoc(self, SQL, data=None, force_double_array=True, silent=False):
		self.__lock.acquire(True)
		try:
			try:
				from sqlite3 import dbapi2 as database
			except:
				from pysqlite2 import dbapi2 as database
			DBH = database.connect(self.db_file, check_same_thread=False)
			DBH.row_factory = self.dict_factory
			cur = DBH.cursor()
			if data:
				cur.execute(SQL, data)
			else:
				cur.execute(SQL)
			rows = cur.fetchall()
			if(len(rows)==1 and not force_double_array):
				self.__lock.release()
				return rows[0]
			else:
				self.__lock.release()
				return rows
		except Exception, e:
			err = str(e).lower()
			if silent is False and 'no such table: version' not in err:
				kodi.raise_error("Database error", e)
			kodi.log(SQL)	
			kodi.log("Database error: %s" % e)
		del DBH	
		self.__lock.release()
			
	def execute(self, SQL, data=[], silent=False):
		if SQL.startswith('REPLACE INTO'): SQL = 'INSERT OR ' + SQL
		self.__lock.acquire(True)
		try:
			if data:
				self.DBC.execute(SQL, data)
			else:
				self.DBC.execute(SQL)
			try:
				self.lastrowid = self.DBC.lastrowid
			except:
				self.lastrowid = None
		except Exception, e:
			if silent is False and IGNORE_UNIQUE_ERRORS and re.match(self._unique_str, str(e)):
				kodi.raise_error("Database error", e)
				kodi.log(SQL)
				kodi.log("Database error: %s" % e)
		self.__lock.release()

	def execute_many(self, SQL, data, silent=False):
		if SQL.startswith('REPLACE INTO'): SQL = 'INSERT OR ' + SQL
		self.__lock.acquire(True)
		try:
			self.DBC.executemany(SQL, data)
		except Exception, e:
			if silent is False and IGNORE_UNIQUE_ERRORS and re.match(self._unique_str, str(e)):
				kodi.raise_error("Database error", e)
				kodi.log(SQL)
				kodi.log("Database error: %s" % e)
		self.__lock.release()

	def _connect(self):
		if self.quiet is False:
			kodi.log("Connecting to " + self.db_file)
		try:
			from sqlite3 import dbapi2 as database
			if self.quiet is False:
				kodi.log("%s loading sqlite3 as DB engine" % kodi.get_name())
		except:
			from pysqlite2 import dbapi2 as database
			if self.quiet is False:
				kodi.log("%s loading pysqlite2 as DB engine"  % kodi.get_name())
		if self.quiet is False:
			kodi.log("Connecting to SQLite on: " + self.db_file)
		directory = os.path.dirname(self.db_file)
		if not kodi.vfs.exists(directory): kodi.vfs.mkdir(directory)
		self.DBH = database.connect(self.db_file, check_same_thread=False)
		try:
			self.DBC = self.DBH.cursor()
		except Exception, e:
			kodi.log(e)
			kodi.raise_error("SqlLite Error", e)
			sys.exit()
		self.__connected = True

DB_TYPE = 'sqlite'
DB_FILE = kodi.vfs.join(kodi.get_profile(), 'cache.db')
	
class DBI(SQLiteDatabase):
	def _initialize(self):
		self.connect()
		schema_file = kodi.vfs.join(kodi.get_path(), 'resources/database/schema.%s.sql' % self.db_type)
		if self.run_script(schema_file, commit=False):
			self.execute('DELETE FROM version WHERE 1', silent=True)
			self.execute('INSERT INTO version(db_version) VALUES(?)', [self.db_version], silent=True)
			self.commit()
		self.disconnect()

DB = DBI(DB_FILE, quiet=True, connect=True)
