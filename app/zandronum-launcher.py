#!/usr/bin/env python

import gi, sys, os, configparser, subprocess, shlex
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio, GObject, Gdk

# IWAD filenames/descriptions/mod files
doom_iwads = {
	"doom.wad": {
		"name": "The Ultimate Doom",
		"patch": "",
		"mods": ["hud-stuff.pk3", "zdoom-1.pk3", "zdoom-2.pk3", "jfo-udoom.pk3"]
	},
	"doom2.wad": {
		"name": "Doom II: Hell on Earth",
		"patch": "",
		"mods": ["hud-stuff.pk3", "zdoom-1.pk3", "zdoom-2.pk3", "zdoom-doom2.pk3", "jfo-doom2.pk3"]
	},
	"plutonia.wad": {
		"name": "Final Doom - The Plutonia Experiment",
		"patch": "",
		"mods": ["hud-stuff.pk3", "zdoom-1.pk3", "zdoom-2.pk3", "zdoom-doom2.pk3", "zdoom-plut.pk3", "jfo-plut.pk3"]
	},
	"tnt.wad": {
		"name": "Final Doom - TNT: Evilution",
		"patch": "tnt31-patch.wad",
		"mods": ["hud-stuff.pk3", "zdoom-1.pk3", "zdoom-2.pk3", "zdoom-doom2.pk3", "zdoom-tnt.pk3", "jfo-tnt.pk3"]
	},
	"freedoom1.wad": {
		"name": "Freedoom Phase 1",
		"patch": "",
		"mods": []
	},
	"freedoom2.wad": {
		"name": "Freedoom Phase 2",
		"patch": "",
		"mods": []
	}
}

ui_dir = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), "ui")

