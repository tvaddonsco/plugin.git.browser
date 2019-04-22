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
from commoncore import kodi
from commoncore import filelock
import traceback

class DatabaseException(Exception):
	pass

regex_replace = re.compile("^[\s\t\n]*replace[\s\t\n]*into[\s\t\n]*", re.IGNORECASE)

class BASEDatabase:
	__lock = False
	__connected = False
	__ignore_errors = [re.compile('column (.)+ is not unique$', re.IGNORECASE), re.compile('UNIQUE constraint failed', re.IGNORECASE), re.compile('no such table: version', re.IGNORECASE)]
	autoconnect = True
	
	def __init__(self, quiet=False, version=1):
		self.quiet=quiet
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
		self.DBH.commit()

	def do_init(self):
		do_init = True
		try:	
			test = self.query("SELECT 1 FROM version WHERE db_version >= ?", [self.db_version], force_double_array=False, quiet=True)
			if test:
				do_init = False
		except:
			do_init = True
		return do_init
	
	def dict_factory(self, cursor, row):
		d = {}
		for idx, col in enumerate(cursor.description):
			d[col[0]] = row[idx]
		return d

	def ignore_errors(self, e):
		err = str(e)
		for test in self.__ignore_errors:
			if test.search(err): return True

	def handel_error(self, error):
		traceback.print_stack()
		raise error
	
	def prepaire_sql(self, SQL):
		if regex_replace.search(SQL): SQL = 'INSERT OR ' + SQL
		return SQL

	def query(self, SQL, data=None,force_double_array=True, quiet=False):
		SQL = self.prepaire_sql(SQL)
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
		except Exception as e:
			if self.quiet is False or quiet is False and not self.ignore_errors(e):
				self.handel_error(DatabaseException("Database Error: %s" % e))
				kodi.log("Database Error: %s" % e)

	def query_assoc(self, SQL, data=None, force_double_array=True, quiet=False):
		SQL = self.prepaire_sql(SQL)
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
		except Exception as e:
			if self.quiet is False or quiet is False and not self.ignore_errors(e):
				self.handel_error(DatabaseException("Database Error: %s" % e))
				kodi.log("Database Error: %s" % e)
		
	def execute(self, SQL, data=[], quiet=False):
		SQL = self.prepaire_sql(SQL)
		try:
			if data:
				self.DBC.execute(SQL, data)
			else:
				self.DBC.execute(SQL)
			try:
				self.lastrowid = self.DBC.lastrowid
			except:
				self.lastrowid = None
		except Exception as e:
			if self.quiet is False or quiet is False and not self.ignore_errors(e):
				self.handel_error(DatabaseException("SQLite Database Error: %s" % e))
				kodi.log("Database Error: %s" % e)

	def execute_many(self, SQL, data, quiet=False):
		SQL = self.prepaire_sql(SQL)
		try:
			self.DBC.executemany(SQL, data)
		except Exception as e:
			if self.quiet is False or quiet is False and not self.ignore_errors(e):
				self.handel_error(DatabaseException("Database Error: %s" % e))
				kodi.log("Database Error: %s" % e)
	
	def run_script(self, sql_file, commit=True):
		if kodi.vfs.exists(sql_file):
			full_sql = kodi.vfs.read_file(sql_file)
			sql_stmts = full_sql.split(';')
			for SQL in sql_stmts:
				if SQL is not None and len(SQL.strip()) > 0:
					self.execute(SQL, quiet=True)
			if commit: self.commit()
			return True
		else:
			return False
				
