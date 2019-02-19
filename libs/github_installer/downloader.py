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
import xbmcgui
import zipfile
import requests
from commoncore import kodi
from commoncore.core import format_size
from libs.github import get_version_by_name, get_version_by_xml

class downloaderException(Exception):
	pass

def format_status(cached, total, speed):
	cached = format_size(cached)
	total = format_size(total)
	speed = format_size(speed, 'B/s')
	return 	"%s of %s at %s" % (cached, total, speed) 

def test_url(url):
	r = requests.head(url)
	return r.status_code == requests.codes.ok

def download(url, addon_id, destination, unzip=False, quiet=False):
	version = None
	filename = addon_id + '.zip'
	r = requests.get(url, stream=True)
	kodi.log("Download: %s" % url)
	
	
	
	if r.status_code == requests.codes.ok:
		temp_file = kodi.vfs.join(kodi.get_profile(), "downloads")
		if not kodi.vfs.exists(temp_file): kodi.vfs.mkdir(temp_file, recursive=True)
		temp_file = kodi.vfs.join(temp_file, filename)
		try:
			total_bytes = int(r.headers["Content-Length"])
		except:
			total_bytes = 0
		block_size = 1000
		cached_bytes = 0
		if not quiet:
			pb = xbmcgui.DialogProgress()
			pb.create("Downloading",filename,' ', ' ')
		kodi.sleep(150)
		start = time.time()
		with open(temp_file, 'wb') as f:
			for block in r.iter_content(chunk_size=block_size):
				if not block: break
				if not quiet and pb.iscanceled():
					raise downloaderException('Download Aborted')
					return False
				cached_bytes += len(block)
				f.write(block)
				if total_bytes > 0:
					delta = int(time.time() - start)
					if delta:
						bs = int(cached_bytes / (delta))
					else: bs = 0
					if not quiet:
						percent = int(cached_bytes * 100 / total_bytes)
						pb.update(percent, "Downloading",filename, format_status(cached_bytes, total_bytes, bs))
		
		if not quiet: pb.close()
		if unzip:
			zip_ref = zipfile.ZipFile(temp_file, 'r')
			zip_ref.extractall(destination)
			zip_ref.close()
			kodi.vfs.rm(temp_file, quiet=True)
			try:
				xml = kodi.vfs.read_file(kodi.vfs.join(destination, kodi.vfs.join(addon_id, 'addon.xml')), soup=True)
				version = get_version_by_xml(xml)
				if not version:
					version = get_version_by_name(filename)
			except:
				kodi.log("Unable to fine version from addon.xml for addon: %s" % addon_id)
		else:
			kodi.vfs.mv(temp_file, kodi.vfs.join(destination, filename))
	else:
		kodi.close_busy_dialog()
		raise downloaderException(r.status_code)
	return version
	