@Gtk.Template(filename=os.path.join(ui_dir, "filedialogbutton.ui"))
class FileDialogButton(Gtk.Box):
	__gtype_name__ = "FileDialogButton"

	# Button properties
	icon_name = GObject.Property(type=str, default="", flags=GObject.ParamFlags.READWRITE)
	folder_select = GObject.Property(type=bool, default=False, flags=GObject.ParamFlags.READWRITE)
	can_clear = GObject.Property(type=bool, default=False, flags=GObject.ParamFlags.READWRITE)
	can_reset = GObject.Property(type=bool, default=False, flags=GObject.ParamFlags.READWRITE)
	is_linked = GObject.Property(type=bool, default=True, flags=(GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY))

	# File properties
	default_folder = GObject.Property(type=Gio.File, default=None, flags=GObject.ParamFlags.READWRITE)
	selected_file = GObject.Property(type=Gio.File, default=None, flags=GObject.ParamFlags.READWRITE)
	default_file = GObject.Property(type=Gio.File, default=None, flags=GObject.ParamFlags.READWRITE)

	# Dialog properties
	dlg_title = GObject.Property(type=str, default="Open File", flags=GObject.ParamFlags.READWRITE)
	dlg_parent = GObject.Property(type=Gtk.Widget, default=None, flags=(GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY))

	# Class widget variables
	image = Gtk.Template.Child("image")
	label = Gtk.Template.Child("label")
	file_btn = Gtk.Template.Child("file-btn")
	clear_btn = Gtk.Template.Child("clear-btn")
	reset_btn = Gtk.Template.Child("reset-btn")

	# Dialog variable
	dialog = Gtk.Template.Child("dialog")

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		# Update widget state
		if self.is_linked == True:
			self.add_css_class("linked")
		else: 
			self.set_spacing(6)
			if self.can_clear == True: self.clear_btn.add_css_class("flat")
			if self.can_reset == True: self.reset_btn.add_css_class("flat")

		self.notify("icon-name")
		self.notify("can-clear")
		self.notify("can-reset")

		self.notify("selected-file")
		self.notify("default-file")

		# Dialog parent
		self.dialog.set_transient_for(self.dlg_parent)

	@Gtk.Template.Callback()
	def on_activate(self, cycling, data):
		self.file_btn.activate()

	@Gtk.Template.Callback()
	def on_icon_name_notify(self, pspec, user_data):
		icon_name = self.icon_name

		if icon_name == "":
			icon_name = "folder-symbolic" if self.folder_select == True else "document-open-symbolic"

		self.image.set_from_icon_name(icon_name)

	def set_clear_btn_state(self):
		self.clear_btn.set_sensitive(self.selected_file is not None)

	def set_reset_btn_state(self):
		if self.default_file is None or self.selected_file is None:
			self.reset_btn.set_sensitive(self.default_file is not None)
		else:
			self.reset_btn.set_sensitive(not self.default_file.equal(self.selected_file))

	@Gtk.Template.Callback()
	def on_can_clear_notify(self, pspec, user_data):
		self.clear_btn.set_visible(self.can_clear)

		if self.can_clear == True: self.set_clear_btn_state()

	@Gtk.Template.Callback()
	def on_can_reset_notify(self, pspec, user_data):
		self.reset_btn.set_visible(self.can_reset)

		if self.can_reset == True: self.set_reset_btn_state()

	@Gtk.Template.Callback()
	def on_selected_file_notify(self, pspec, user_data):
		self.label.set_text(self.selected_file.get_basename() if self.selected_file is not None else "(None)")

		if self.can_clear == True: self.set_clear_btn_state()
		if self.can_reset == True: self.set_reset_btn_state()

	@Gtk.Template.Callback()
	def on_default_file_notify(self, pspec, user_data):
		if self.can_reset == True: self.set_reset_btn_state()

	@Gtk.Template.Callback()
	def on_file_btn_clicked(self, button):
		self.dialog.set_title(self.dlg_title)
		self.dialog.set_action(Gtk.FileChooserAction.SELECT_FOLDER if self.folder_select == True else Gtk.FileChooserAction.OPEN)

		if self.selected_file is not None:
			self.dialog.set_file(self.selected_file)
		else:
			if self.default_folder is not None:
				self.dialog.set_current_folder(self.default_folder)

		self.dialog.show()

	@Gtk.Template.Callback()
	def on_dialog_response(self, dialog, response):
		if response == Gtk.ResponseType.ACCEPT:
			self.selected_file = dialog.get_file()

	@Gtk.Template.Callback()
	def on_clear_btn_clicked(self, button):
		self.selected_file = None

	@Gtk.Template.Callback()
	def on_reset_btn_clicked(self, button):
		self.selected_file = self.default_file

	def set_file_filter(self, name, mime_types):
		if mime_types is not None:
			file_filter = Gtk.FileFilter()
			for mime_type in mime_types:
				file_filter.add_mime_type(mime_type)
			file_filter.set_name(name)
			self.dialog.add_filter(file_filter)

	def set_default_folder(self, def_folder):
		self.default_folder = Gio.File.new_for_path(def_folder) if def_folder != "" else None
		
	def set_selected_file(self, sel_file):
		self.selected_file = Gio.File.new_for_path(sel_file) if sel_file != "" else None

	def get_selected_file(self):
		return(self.selected_file.get_path() if self.selected_file is not None else "")

	def set_default_file(self, def_file):
		self.default_file = Gio.File.new_for_path(def_file) if def_file != "" else None

