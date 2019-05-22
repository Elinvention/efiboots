#!/usr/bin/env python3

import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio
import subprocess
import re
import logging


def find_esp():
	custom_efi = [ arg.split("--efi=")[1] for arg in sys.argv[1:] if arg.startswith("--efi=") ]
	if len(custom_efi) > 0:
		res = custom_efi[0]
	else:
		# findmnt --noheadings --output SOURCE --target /boot/efi
		cmd = ["findmnt", "--noheadings", "--output", "SOURCE", "--target", "/boot/efi"]
		print(*cmd)
		try:
			res = subprocess.check_output(cmd).decode('UTF-8').strip()
		except subprocess.CalledProcessError:
			print("Please mount ESP to /boot/efi", sep='\n', file=sys.stderr)
			return
	print(res)
	return res[:-1], res[-1:]


esp = "--disk %s --part %s" % find_esp()


def run_efibootmgr():
	try:
		output = subprocess.check_output([ "efibootmgr", "-v" ]).decode('UTF-8').strip().split('\n')
		logging.debug(repr(output))
		return output
	except subprocess.CalledProcessError as e:
		print(e, file=sys.stderr)

def btn_with_icon(icon):
	btn = Gtk.Button()
	icon = Gio.ThemedIcon(name=icon)
	image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
	btn.add(image)
	return btn

def yes_no_dialog(parent, primary, secondary):
	dialog = Gtk.MessageDialog(parent=parent, flags=0, message_type=Gtk.MessageType.QUESTION,
							buttons=Gtk.ButtonsType.YES_NO, text=primary)
	dialog.format_secondary_text(secondary)
	response = dialog.run()
	dialog.destroy()
	return response

def entry_dialog(parent, message, title=''):
	dialog = Gtk.MessageDialog(parent,
			Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
			Gtk.MessageType.QUESTION, Gtk.ButtonsType.OK_CANCEL, message)

	dialog.set_title(title)

	dialogBox = dialog.get_content_area()
	userEntry = Gtk.Entry()
	userEntry.set_size_request(250,0)
	dialogBox.pack_end(userEntry, False, False, 0)

	dialog.show_all()
	response = dialog.run()
	text = userEntry.get_text() 
	dialog.destroy()
	if (response == Gtk.ResponseType.OK) and (text != ''):
		return text

def info_dialog(parent, message, title):
	dialog = Gtk.MessageDialog(parent, Gtk.DialogFlags.DESTROY_WITH_PARENT,
			Gtk.MessageType.INFO, Gtk.ButtonsType.OK, message)
	dialog.set_title(title)
	dialog.show_all()
	dialog.run()
	dialog.destroy()

def error_dialog(parent, message, title):
	dialog = Gtk.MessageDialog(parent=parent, flags=Gtk.DialogFlags.DESTROY_WITH_PARENT,
			message_type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.CANCEL, text=title)
	area = dialog.get_message_area()
	for child in area.get_children():
		child.set_selectable(True)
	dialog.format_secondary_text(message)
	dialog.show_all()
	dialog.run()
	dialog.destroy()


