import sys
import subprocess
import re
import logging
import gi

from typing import Callable

from efibootmgr import Efibootmgr

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio


def btn_with_icon(icon):
	btn = Gtk.Button(hexpand=True)
	icon = Gio.ThemedIcon(name=icon)
	image = Gtk.Image.new_from_gicon(icon)
	btn.set_child(image)
	return btn


def yes_no_dialog(parent, primary, secondary, on_response):
	dialog = Gtk.MessageDialog(transient_for=parent, message_type=Gtk.MessageType.QUESTION,
							buttons=Gtk.ButtonsType.YES_NO, text=primary, secondary_text=secondary)
	area = dialog.get_message_area()
	child = area.get_first_child()
	while child:
		child.set_selectable(True)
		child = child.get_next_sibling()
	dialog.connect('response', on_response)
	dialog.show()
	return dialog


def error_dialog(transient_for: Gtk.Window, message: str, title: str, on_response):
	dialog = Gtk.MessageDialog(transient_for=transient_for, destroy_with_parent=True,
			message_type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.CLOSE,
			text=title, secondary_text=message, modal=True)
	area = dialog.get_message_area()
	child = area.get_first_child()
	while child:
		child.set_selectable(True)
		child = child.get_next_sibling()
	dialog.connect('response', on_response)
	dialog.show()
	return dialog


many_esps_error_message = """
This program detected more than one EFI System Partition on your system. You have to choose the right one.
You can either mount your ESP on /boot/efi or pass the ESP block device via --disk and --part
(e.g. --disk=/dev/sda --part=1).

Choose wisely.
"""


device_regex = re.compile(r'^([a-z/]+[0-9a-z]*?)p?([0-9]+)$')

def device_to_disk_part(device: str) -> tuple[str, str]:
	try:
		disk, part = device_regex.match(device).groups()
		logging.debug("Device path %s split into %s and %s", device, disk, part)
		return disk, part
	except AttributeError:
		raise ValueError("Could not match device " + device)


def make_auto_detect_esp_with_findmnt(esp_mount_point) -> Callable:
	def auto_detect_esp_with_findmnt() -> tuple[str, str] | None:
		# findmnt --noheadings --output SOURCE --mountpoint /boot/efi
		cmd = ["findmnt", "--noheadings", "--output", "SOURCE,FSTYPE", "--mountpoint", esp_mount_point]

		logging.debug("Running: %s", ' '.join(cmd))
		try:
			findmnt_output = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout
		except (FileNotFoundError, subprocess.CalledProcessError) as e:
			logging.warning("Could not detect ESP with findmnt: %s", e)
			return
		splitted = findmnt_output.strip().split()
		for source, fstype in zip(splitted[::2], splitted[1::2]):
			if fstype == 'vfat':
				disk, part = device_to_disk_part(source)
				return disk, part
	return auto_detect_esp_with_findmnt


def auto_detect_esp_with_lsblk() -> tuple[str, str] | None:
	"""
	Finds the ESP by scanning the partition table. It should work with GPT (tested) and MBR (not tested).
	This method doesn't require the ESP to be mounted.
	:return: 2 strings that can be passed to efibootmgr --disk and --part argument.
	"""
	esp_part_types = ('C12A7328-F81F-11D2-BA4B-00A0C93EC93B', 'EF')

	# lsblk --noheadings --pairs --paths --output NAME,PARTTYPE
	cmd = ['lsblk', '--noheadings', '--pairs', '--paths', '--output', 'NAME,PARTTYPE,FSTYPE']

	logging.debug("Running: %s", ' '.join(cmd))
	try:
		res = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout.strip()
	except (FileNotFoundError, subprocess.CalledProcessError) as e:
		logging.warning("Could not detect ESP with lsblk: %s", e)
		return
	regex = re.compile('^NAME="(.+)" PARTTYPE="(.+)" FSTYPE="(.+)"$', re.MULTILINE)
	esps = []
	for match in regex.finditer(res):
		name, part_type, fs_type = match.groups()
		if part_type.upper() in esp_part_types and fs_type == 'vfat':
			esps.append(name)
	if len(esps) == 1:
		source = esps[0]
		disk, part = device_to_disk_part(source)
	else:
		logging.warning(many_esps_error_message)
		error_dialog(None, f"{many_esps_error_message}\nDetected ESPs: {', '.join(esps)}",
					"More than one EFI System Partition detected!", lambda *_: sys.exit(-1))
		return None
	return disk, part