class PreferencesWindow(Adw.PreferencesWindow):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.set_default_size(560, -1)
		self.set_title("Zandronum Preferences")
		self.set_modal(True)
		self.set_search_enabled(False)

		self.connect("close-request", self.on_window_close)

		# Executable button
		self.exec_btn = FileDialogButton(valign=Gtk.Align.CENTER, width_request=300, dlg_title="Select Zandronum Executable", dlg_parent=self, icon_name="application-x-executable-symbolic", can_reset=True)

		self.exec_listrow = Adw.ActionRow(title="_Zandronum Path", use_underline=True)
		self.exec_listrow.add_suffix(self.exec_btn)
		self.exec_listrow.set_activatable_widget(self.exec_btn)

		# IWAD dir button
		self.iwaddir_btn = FileDialogButton(valign=Gtk.Align.CENTER, width_request=300, dlg_title="Select IWAD Folder", dlg_parent=self, folder_select=True, can_reset=True)

		self.iwaddir_listrow = Adw.ActionRow(title="_IWAD Folder", use_underline=True)
		self.iwaddir_listrow.add_suffix(self.iwaddir_btn)
		self.iwaddir_listrow.set_activatable_widget(self.iwaddir_btn)

		# PWAD dir button
		self.pwaddir_btn = FileDialogButton(valign=Gtk.Align.CENTER, width_request=300, dlg_title="Select Default WAD Folder", dlg_parent=self, folder_select=True, can_reset=True)

		self.pwaddir_listrow = Adw.ActionRow(title="Default _WAD Folder", use_underline=True)
		self.pwaddir_listrow.add_suffix(self.pwaddir_btn)
		self.pwaddir_listrow.set_activatable_widget(self.pwaddir_btn)

		# Mods switch
		self.mods_switch = Gtk.Switch(valign=Gtk.Align.CENTER)

		self.mods_listrow = Adw.ActionRow(title="Enable Hi-Res _Graphics", use_underline=True)
		self.mods_listrow.add_suffix(self.mods_switch)
		self.mods_listrow.set_activatable_widget(self.mods_switch)

		# Preferences group
		self.prefs_group = Adw.PreferencesGroup(title="Preferences")
		self.prefs_group.add(self.exec_listrow)
		self.prefs_group.add(self.iwaddir_listrow)
		self.prefs_group.add(self.pwaddir_listrow)
		self.prefs_group.add(self.mods_listrow)

		# Preferences page
		self.page = Adw.PreferencesPage()
		self.page.add(self.prefs_group)

		self.add(self.page)

		# Widget initialization
		self.exec_btn.set_default_file(app.default_exec_file)
		self.exec_btn.set_selected_file(app.main_config["zandronum"]["exec_file"])

		self.iwaddir_btn.set_default_file(app.default_iwad_dir)
		self.iwaddir_btn.set_selected_file(app.main_config["zandronum"]["iwad_dir"])

		self.pwaddir_btn.set_default_file(app.default_pwad_dir)
		self.pwaddir_btn.set_selected_file(app.main_config["zandronum"]["pwad_dir"])

		self.mods_switch.set_active(app.main_config["zandronum"]["use_mods"])

	def on_window_close(self, window):
		app.main_config["zandronum"]["exec_file"] = self.exec_btn.get_selected_file()

		iwad_dir = self.iwaddir_btn.get_selected_file()

		if iwad_dir != app.main_config["zandronum"]["iwad_dir"]:
			app.main_config["zandronum"]["iwad_dir"] = iwad_dir
			app.main_window.populate_iwad_combo()

		pwad_dir = self.pwaddir_btn.get_selected_file()

		app.main_config["zandronum"]["pwad_dir"] = pwad_dir
		app.main_window.pwad_btn.set_default_folder(pwad_dir)

		app.main_config["zandronum"]["use_mods"] = self.mods_switch.get_active()

		self.destroy()