class EFIStore(Gtk.ListStore):
	def __init__(self, window):
		self.window = window
		Gtk.ListStore.__init__(self, str, str, str, bool, bool)
		self.regex = re.compile("^Boot([0-9A-F]+)(\*)? (.+)\t(?:.+File\((.+)\))?.*$")
		self.refresh()

	def reorder(self):
		reorder_logger = logging.getLogger("reorder")
		new_order = []

		for bootnum in self.boot_order:
			index = self.index_num(bootnum)
			if index is None:
				reorder_logger.warning('%s is in BootOrder, but it\'s not in the list', bootnum)
			else:
				new_order.append(index)

		for i,row in enumerate(self):
			if i not in new_order:
				reorder_logger.warning('%s is not in BootOrder, appending to the list', row[0])
				new_order.append(i)

		reorder_logger.debug("New order is: %s", new_order)

		assert(len(new_order) == len(self))
		super().reorder(new_order)

	def swap(self, a, b):
		super().swap(a, b)
		self.boot_order = [ x[0] for x in self ]

	def index_num(self, num):
		for i,row in enumerate(self):
			if row[0] == num:
				return i

	def refresh(self, *args):
		self.clear()
		self.boot_order = []
		self.boot_order_initial = []
		self.boot_next = None
		self.boot_next_initial = None
		self.boot_active = []
		self.boot_inactive = []
		self.boot_add = []
		self.boot_remove = []

		parser_logger = logging.getLogger("parser")
		boot = run_efibootmgr()
		if boot is not None:
			for line in boot:
				match = self.regex.match(line)
				if match and match.group(1) and match.group(3):
					num, active, name, loader = match.groups()
					parsed = [num, name, loader, active is not None, num == self.boot_next]
					self.append(parsed)
					parser_logger.debug("Entry: %s", parsed)
				elif line.startswith("BootOrder"):
					self.boot_order = self.boot_order_initial = line.split(':')[1].strip().split(',')
					parser_logger.debug("BootOrder: %s", self.boot_order)
				elif line.startswith("BootNext"):
					self.boot_next = self.boot_next_initial = line.split(':')[1].strip()
					parser_logger.debug("BootNext: %s", self.boot_next)
				else:
					parser_logger.warning("line didn't match: %s", repr(line))
			self.reorder()
		else:
			error_dialog(self.window, "Please verify that efibootmgr is installed", "Error")
			sys.exit(-1)

	def change_boot_next(self, widget, path):
		selected_path = Gtk.TreePath(path)
		for row in self:
			if row.path == selected_path:
				row[4] = not row[4]
				self.boot_next = row[0] if row[4] else None
			else:
				row[4] = False

	def change_active(self, widget, path):
		selected_path = Gtk.TreePath(path)
		for row in self:
			if row.path == selected_path:
				row[3] = not row[3]
				num = row[0]
				if row[3]:
					if num in self.boot_inactive:
						self.boot_inactive.remove(num)
					else:
						self.boot_active.append(num)
				else:
					if num in self.boot_active:
						self.boot_active.remove(num)
					else:
						self.boot_inactive.append(num)

	def add(self, label, loader):
		self.insert(0, ["NEW*", label, loader, True, False])
		self.boot_add.append((label, loader))

	def remove(self, row_iter):
		num = self.get_value(row_iter, 0)
		for row in self:
			if row[0] == num:
				self.boot_remove.append(num)
				self.boot_order.remove(num)
		super().remove(row_iter)

	def apply_changes(self):
		try:
			subprocess.check_output(["pkexec", "sh", "-c", str(self)])
		except subprocess.CalledProcessError as e:
			error_dialog(self.window, str(e), "Error")
		self.refresh()

	def pending_changes(self):
		return (self.boot_next_initial != self.boot_next or
				self.boot_order_initial != self.boot_order or self.boot_add or
				self.boot_remove or self.boot_active or self.boot_inactive)

	def __str__(self):
		str = ''
		for entry in self.boot_remove:
			str += f'efibootmgr {esp} --delete-bootnum --bootnum {entry}\n'
		for label, loader in self.boot_add:
			str += f'efibootmgr {esp} --create --label {label} --loader {loader}\n'
		if self.boot_order != self.boot_order_initial:
			str += f'efibootmgr {esp} --bootorder {",".join(self.boot_order)}\n'
		if self.boot_next_initial != self.boot_next:
			if self.boot_next is None:
				str += f'efibootmgr {esp} --delete-bootnext\n'
			else:
				str += f'efibootmgr {esp} --bootnext {self.boot_next}\n'
		for entry in self.boot_active:
			str += f'efibootmgr {esp} --bootnum {entry} --active\n'
		for entry in self.boot_inactive:
			str += f'efibootmgr {esp} --bootnum {entry} --inactive\n'
		return str


