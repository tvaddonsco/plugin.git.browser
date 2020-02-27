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
from commoncore.database import SQLiteDatabase

DB_TYPE = 'sqlite'
DB_FILE = kodi.vfs.join(kodi.get_profile(), 'cache.db')

class DBI(SQLiteDatabase):
	def _initialize(self):
		self.connect()
		schema_file = kodi.vfs.join(kodi.get_path(), 'resources/database/schema.%s.sql' % self.db_type)
		if self.run_script(schema_file, commit=False):
			self.execute('DELETE FROM version', quiet=True)
			self.execute('INSERT INTO version(db_version) VALUES(?)', [self.db_version], quiet=True)
			self.commit()
		self.disconnect()

DB = DBI(DB_FILE, quiet=True, connect=True, version=3)