class MainWindow(Adw.ApplicationWindow):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		# Zandronum launch flag
		self.launch_flag = False

		# Window properties
		self.set_default_size(620, -1)
		self.set_valign(Gtk.Align.CENTER)
		self.set_title("Zandronum Launcher")

		# Shortcut window
		shortcut_builder = Gtk.Builder.new_from_file(os.path.join(app.app_dir, "ui/shortcutwindow.ui"))
		self.shortcut_window = shortcut_builder.get_object("shortcut-window")
		self.set_help_overlay(self.shortcut_window)

		self.connect("close-request", self.on_window_close)

		# Actions
		self.menu_reset_action = Gio.SimpleAction.new("menu-reset", None)
		self.menu_reset_action.connect("activate", self.on_menu_reset_action)
		self.add_action(self.menu_reset_action)
		app.set_accels_for_action("win.menu-reset", ["<ctrl>r"])

		self.menu_prefs_action = Gio.SimpleAction.new("menu-prefs", None)
		self.menu_prefs_action.connect("activate", self.on_menu_prefs_action)
		self.add_action(self.menu_prefs_action)
		app.set_accels_for_action("win.menu-prefs", ["<ctrl>comma", "<ctrl>p"])

		self.key_quit_action = Gio.SimpleAction.new("key-quit", None)
		self.key_quit_action.connect("activate", self.on_key_quit_action)
		self.add_action(self.key_quit_action)
		app.set_accels_for_action("win.key-quit", ["<ctrl>q"])

		self.key_launch_action = Gio.SimpleAction.new("key-launch", None)
		self.key_launch_action.connect("activate", self.on_key_launch_action)
		self.add_action(self.key_launch_action)
		app.set_accels_for_action("win.key-launch", ["<ctrl>Return", "<ctrl>KP_Enter"])

		app.set_accels_for_action("win.show-help-overlay", ["<ctrl>question"])

		# Header
		headermenu_builder = Gtk.Builder.new_from_file(os.path.join(app.app_dir, "ui/headermenu.ui"))
		self.header_popover = headermenu_builder.get_object("header-popover")

		self.menu_btn = Gtk.MenuButton(icon_name="open-menu-symbolic", primary=True)
		self.menu_btn.set_popover(self.header_popover)

		self.header_bar = Gtk.HeaderBar()
		self.header_bar.pack_end(self.menu_btn)

		# IWAD (game) combo
		self.iwad_combo = Gtk.ComboBox(valign=Gtk.Align.CENTER, width_request=350)

		self.iwad_store = Gtk.ListStore(str, str)
		self.iwad_combo.set_model(self.iwad_store)

		iwad_cell = Gtk.CellRendererText()

		self.iwad_combo.pack_start(iwad_cell, True)
		self.iwad_combo.add_attribute(iwad_cell, "text", 0)

		self.iwad_listrow = Adw.ActionRow(title="_Game", use_underline=True)
		self.iwad_listrow.add_suffix(self.iwad_combo)
		self.iwad_listrow.set_activatable_widget(self.iwad_combo)

		# PWAD button
		pwad_filter = ["application/x-doom-wad", "application/zip", "application/x-7z-compressed"]

		self.pwad_btn = FileDialogButton(valign=Gtk.Align.CENTER, dlg_title="Open WAD File", dlg_parent=self, can_clear=True, width_request=350)
		self.pwad_btn.set_file_filter("WAD files", pwad_filter)

		self.pwad_listrow = Adw.ActionRow(title="Optional WAD _File", use_underline=True)
		self.pwad_listrow.add_suffix(self.pwad_btn)
		self.pwad_listrow.set_activatable_widget(self.pwad_btn)

		# Custom params entry
		self.params_entry = Gtk.Entry(valign=Gtk.Align.CENTER, secondary_icon_name="edit-clear-symbolic", width_request=350)
		self.params_entry.connect("icon-press", self.on_params_entry_clear)

		self.params_listrow = Adw.ActionRow(title="_Custom Switches", use_underline=True)
		self.params_listrow.add_suffix(self.params_entry)
		self.params_listrow.set_activatable_widget(self.params_entry)

		# Additional expander row
		self.add_expandrow = Adw.ExpanderRow(title="_Additional Parameters", use_underline=True, show_enable_switch=True)
		self.add_expandrow.add_row(self.params_listrow)

		# Launch params group
		self.launch_group = Adw.PreferencesGroup(title="Launch Parameters")
		self.launch_group.add(self.iwad_listrow)
		self.launch_group.add(self.pwad_listrow)
		self.launch_group.add(self.add_expandrow)

		# Launch button
		self.launch_btn = Gtk.Button(label="_Launch Zandronum", halign=Gtk.Align.CENTER, use_underline=True, css_classes=["suggested-action", "pill"])
		self.launch_btn.connect("clicked", self.on_launch_btn_clicked)

		# Launch box
		self.launch_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=28)

		self.launch_box.append(self.launch_group)
		self.launch_box.append(self.launch_btn)

		# Launch clamp
		self.launch_clamp = Adw.Clamp(margin_top=24, margin_bottom=28)
		self.launch_clamp.set_child(self.launch_box)

		# Window box
		self.win_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

		self.win_box.append(self.header_bar)
		self.win_box.append(self.launch_clamp)

		# Toast overlay
		self.toast_overlay = Adw.ToastOverlay()
		self.toast_overlay.set_child(self.win_box)
		
		self.set_content(self.toast_overlay)
		self.set_focus(self.iwad_listrow)

		# Widget initialization
		self.populate_iwad_combo()

		self.pwad_btn.set_default_folder(app.main_config["zandronum"]["pwad_dir"])
		self.pwad_btn.set_selected_file(app.main_config["launcher"]["file"])

		self.params_entry.set_text(app.main_config["launcher"]["params"])

		self.add_expandrow.set_enable_expansion(app.main_config["launcher"]["params_on"])
		self.add_expandrow.set_expanded(app.main_config["launcher"]["params_on"])

	def populate_iwad_combo(self):
		self.iwad_store.clear()

		iwad_index = 0

		iwads = os.listdir(app.main_config["zandronum"]["iwad_dir"])
		iwads.sort()

		for i in range(len(iwads)):
			iwad_lc = iwads[i].lower()

			if iwad_lc in doom_iwads:
				iwad_iter = self.iwad_store.append()
				self.iwad_store.set_value(iwad_iter, 0, doom_iwads[iwad_lc]["name"])
				self.iwad_store.set_value(iwad_iter, 1, iwad_lc)
				
			if iwad_lc == app.main_config["launcher"]["iwad"]:
				iwad_index = i

		try:
			self.iwad_combo.set_active(iwad_index)
		except:
			self.iwad_combo.set_active(-1)

		self.launch_btn.set_sensitive(True if len(self.iwad_store) > 0 else False)
		self.key_launch_action.set_enabled(True if len(self.iwad_store) > 0 else False)

	def on_params_entry_clear(self, pos, data):
		self.params_entry.set_text("")

	def on_launch_btn_clicked(self, button):
		self.launch_flag = True

		self.close()

	def on_key_launch_action(self, action, param):
		self.launch_btn.activate()

	def on_key_quit_action(self, action, param):
		self.close()

	def on_menu_reset_action(self, action, param):
		try:
			self.iwad_combo.set_active(0)
		except:
			self.iwad_combo.set_active(-1)
		self.pwad_btn.set_selected_file("")
		self.params_entry.set_text("")
		self.add_expandrow.set_enable_expansion(False)

	def on_menu_prefs_action(self, action, param):
		prefs_window = PreferencesWindow(transient_for=self)
		prefs_window.show()

	def on_window_close(self, window):
		error_status = False

		iwad_item = self.iwad_combo.get_active_iter()

		try:
			iwad_name = self.iwad_store[iwad_item][1]
		except:
			iwad_name = ""

		pwad_file = self.pwad_btn.get_selected_file()

		params = self.params_entry.get_text()
		params_on = (self.add_expandrow.get_enable_expansion() and params != "")

		if self.launch_flag == True:
			error_status = self.launch_zandronum(iwad_name, pwad_file, params, params_on)

			if error_status == True: self.launch_flag = False

		if error_status == False:
			app.main_config["launcher"]["iwad"] = iwad_name
			app.main_config["launcher"]["file"] = pwad_file
			app.main_config["launcher"]["params"] = params
			app.main_config["launcher"]["params_on"] = params_on

		return(error_status)

	def launch_zandronum(self, iwad_name, pwad_file, params, params_on):
		# Return with error if Zandronum executable does not exist
		if os.path.exists(app.main_config["zandronum"]["exec_file"]) == False:
			self.show_toast("ERROR: Zandronum executable not found")
			return(True)

		# Initialize Zandronum command line with executable
		cmdline = app.main_config["zandronum"]["exec_file"]

		# Return with error if IWAD name is empty
		if iwad_name == "":
			self.show_toast("ERROR: No IWAD file specified")
			return(True)

		iwad_file = os.path.join(app.main_config["zandronum"]["iwad_dir"], iwad_name)

		# Return with error if IWAD file does not exist
		if os.path.exists(iwad_file) == False:
			self.show_toast("ERROR: IWAD file {:s} not found".format(iwad_name))
			return(True)

		# Add IWAD file
		cmdline += ' -iwad "{:s}"'.format(iwad_file)

		# Add patch file if present
		patch_name = doom_iwads[iwad_name]["patch"]
		if patch_name != "":
			patch_file = os.path.join(app.patch_dir, patch_name)

			if os.path.exists(patch_file): cmdline += ' -file "{:s}"'.format(patch_file)

		# Add mod files if use hi-res graphics option is true
		if app.main_config["zandronum"]["use_mods"] == True:
			mod_list = doom_iwads[iwad_name]["mods"]

			for mod_name in mod_list:
				if mod_name != "":
					mod_file = os.path.join(app.mod_dir, mod_name)

					if os.path.exists(mod_file): cmdline += ' -file "{:s}"'.format(mod_file)

		# Add PWAD file if present
		if pwad_file != "" and os.path.exists(pwad_file): cmdline += ' -file "{:s}"'.format(pwad_file)

		# Add extra params if present and enabled
		if params_on == True:
			if params != "": cmdline += ' {:s}'.format(params)

		# Launch Zandronum
		subprocess.Popen(shlex.split(cmdline))

		return(False)

	def show_toast(self, toast_title):
		toast = Adw.Toast(title=toast_title, priority=Adw.ToastPriority.HIGH)
		self.toast_overlay.add_toast(toast)

