# -*- Mode: python; coding: utf-8; tab-width: 8; indent-tabs-mode: t; -*-
#
# Copyrigh © 2014 Laurent Vivier <laurent@vivier.eu>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301, USA.

import sys
import urllib.parse
import acoustid

import rb
from gi.repository import RB
from gi.repository import GObject, Gtk, Gio, Peas, PeasGtk

import gettext
gettext.install('rhythmbox', RB.locale_dir())

API_KEY = 'YICdhiH5'

class SongID(GObject.GObject, Peas.Activatable):
	__gtype_name__ = 'SongID'
	object = GObject.property(type=GObject.GObject)

	def __init__(self):
		GObject.GObject.__init__(self)

	def do_activate(self):
		shell = self.object
		self.__db = shell.props.db

		# add a "Update Artist/Title" in "Edit" menu

		self.__action = Gio.SimpleAction(name="songid-update-song")
		self.__action.connect("activate", self.update_song_cb)

		app = Gio.Application.get_default()
		app.add_action(self.__action)

		item = Gio.MenuItem()
		item.set_label(_("Update Artist/Title"))
		item.set_detailed_action('app.songid-update-song')

		app.add_plugin_menu_item('edit', 'songid-update-song', item)
		app.add_plugin_menu_item('browser-popup', 'songid-update-song',
					 item)

	def do_deactivate(self):
		shell = self.object
		app = Gio.Application.get_default()
		app.remove_action('songid-update-song')
		app.remove_plugin_menu_item('edit', 'songid-update-song')
		app.remove_plugin_menu_item('browser-popup',
					     'songid-update-song')
		del self.__action

	def update_song_cb(self, action, parameter):
		shell = self.object
		page = shell.props.selected_page
		if not hasattr(page, "get_entry_view"):
			return

		entries = page.get_entry_view().get_selected_entries()
		for entry in entries:
			uri = entry.get_playback_uri()
			uri_path = urllib.parse.urlparse(uri).path
			path = urllib.parse.unquote(uri_path)
			results = acoustid.match(API_KEY, path.encode('utf-8'))

			artist_score = { }
			title_score = { }
			max_title = 0.0
			max_artist = 0.0
			for score, rid, title, artist in results:
				if artist == None:
					continue
				if title == None:
					continue
				if artist in artist_score:
					artist_score[artist] = artist_score[artist] + score
				else:
					artist_score[artist] = score
				if artist_score[artist] > max_artist:
					max_artist = artist_score[artist]
				if title in title_score:
					title_score[title] = title_score[title] + score
				else:
					title_score[title] = score
				if title_score[title] > max_title:
					max_title = title_score[title]

			for artist in artist_score:
				if artist_score[artist] == max_artist:
					self.__db.entry_set(entry, RB.RhythmDBPropType.ARTIST,
							    str(artist))
					break
			for title in title_score:
				if title_score[title] == max_title:
					self.__db.entry_set(entry, RB.RhythmDBPropType.TITLE,
							    str(title))
					break
		self.__db.commit() 
