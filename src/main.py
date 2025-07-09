# main.py
#
# Copyright 2025 Elia Argentieri
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later


import logging
import gi
import sys

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio, GLib


class EfibootsApplication(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            application_id="ovh.elinvention.Efiboots",
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
            resource_base_path="/ovh/elinvention/Efiboots",
            **kwargs
        )
        self.window = None

        self.add_main_option(
            "disk",
            ord("d"),
            GLib.OptionFlags.NONE,
            GLib.OptionArg.STRING,
            "Disk device where ESP is located (for example /dev/sda)",
            None,
        )
        self.add_main_option(
            "part",
            ord("p"),
            GLib.OptionFlags.NONE,
            GLib.OptionArg.STRING,
            "Partition number of ESP (for example if ESP is on /dev/sda1 you should set this to 1)",
            None,
        )

        self.disk = ""
        self.part = ""

    def resource_path(self, relpath):
        base_path = self.get_resource_base_path()
        return base_path + '/' + relpath

    def do_startup(self):
        logging.debug("do startup")
        Gtk.Application.do_startup(self)

        action = Gio.SimpleAction.new("quit", None)
        action.connect("activate", self.on_quit)
        self.add_action(action)

        logging.debug("resource base path: %s", self.get_resource_base_path())
        menus_builder = Gtk.Builder.new_from_resource(self.resource_path("gtk/menus.ui"))

        logging.debug("app-menu: %s", self.get_menu_by_id("app-menu"))
        self.set_menubar(menus_builder.get_object("app-menu"))

    def do_activate(self):
        # We only allow a single window and raise any existing ones
        if not self.window:
            # Windows are associated with the application
            # when the last one is closed the application shuts down
            from efiboots.window import EfibootsMainWindow
            self.window = EfibootsMainWindow(application=self)

        self.window.query_system(self.disk, self.part)
        self.window.present()

    def do_command_line(self, command_line):
        options = command_line.get_options_dict()
        # convert GVariantDict -> GVariant -> dict
        options = options.end().unpack()

        if "disk" in options:
            self.disk = options["disk"]
            logging.debug("Found disk from command line: %s", self.disk)
        if "part" in options:
            self.part = options["part"]
            logging.debug("Found part from command line: %s", self.part)

        self.activate()
        return 0

    def on_quit(self, action, param):
        self.quit()


def main(version):
    logging.basicConfig(level=logging.DEBUG)
    app = EfibootsApplication()
    app.run(sys.argv)

if __name__ == "__main__":
    main("")