class LauncherApp(Adw.Application):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.connect("activate", self.on_activate)

		# App dirs
		self.app_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
		self.patch_dir = os.path.join(self.app_dir, "patches")
		self.mod_dir = os.path.join(self.app_dir, "mods")

		# Config dir
		self.config_dir = os.path.join(os.getenv("HOME"), ".config/zandronum")

		if os.path.exists(self.config_dir) == False:
			os.makedirs(self.config_dir)

		# Zandronum INI file
		self.zandronum_ini_file = os.path.join(self.config_dir, "zandronum.ini")

		if os.path.exists(self.zandronum_ini_file) == False:
			zandronum_ini_src = os.path.join(self.app_dir, "config/zandronum.ini")

			shutil.copyfile(zandronum_ini_src, zandronum_ini_file)

		# Default settings
		self.default_exec_file = "/usr/bin/zandronum"
		self.default_iwad_dir = os.path.join(self.app_dir, "iwads")
		self.default_pwad_dir = self.config_dir

		# Parse configuration file
		self.launcher_config_file = os.path.join(self.config_dir, "launcher.conf")

		parser = configparser.ConfigParser()
		parser.read(self.launcher_config_file)

		self.main_config = { "launcher": {}, "zandronum": {} }

		self.main_config["launcher"]["iwad"] = parser.get("launcher", "iwad", fallback="")
		self.main_config["launcher"]["file"] = parser.get("launcher", "file", fallback="")
		self.main_config["launcher"]["params"] = parser.get("launcher", "params", fallback="")
		try:
			self.main_config["launcher"]["params_on"] = parser.getboolean("launcher", "params_on", fallback=False)
		except:
			self.main_config["launcher"]["params_on"] = False

		self.main_config["zandronum"]["exec_file"] = parser.get("zandronum", "exec_file", fallback=self.default_exec_file)
		self.main_config["zandronum"]["iwad_dir"] = parser.get("zandronum", "iwad_dir", fallback=self.default_iwad_dir)
		self.main_config["zandronum"]["pwad_dir"] = parser.get("zandronum", "pwad_dir", fallback=self.default_pwad_dir)
		try:
			self.main_config["zandronum"]["use_mods"] = parser.getboolean("zandronum", "use_mods", fallback=True)
		except:
			self.main_config["zandronum"]["use_mods"] = True

		if self.main_config["zandronum"]["exec_file"] == "" or os.path.exists(self.main_config["zandronum"]["exec_file"]) == False:
			self.main_config["zandronum"]["exec_file"] = self.default_exec_file

		if self.main_config["zandronum"]["iwad_dir"] == "" or os.path.exists(self.main_config["zandronum"]["iwad_dir"]) == False:
			self.main_config["zandronum"]["iwad_dir"] = self.default_iwad_dir

		if self.main_config["zandronum"]["pwad_dir"] == "" or os.path.exists(self.main_config["zandronum"]["pwad_dir"]) == False:
			self.main_config["zandronum"]["pwad_dir"] = self.default_pwad_dir

	def on_activate(self, app):
		self.main_window = MainWindow(application=app)
		self.main_window.present()

	def write_launcher_config(self):
		parser = configparser.ConfigParser()
		parser.read_dict(self.main_config)

		with open(self.launcher_config_file, "w") as configfile:
			parser.write(configfile)

# Main app
app = LauncherApp(application_id="com.github.zandronumlauncher")
app.run(sys.argv)

app.write_launcher_config()

app.main_window.destroy()