def auto_detect_esp(window):
	methods = (make_auto_detect_esp_with_findmnt('/efi'), make_auto_detect_esp_with_findmnt('/boot/efi'),
			   make_auto_detect_esp_with_findmnt('/boot'), auto_detect_esp_with_lsblk)
	for find_esp_method in methods:
		result = find_esp_method()
		if not result:
			continue
		disk, part = result
		logging.info("Detected ESP on disk %s part %s", disk, part)
		return disk, part
	logging.fatal("Can't auto-detect ESP! All methods failed.")
	return None, None


def execute_script_as_root(script):
	logging.info("Running command `pkexec sh -c %s`", script)
	subprocess.run(["pkexec", "sh", "-c", script], check=True, capture_output=True)


class EFIStore(Gtk.ListStore):
	ROW_CURRENT = 0
	ROW_NUM = 1
	ROW_NAME = 2
	ROW_PATH = 3
	ROW_PARAMETERS = 4
	ROW_ACTIVE = 5
	ROW_NEXT = 6

	def __init__(self, window):
		self.window = window
		Gtk.ListStore.__init__(self, bool, str, str, str, str, bool, bool)
		self._efibootmgr = None
		self.clear()

	@property
	def efibootmgr(self):
		if self._efibootmgr is None:
			self._efibootmgr = Efibootmgr.get_instance()
		return self._efibootmgr

	def reorder(self, **kwargs):
		reorder_logger = logging.getLogger("reorder")
		new_order = []

		for bootnum in self.boot_order:
			index = self.index_num(bootnum)
			if index is None:
				reorder_logger.warning('%s is in BootOrder, but it\'s not in the list', bootnum)
			else:
				new_order.append(index)

		for i, row in enumerate(self):
			if i not in new_order:
				reorder_logger.warning('%s is not in BootOrder, appending to the list', row[EFIStore.ROW_NUM])
				new_order.append(i)

		reorder_logger.debug("New order is: %s", new_order)

		assert(len(new_order) == len(self))
		super().reorder(new_order)

	def swap(self, a, b):
		super().swap(a, b)
		self.boot_order = [ x[EFIStore.ROW_NUM] for x in self ]

	def index_num(self, num):
		for i,row in enumerate(self):
			if row[EFIStore.ROW_NUM] == num:
				return i

	def clear(self):
		super().clear()
		self.boot_order = []
		self.boot_order_initial = []
		self.boot_next = None
		self.boot_next_initial = None
		self.boot_active = []
		self.boot_inactive = []
		self.boot_add = []
		self.boot_remove = []
		self.boot_current = None
		self.timeout = None
		self.timeout_initial = None

	def refresh(self, *args):
		self.clear()

		try:
			boot = self.efibootmgr.run()
		except (FileNotFoundError, subprocess.CalledProcessError) as e:
			logging.exception("Error running efibootmgr. Please check that it is correctly installed.")
			error_dialog(transient_for=self.window, title="efibootmgr utility not installed!",
						message=f"Please check that the efibootmgr utility is correctly installed, as this program requires its output.\n{str(e)}",
						on_response=lambda *_: sys.exit(-1))
			return
		except UnicodeDecodeError as e:
			logging.exception("Error decoding efibootmgr -v output.")
			error_dialog(transient_for=self.window, title="Error while decoding efibootmgr output.",
						message="Could not decode efiboomgr output.\n" + e, on_response=lambda *_: sys.exit(-2))
			return

		if boot is not None:
			parsed_efi = self.efibootmgr.parse(boot)
			for entry in parsed_efi['entries']:
				row = self.append()
				self.set_value(row, EFIStore.ROW_CURRENT, entry['num'] == parsed_efi['boot_current'])
				self.set_value(row, EFIStore.ROW_NUM, entry['num'])
				self.set_value(row, EFIStore.ROW_NAME, entry['name'])
				self.set_value(row, EFIStore.ROW_PATH, entry['path'])
				self.set_value(row, EFIStore.ROW_PARAMETERS, entry['parameters'])
				self.set_value(row, EFIStore.ROW_ACTIVE, entry['active'])
				self.set_value(row, EFIStore.ROW_NEXT, entry['num'] == parsed_efi['boot_next'])
			self.boot_order = self.boot_order_initial = parsed_efi['boot_order']
			self.boot_next = self.boot_next_initial = parsed_efi['boot_next']
			self.boot_current = parsed_efi['boot_current']
			self.timeout = self.timeout_initial = parsed_efi['timeout']
			self.window.timeout_spin.set_value(self.timeout)
			self.reorder()

	def change_boot_next(self, widget, path):
		selected_path = Gtk.TreePath(path)
		for row in self:
			if row.path == selected_path:
				row[EFIStore.ROW_NEXT] = not row[EFIStore.ROW_NEXT]
				self.boot_next = row[EFIStore.ROW_NUM] if row[EFIStore.ROW_NEXT] else None
			else:
				row[EFIStore.ROW_NEXT] = False

	def change_active(self, widget, path):
		selected_path = Gtk.TreePath(path)
		for row in self:
			if row.path == selected_path:
				row[EFIStore.ROW_ACTIVE] = not row[EFIStore.ROW_ACTIVE]
				num = row[EFIStore.ROW_NUM]
				if row[EFIStore.ROW_ACTIVE]:
					if num in self.boot_inactive:
						self.boot_inactive.remove(num)
					else:
						self.boot_active.append(num)
				else:
					if num in self.boot_active:
						self.boot_active.remove(num)
					else:
						self.boot_inactive.append(num)

	def change_timeout(self, timeout_spin):
		self.timeout = timeout_spin.get_value_as_int()

	def fill_row(self, row, current, num, name, path, parameters, active, next):
		self.set_value(row, EFIStore.ROW_CURRENT, current)
		self.set_value(row, EFIStore.ROW_NUM, num)
		self.set_value(row, EFIStore.ROW_NAME, name)
		self.set_value(row, EFIStore.ROW_PATH, path)
		self.set_value(row, EFIStore.ROW_PARAMETERS, parameters)
		self.set_value(row, EFIStore.ROW_ACTIVE, active)
		self.set_value(row, EFIStore.ROW_NEXT, next)

	def add(self, label, path, parameters):
		new_num = "NEW{:d}".format(len(self.boot_add))
		row = self.insert(0)
		self.fill_row(row, False, new_num, label, path, parameters, True, False)
		self.boot_add.append((new_num, label, path, parameters))

	def remove(self, row_index, row_iter):
		num = self.get_value(row_iter, EFIStore.ROW_NUM)
		if num.startswith('NEW'):
			self.boot_add = [entry for entry in self.boot_add if entry[0] != num]
		else:
			for row in self:
				if row[EFIStore.ROW_NUM] == num:
					self.boot_remove.append(num)
					self.boot_order.remove(num)
		super().remove(row_iter)

	def pending_changes(self):
		return (self.boot_next_initial != self.boot_next or
				self.boot_order_initial != self.boot_order or self.boot_add or
				self.boot_remove or self.boot_active or self.boot_inactive
				or self.timeout != self.timeout_initial
			)

	def to_script(self, disk, part):
		esp = f"--disk {disk} --part {part}"
		script = ''
		for entry in self.boot_remove:
			script += f'efibootmgr {esp} --delete-bootnum --bootnum {entry}\n'
		for _, label, loader, params in self.boot_add:
			script += f'efibootmgr {esp} --create --label \'{label}\' --loader \'{loader}\' --unicode \'{params}\'\n'
		if self.boot_order != self.boot_order_initial:
			script += f'efibootmgr {esp} --bootorder {",".join(self.boot_order)}\n'
		if self.boot_next_initial != self.boot_next:
			if self.boot_next is None:
				script += f'efibootmgr {esp} --delete-bootnext\n'
			else:
				script += f'efibootmgr {esp} --bootnext {self.boot_next}\n'
		for entry in self.boot_active:
			script += f'efibootmgr {esp} --bootnum {entry} --active\n'
		for entry in self.boot_inactive:
			script += f'efibootmgr {esp} --bootnum {entry} --inactive\n'
		if self.timeout != self.timeout_initial:
			script += f'efibootmgr {esp} --timeout {self.timeout}\n'
		return script


