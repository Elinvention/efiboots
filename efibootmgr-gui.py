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

def efibootmgr_set_boot_next(bootnum):
	if bootnum is None:
		cmd = ["pkexec", "efibootmgr", *ESP, "--delete-bootnext"]
	else:
		cmd = ["pkexec", "efibootmgr", *ESP, "--bootnext", str(bootnum)]
	print(*cmd)
	return subprocess.check_output(cmd)

def efibootmgr_set_boot_order(order):
	cmd = ["pkexec", "efibootmgr", *ESP, "--bootorder", ','.join(map('{0:04d}'.format, order))]
	print(*cmd)
	return subprocess.check_output(cmd)

def efibootmgr_remove(num):
	cmd = ["pkexec", "efibootmgr", *ESP, "--delete-bootnum", "--bootnum", '{0:04d}'.format(num)]
	print(*cmd)
	return subprocess.check_output(cmd)

def efibootmgr_add(label, loader):
	cmd = ["pkexec", "efibootmgr", *ESP, "--create", "--label", label, "--loader", loader]
	print(*cmd)
	return subprocess.check_output(cmd)

def get_efibootmgr():
	try:
		return subprocess.check_output("efibootmgr").decode('UTF-8').strip().split('\n')
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


class EFIStore(Gtk.ListStore):
	def __init__(self):
		Gtk.ListStore.__init__(self, str, str, bool)
		self.regex = re.compile("^Boot([0-9]+)\*? (.+)$")
		self.refresh()

	def reorder(self):
		if self.boot_order:
			super().reorder([ self.index_num(v) for v in self.boot_order ])

	def swap(self, a, b):
		super().swap(a, b)
		self.boot_order = [ int(x[0]) for x in self ]
		self.boot_order_changed = True

	def index_num(self, num):
		for i,row in enumerate(self):
			if int(row[0]) == num:
				return i

	def refresh(self, *args):
		self.clear()
		self.boot_order = []
		self.boot_order_changed = False
		self.boot_next = None
		self.boot_next_changed = False
		self.boot_add = []
		self.boot_remove = []

		boot = get_efibootmgr()
		if boot is not None:
			for line in boot:
				match = self.regex.match(line)
				if match and match.group(1) and match.group(2):
					num, name = match.group(1), match.group(2)
					self.append([num, name, int(num) == self.boot_next])
				elif line.startswith("BootOrder"):
					self.boot_order = list(map(int, line.split(':')[1].strip().split(',')))
				elif line.startswith("BootNext"):
					self.boot_next = int(line.split(':')[1].strip())
			self.reorder()

	def change_boot_next(self, widget, path):
		selected_path = Gtk.TreePath(path)
		for row in self:
			if row.path == selected_path:
				row[2] = not row[2]
				self.boot_next = int(row[0]) if row[2] else None
				self.boot_next_changed = True
			else:
				row[2] = False

	def add(self, label, loader):
		self.insert(0, ["NEW*", label, False])
		self.boot_add.append((label, loader))

	def remove(self, row_iter):
		num = int(self.get_value(row_iter, 0))
		for row in self:
			if int(row[0]) == num:
				self.boot_remove.append(num)
				self.boot_order.remove(num)
		super().remove(row_iter)

	def apply(self):
		try:
			for entry in self.boot_remove:
				efibootmgr_remove(entry)
			for entry in self.boot_add:
				efibootmgr_add(*entry)
			if self.boot_order_changed:
				efibootmgr_set_boot_order(self.boot_order)
			if self.boot_next_changed:
				efibootmgr_set_boot_next(self.boot_next)
		except subprocess.CalledProcessError as e:
			print(e, file=sys.stderr)
		self.refresh()

	def pending(self):
		return self.boot_next_changed or self.boot_order_changed or self.boot_add or self.boot_remove


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
		renderer_radio = Gtk.CellRendererToggle(radio=True)
		renderer_radio.connect("toggled", self.store.change_boot_next)
		column1 = Gtk.TreeViewColumn("BootNum", renderer_text, text=0)
		column2 = Gtk.TreeViewColumn("Name", renderer_text, text=1)
		column3 = Gtk.TreeViewColumn("NextBoot", renderer_radio, active=2)
		self.tree.append_column(column1)
		self.tree.append_column(column2)
		self.tree.append_column(column3)

		hb = Gtk.HeaderBar()
		hb.set_show_close_button(True)
		hb.props.title = "EFI boot manager"
		self.set_titlebar(hb)

		clear_btn = btn_with_icon("edit-clear-all-symbolic")
		clear_btn.connect("button-press-event", self.store.refresh)
		hb.pack_end(clear_btn)

		write_btn = btn_with_icon("document-save-symbolic")
		write_btn.connect("button-press-event", self.apply)
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

	def apply(self, *args):
		response = yes_no_dialog(self, "Are you sure you want to continue?", "Your changes are about to be written to EFI's NVRAM.")
		if response == Gtk.ResponseType.YES:
			self.store.apply()

	def quit(self, *args):
		if self.store.pending():
			response = yes_no_dialog(self, "Are you sure you want to disacrd?", "Your changes will be lost if you don't save them.")
			if response != Gtk.ResponseType.YES:
				return True
		Gtk.main_quit()


win = EFIWindow()
win.show_all()
Gtk.main()