class SQLiteDatabase(BASEDatabase):
	db_lock = None
	def __init__(self, db_file='', version=1, quiet=False, connect=True):
		self.quiet=quiet
		self.db_type = 'sqlite'
		self.lastrowid = None
		self.db_file = db_file
		self.db_lock = filelock.FileLock(db_file + ".lock")
		self.db_version = version
		if connect: self._connect()
		if self.do_init(): self._initialize()
	
	def commit(self):
		with self.db_lock:
			self.DBH.commit()

	def query(self, SQL, data=None,force_double_array=True, quiet=False):
		SQL = self.prepaire_sql(SQL)
		with self.db_lock:
			try:
				if data:
					self.DBC.execute(SQL, data)
				else:
					self.DBC.execute(SQL)
				rows = self.DBC.fetchall()
				if(len(rows)==1 and not force_double_array):

					self.db_lock.release()
					return rows[0]
				else:
					self.db_lock.release()
					return rows
			except Exception as e:
				if self.quiet is False or quiet is False and not self.ignore_errors(e):
					self.handel_error(DatabaseException("SQLite Database Error: %s" % e))
					kodi.log("SQLite Database Error: %s" % e)
			finally:
				self.db_lock.release()
				
	def query_assoc(self, SQL, data=None, force_double_array=True, quiet=False):
		SQL = self.prepaire_sql(SQL)
		with self.db_lock:
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
					self.db_lock.release()
					return rows[0]
				else:
					self.db_lock.release()
					return rows
			except Exception as e:
				if self.quiet is False or quiet is False and not self.ignore_errors(e):
					self.handel_error(DatabaseException("SQLite Database Error: %s" % e))
					kodi.log("SQLite Database Error: %s" % e)
			finally:
				del DBH
				self.db_lock.release()
			
	def execute(self, SQL, data=[], quiet=False):
		SQL = self.prepaire_sql(SQL)
		with self.db_lock:
			try:
				if data:
					self.DBC.execute(SQL, data)
				else:
					self.DBC.execute(SQL)
				try:
					self.lastrowid = self.DBC.lastrowid
				except:
					self.lastrowid = None
			except Exception as e:
				if self.quiet is False or quiet is False and not self.ignore_errors(e):
					self.handel_error(DatabaseException("SQLite Database Error: %s" % e))
					kodi.log("SQLite Database Error: %s" % e)
			finally:
				self.db_lock.release()

	def execute_many(self, SQL, data, quiet=False):
		SQL = self.prepaire_sql(SQL)
		with self.db_lock:
			try:
				self.DBC.executemany(SQL, data)
			except Exception as e:
				if self.quiet is False or quiet is False and not self.ignore_errors(e):
					self.handel_error(DatabaseException("SQLite Database Error: %s" % e))
					kodi.log("SQLite Database Error: %s" % e)
			finally:
				self.db_lock.release()

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
		directory = kodi.vfs.dirname(self.db_file)
		if not kodi.vfs.exists(directory): kodi.vfs.mkdir(directory)
		self.DBH = database.connect(self.db_file, check_same_thread=False)
		try:
			self.DBC = self.DBH.cursor()
			self.__connected = True	
		except Exception as e:
			self.handel_error(DatabaseException("SQLite Database Error: %s" % e))
			kodi.log("SQLite Database Error: %s" % e)

class MySQLDatabase(BASEDatabase):
	__ignore_errors = [re.compile('1062: Duplicate entry', re.IGNORECASE)]
	
	def __init__(self, host, dbname, username, password, port, version=1, quiet=False, connect=True):
		self.quiet=quiet
		self.db_type = 'mysql'
		self.lastrowid = None
		self.host = host
		self.dbname = dbname
		self.username=username
		self.password = password
		self.port = port
		self.db_version = version
		if connect: self._connect()
		if self.do_init(): self._initialize()	

	def _connect(self):
		try:	
			import mysql.connector as database
			dsn = {
					"database": self.dbname,
					"host": self.host,
					"port": int(self.port),
					"user": str(self.username),
					"password": str(self.password),
					"buffered": True
			}
			self.DBH = database.connect(**dsn)
			self.DBC = self.DBH.cursor()
			self.__connected = True
		except Exception as e:
			self.handel_error(DatabaseException("MySQL Database Error: %s" % e))
		

	def prepaire_sql(self, SQL):
		SQL = SQL.replace('?', '%s')
		return SQL

	def execute(self, SQL, data=[], quiet=False):
		try:
			if data:
				SQL = self.prepaire_sql(SQL)
				self.DBC.execute(SQL, data)
			else:
				self.DBC.execute(SQL)
			try:
				self.lastrowid = self.DBC.lastrowid
			except:
				self.lastrowid = None
		except Exception as e:
			if self.quiet is False or quiet is False and not self.ignore_errors(e):
				self.handel_error(DatabaseException("MySQL Database Error: %s" % e))

	def execute_many(self, SQL, data, quiet=False):
		try:
			SQL = SQL.replace('?', '%s')
			self.DBC.executemany(SQL, data)
		except Exception as e:
			if self.quiet is False or quiet is False and not self.ignore_errors(e):
				self.handel_error(DatabaseException("MySQL Database Error: %s" % e))

	def query(self, SQL, data=None, force_double_array=True, quiet=False):
		try:
			if data:
				SQL = self.prepaire_sql(SQL)
				self.DBC.execute(SQL, data)
			else:
				self.DBC.execute(SQL)
			rows = self.DBC.fetchall()
			if(len(rows)==1 and not force_double_array):
				return rows[0]
			else:
				return rows
		except Exception as e:
			if self.quiet is False or quiet is False and not self.ignore_errors(e):
				self.handel_error(DatabaseException("MySQL Database Error: %s" % e))
		
	def query_assoc(self, SQL, data=None, force_double_array=True, quiet=False):
		try:
			if data:
				SQL = self.prepaire_sql(SQL)
				self.DBC.execute(SQL, data)
			else:
				self.DBC.execute(SQL)
			rows = self.DBC.fetchall()
			if(len(rows)==1 and not force_double_array):
				d = {}
				for idx, col in enumerate(self.DBC.column_names):
					d[col] = row[0][idx]
				return d
			else:
				set = []
				for row in rows:
					d = {}
					for idx, col in enumerate(self.DBC.column_names):
						d[col] = row[idx]
					set.append(d)
				return set
		except Exception as e:
			if self.quiet is False or quiet is False and not self.ignore_errors(e):
				self.handel_error(DatabaseException("MySQL Database Error: %s" % e))