class EFIWindow(Gtk.ApplicationWindow):
	def __init__(self, app):
		Gtk.Window.__init__(self, title="EFI boot manager", application=app)

		vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_top=10, margin_start=10, margin_bottom=10, margin_end=10)
		self.set_child(vbox)

		self.store = EFIStore(self)
		self.tree = Gtk.TreeView(model=self.store, vexpand=True, has_tooltip=True)
		self.tree.connect('query-tooltip', self.on_query_tooltip)
		vbox.append(self.tree)

		renderer_text = Gtk.CellRendererText()
		renderer_check = Gtk.CellRendererToggle(radio=False)
		renderer_radio = Gtk.CellRendererToggle(radio=True)
		renderer_boot_current = Gtk.CellRendererToggle(radio=True, activatable=False)
		renderer_check.connect("toggled", self.store.change_active)
		renderer_radio.connect("toggled", self.store.change_boot_next)
		self.tree.append_column(Gtk.TreeViewColumn("BootCurrent", renderer_boot_current, active=0))
		self.tree.append_column(Gtk.TreeViewColumn("BootNum", renderer_text, text=1))
		self.tree.append_column(Gtk.TreeViewColumn("Name", renderer_text, text=2))
		self.tree.append_column(Gtk.TreeViewColumn("Path", renderer_text, text=3))
		self.tree.append_column(Gtk.TreeViewColumn("Parameters", Gtk.CellRendererText(ellipsize=True), text=4))
		self.tree.append_column(Gtk.TreeViewColumn("Active", renderer_check, active=5))
		self.tree.append_column(Gtk.TreeViewColumn("NextBoot", renderer_radio, active=6))

		hb = Gtk.HeaderBar()
		self.set_titlebar(hb)

		clear_btn = btn_with_icon("edit-clear-all-symbolic")
		clear_btn.set_tooltip_text("clear all")
		clear_btn.connect("clicked", self.on_clicked_discard_changes)
		hb.pack_end(clear_btn)

		write_btn = btn_with_icon("document-save-symbolic")
		write_btn.connect("clicked", self.apply_changes)
		write_btn.set_tooltip_text("save")
		hb.pack_end(write_btn)

		hbox = Gtk.Box(hexpand=True)
		hbox.add_css_class("linked")
		vbox.append(hbox)

		up = btn_with_icon("go-up-symbolic")
		down = btn_with_icon("go-down-symbolic")
		new = btn_with_icon("list-add-symbolic")
		delete = btn_with_icon("list-remove-symbolic")

		up.set_tooltip_text("move up")
		down.set_tooltip_text("move down")
		new.set_tooltip_text("create new entry")
		delete.set_tooltip_text("delete entry")

		hbox.append(up)
		hbox.append(down)
		hbox.append(new)
		hbox.append(delete)

		up.connect("clicked", self.up)
		down.connect("clicked", self.down)
		new.connect("clicked", self.new)
		delete.connect("clicked", self.delete)

		tbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
		tbox.append(Gtk.Label(label="Boot manager timeout in seconds:"))
		self.timeout_spin = Gtk.SpinButton.new_with_range(0, 999, 1)
		self.timeout_spin.connect('value_changed', self.store.change_timeout)
		tbox.append(self.timeout_spin)
		vbox.append(tbox)

		self.connect("close-request", self.on_close_request)
		self.set_default_size(300, 260)

	def query_system(self, disk, part):
		if not (disk and part):
			disk, part = auto_detect_esp(self)
		if not (disk and part):
			error_dialog(self, "Could not find an EFI System Partition. Ensure your ESP is mounted on /efi, "
								"/boot/efi or /boot, that it has the correct partition type and vfat file system and that "
								"either findmnt or lsblk commands are installed (should be by default on most distros).",
								"Can't auto-detect ESP!", lambda *_: sys.exit(-1))
			return
		self.disk, self.part = disk, part
		self.store.refresh()

	def on_query_tooltip(self, treeview, x, y, keyboard_mode, tooltip):
		if keyboard_mode:
			path, column = treeview.get_cursor()
			if not path:
				return False
		else:
			bin_x, bin_y = treeview.convert_widget_to_bin_window_coords(x, y)
			result = treeview.get_path_at_pos(bin_x, bin_y)
			if result is None:
				return False
			path, column, _, _ = result
		if column.get_title() == "Parameters":
			model_iter = treeview.get_model().get_iter(path)
			text = treeview.get_model().get(model_iter, EFIStore.ROW_PARAMETERS)[0]
			if text:
				tooltip.set_text(text)
				treeview.set_tooltip_cell(tooltip, path, column, None)
				return True
		return False

	def up(self, *args):
		_, selection = self.tree.get_selection().get_selected()
		if selection is not None:
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
		dialog = Gtk.MessageDialog(transient_for=self, modal=True,
				destroy_with_parent=True, message_type=Gtk.MessageType.QUESTION,
				buttons=Gtk.ButtonsType.OK_CANCEL, text="Label is mandatory. It is the name that will show up in your EFI boot menu.\n\n"
				"Path is the path to the loader relative to the ESP, like \\EFI\\Boot\\bootx64.efi\n\n"
				"Parameters is an optional list of aguments to pass to the loader (your kernel parameters if you use EFISTUB)")

		dialog.set_title("New EFI loader")
		yes_button = dialog.get_widget_for_response(Gtk.ResponseType.OK)
		yes_button.set_sensitive(False)
		dialog_box = dialog.get_content_area()

		fields = ["label", "path", "parameters"]
		entries = {}
		grid = Gtk.Grid(row_spacing=2, column_spacing=8, halign=Gtk.Align.CENTER)
		for i, field in enumerate(fields):
			entries[field] = Gtk.Entry()
			entries[field].set_size_request(400, 0)
			label = Gtk.Label(label=field.capitalize() + ":")
			grid.attach(label, 0, i, 1, 1)
			grid.attach(entries[field], 1, i, 1, 1)
		
		dialog_box.append(grid)
		entries["label"].connect('changed', lambda l: yes_button.set_sensitive(l.get_text() != ''))
		def on_response(dialog, response):
			label, path, parameters = map(lambda field: entries[field].get_text(), fields)
			if response == Gtk.ResponseType.OK:
				self.store.add(label, path, parameters)
			dialog.close()
		dialog.connect('response', on_response)
		dialog.show()

	def delete(self, *args):
		_, selection = self.tree.get_selection().get_selected()
		index = self.tree.get_selection().get_selected_rows()[1][0].get_indices()[0]
		if selection is not None:
			self.store.remove(index, selection)

	def apply_changes(self, *args):
		if self.store.pending_changes():
			script = self.store.to_script(self.disk, self.part)

			def on_response(dialog, response):
				if response == Gtk.ResponseType.YES:
					try:
						execute_script_as_root(script)
						self.store.refresh()
					except FileNotFoundError as e:
						error_dialog(self, "The pkexec command from PolKit is "
							"required to execute commands with elevated privileges.\n"
							f"{e}", "pkexec not found", lambda d, r: d.close())
					except subprocess.CalledProcessError as e:
						error_dialog(self, f"{e}\n{e.stderr.decode()}", "Error", lambda d, r: d.close())
				dialog.close()
			dialog = yes_no_dialog(self, "Are you sure you want to continue?",
							"Your changes are about to be written to EFI NVRAM.\n"
							"The following commands will be run:\n"	+ script,
							on_response)

	def discard_warning(self, on_response, win):
		if self.store.pending_changes():
			return yes_no_dialog(self, "Are you sure you want to discard?",
									"Your changes will be lost if you don't save them.",
									on_response)
		else:
			return None

	def on_clicked_discard_changes(self, button):
		def on_response(dialog, response):
			if response == Gtk.ResponseType.YES:
				self.store.refresh()
			dialog.close()
		if not self.discard_warning(on_response, self):
			self.store.refresh()

	def on_close_request(self, win):
		def on_response(dialog, response):
			dialog.close()
			if response == Gtk.ResponseType.YES:
				win.destroy()
		if self.discard_warning(on_response, win):
			return True


def run(disk, part):
	def on_activate(app):
		win = EFIWindow(app)
		win.query_system(disk, part)
		win.show()

	app = Gtk.Application()
	app.connect('activate', on_activate)
	app.run()