class EFIWindow(Gtk.Window):
	def __init__(self):
		Gtk.Window.__init__(self, title="EFI boot manager")
		self.set_border_width(10)

		vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
		self.add(vbox)

		self.store = EFIStore(self)
		self.tree = Gtk.TreeView(model=self.store, vexpand=True)
		vbox.add(self.tree)

		renderer_text = Gtk.CellRendererText()
		renderer_check = Gtk.CellRendererToggle(radio=False)
		renderer_radio = Gtk.CellRendererToggle(radio=True)
		renderer_check.connect("toggled", self.store.change_active)
		renderer_radio.connect("toggled", self.store.change_boot_next)
		self.tree.append_column(Gtk.TreeViewColumn("BootNum", renderer_text, text=0))
		self.tree.append_column(Gtk.TreeViewColumn("Name", renderer_text, text=1))
		self.tree.append_column(Gtk.TreeViewColumn("Loader", renderer_text, text=2))
		self.tree.append_column(Gtk.TreeViewColumn("Active", renderer_check, active=3))
		self.tree.append_column(Gtk.TreeViewColumn("NextBoot", renderer_radio, active=4))
		for column in self.tree.get_columns():
			column.set_resizable(True)
			column.set_min_width(75)

		hb = Gtk.HeaderBar()
		hb.set_show_close_button(True)
		hb.props.title = "EFI boot manager"
		self.set_titlebar(hb)

		clear_btn = btn_with_icon("edit-clear-all-symbolic")
		clear_btn.set_tooltip_text("clear all")
		clear_btn.connect("button-press-event", self.discard_changes)
		hb.pack_end(clear_btn)

		write_btn = btn_with_icon("document-save-symbolic")
		write_btn.connect("button-press-event", self.apply_changes)
		write_btn.set_tooltip_text("save")
		hb.pack_end(write_btn)

		hbox = Gtk.HButtonBox()
		hbox.set_layout(Gtk.ButtonBoxStyle.EXPAND)
		vbox.add(hbox)

		up = btn_with_icon("go-up-symbolic")
		down = btn_with_icon("go-down-symbolic")
		new = btn_with_icon("list-add-symbolic")
		delete = btn_with_icon("list-remove-symbolic")

		up.set_tooltip_text("move up")
		down.set_tooltip_text("move down")
		new.set_tooltip_text("create new entry")
		delete.set_tooltip_text("delete entry")

		hbox.add(up)
		hbox.add(down)
		hbox.add(new)
		hbox.add(delete)

		up.connect("button-press-event", self.up)
		down.connect("button-press-event", self.down)
		new.connect("button-press-event", self.new)
		delete.connect("button-press-event", self.delete)

		self.connect("delete-event", self.quit)
		self.set_default_size(300, 260)

	def up(self, *args):
		_, selection = self.tree.get_selection().get_selected()
		if not selection == None:
			next = self.store.iter_previous(selection)
			if next:
				self.store.swap(selection, next)

	def down(self, *args):
		_, selection = self.tree.get_selection().get_selected()
		if selection is not None:
			next = self.store.iter_next(selection)
			if next:
				self.store.swap(selection, next)

	def new(self, *args):
		label = entry_dialog(self, "Label:", "Enter Label of this new EFI entry")
		if label is not None:
			loader = entry_dialog(self, "Loader:", "Enter Loader of this new EFI entry")
			self.store.add(label, loader)

	def delete(self, *args):
		_, selection = self.tree.get_selection().get_selected()
		if selection is not None:
			self.store.remove(selection)

	def apply_changes(self, *args):
		if self.store.pending_changes():
			response = yes_no_dialog(self, "Are you sure you want to continue?",
							"Your changes are about to be written to EFI NVRAM.\nThe following commands will be run:\n" + str(self.store))
			if response == Gtk.ResponseType.YES:
				self.store.apply_changes()

	def discard_warning(self):
		if self.store.pending_changes():
			response = yes_no_dialog(self, "Are you sure you want to discard?", "Your changes will be lost if you don't save them.")
			return response == Gtk.ResponseType.YES
		else:
			return True

	def discard_changes(self, *args):
		if self.discard_warning():
			self.store.refresh()

	def quit(self, *args):
		if not self.discard_warning():
			return True
		else:
			Gtk.main_quit()


def main():
	win = EFIWindow()
	win.show_all()
	Gtk.main()



if __name__ == '__main__':
	logging.basicConfig(level=0)
	main()

