#!/usr/bin/env python3

import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio
import subprocess
import re

def find_esp():
	# findmnt --noheadings --output SOURCE --target /boot/efi
	try:
		res = subprocess.check_output(["findmnt", "--noheadings", "--output", "SOURCE", "--target", "/boot/efi"]).decode('UTF-8').strip()
	except subprocess.CalledProcessError as e:
		print("Please mount ESP to /boot/efi", sep='\n', file=sys.stderr)
		sys.exit()
	return res[:-1], res[-1:]

ESP_DISK, ESP_PART = find_esp()
ESP = ("--disk", ESP_DISK, "--part", ESP_PART)

def efibootmgr_set_boot_next(num):
	if num is None:
		cmd = ["pkexec", "efibootmgr", *ESP, "--delete-bootnext"]
	else:
		cmd = ["pkexec", "efibootmgr", *ESP, "--bootnext", num]
	print(*cmd)
	return subprocess.check_output(cmd)

def efibootmgr_set_boot_order(order):
	cmd = ["pkexec", "efibootmgr", *ESP, "--bootorder", ','.join(order)]
	print(*cmd)
	return subprocess.check_output(cmd)

def efibootmgr_remove(num):
	cmd = ["pkexec", "efibootmgr", *ESP, "--delete-bootnum", "--bootnum", num]
	print(*cmd)
	return subprocess.check_output(cmd)

def efibootmgr_add(label, loader):
	cmd = ["pkexec", "efibootmgr", *ESP, "--create", "--label", label, "--loader", loader]
	print(*cmd)
	return subprocess.check_output(cmd)

def efibootmgr_active(num):
	cmd = ["pkexec", "efibootmgr", *ESP, "--bootnum", num, "--active"]
	print(*cmd)
	return subprocess.check_output(cmd)

def efibootmgr_inactive(num):
	cmd = ["pkexec", "efibootmgr", *ESP, "--bootnum", num, "--inactive"]
	print(*cmd)
	return subprocess.check_output(cmd)

def get_efibootmgr():
	try:
		return subprocess.check_output([ "efibootmgr", "-v" ]).decode('UTF-8').strip().split('\n')
	except subprocess.CalledProcessError as e:
		print(e, file=sys.stderr)

def btn_with_icon(icon):
	btn = Gtk.Button()
	icon = Gio.ThemedIcon(name=icon)
	image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
	btn.add(image)
	return btn

def yes_no_dialog(parent, primary, secondary):
	dialog = Gtk.MessageDialog(parent, 0, Gtk.MessageType.QUESTION, Gtk.ButtonsType.YES_NO, primary)
	dialog.format_secondary_text(secondary)
	response = dialog.run()
	dialog.destroy()
	return response

def entry_dialog(parent, message, title=''):
	dialogWindow = Gtk.MessageDialog(parent, Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.QUESTION, Gtk.ButtonsType.OK_CANCEL, message)

	dialogWindow.set_title(title)

	dialogBox = dialogWindow.get_content_area()
	userEntry = Gtk.Entry()
	userEntry.set_size_request(250,0)
	dialogBox.pack_end(userEntry, False, False, 0)

	dialogWindow.show_all()
	response = dialogWindow.run()
	text = userEntry.get_text() 
	dialogWindow.destroy()
	if (response == Gtk.ResponseType.OK) and (text != ''):
		return text

def info_dialog(parent, message, title):
	dialogWindow = Gtk.MessageDialog(parent, Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, message)
	dialogWindow.set_title(title)
	dialogWindow.show_all()
	dialogWindow.run()
	dialogWindow.destroy()


class EFIStore(Gtk.ListStore):
	def __init__(self):
		Gtk.ListStore.__init__(self, str, str, str, bool, bool)
		self.regex = re.compile("^Boot([0-9A-F]+)(\*)? (.+)\t(?:.+File\((.+)\))?.*$")
		self.refresh()

	def reorder(self):
		if self.boot_order:
			super().reorder([ self.index_num(v) for v in self.boot_order ])

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

		boot = get_efibootmgr()
		if boot is not None:
			for line in boot:
				match = self.regex.match(line)
				if match and match.group(1) and match.group(3):
					num, active, name, loader = match.groups()
					self.append([num, name, loader, active is not None, num == self.boot_next])
				elif line.startswith("BootOrder"):
					self.boot_order = self.boot_order_initial = line.split(':')[1].strip().split(',')
				elif line.startswith("BootNext"):
					self.boot_next = self.boot_next_initial = line.split(':')[1].strip()
			self.reorder()

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
			for entry in self.boot_remove:
				efibootmgr_remove(entry)
			for entry in self.boot_add:
				efibootmgr_add(*entry)
			if self.boot_order != self.boot_order_initial:
				efibootmgr_set_boot_order(self.boot_order)
			if self.boot_next_initial != self.boot_next:
				efibootmgr_set_boot_next(self.boot_next)
			for entry in self.boot_active:
				efibootmgr_active(entry)
			for entry in self.boot_inactive:
				efibootmgr_inactive(entry)
		except subprocess.CalledProcessError as e:
			print(e, file=sys.stderr)
		self.refresh()

	def pending_changes(self):
		return (self.boot_next_initial != self.boot_next or
				self.boot_order_initial != self.boot_order or self.boot_add or
				self.boot_remove or self.boot_active or self.boot_inactive)


class EFIWindow(Gtk.Window):
	def __init__(self):
		Gtk.Window.__init__(self, title="EFI boot manager")
		self.set_border_width(10)

		vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
		self.add(vbox)

		self.store = EFIStore()
		self.tree = Gtk.TreeView(self.store)
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

		hb = Gtk.HeaderBar()
		hb.set_show_close_button(True)
		hb.props.title = "EFI boot manager"
		self.set_titlebar(hb)

		clear_btn = btn_with_icon("edit-clear-all-symbolic")
		clear_btn.connect("button-press-event", self.discard_changes)
		hb.pack_end(clear_btn)

		write_btn = btn_with_icon("document-save-symbolic")
		write_btn.connect("button-press-event", self.apply_changes)
		hb.pack_end(write_btn)

		hbox = Gtk.HButtonBox()
		hbox.set_layout(Gtk.ButtonBoxStyle.EXPAND)
		vbox.add(hbox)
		up = btn_with_icon("go-up-symbolic")
		down = btn_with_icon("go-down-symbolic")
		new = btn_with_icon("list-add-symbolic")
		delete = btn_with_icon("list-remove-symbolic")
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
			response = yes_no_dialog(self, "Are you sure you want to continue?", "Your changes are about to be written to EFI's NVRAM.")
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


win = EFIWindow()
win.show_all()
Gtk.main()

