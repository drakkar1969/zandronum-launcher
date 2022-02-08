#!/usr/bin/env python

import gi, sys, os, configparser, subprocess, shlex
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GObject, Gdk

# IWAD filenames/descriptions/mod files
doom_iwads = {
	"doom.wad": {"name": "The Ultimate Doom", "patch": "", "mods": ["hud-stuff.pk3", "zdoom-1.pk3", "zdoom-2.pk3", "jfo-udoom.pk3"]},
	"doom2.wad": {"name": "Doom II: Hell on Earth", "patch": "", "mods": ["hud-stuff.pk3", "zdoom-1.pk3", "zdoom-2.pk3", "zdoom-doom2.pk3", "jfo-doom2.pk3"]},
	"plutonia.wad": {"name": "Final Doom - The Plutonia Experiment", "patch": "", "mods": ["hud-stuff.pk3", "zdoom-1.pk3", "zdoom-2.pk3", "zdoom-doom2.pk3", "zdoom-plut.pk3", "jfo-plut.pk3"]},
	"tnt.wad": {"name": "Final Doom - TNT: Evilution", "patch": "tnt31-patch.wad", "mods": ["hud-stuff.pk3", "zdoom-1.pk3", "zdoom-2.pk3", "zdoom-doom2.pk3", "zdoom-tnt.pk3", "jfo-tnt.pk3"]},
	"freedoom1.wad": {"name": "Freedoom Phase 1", "patch": "", "mods": []},
	"freedoom2.wad": {"name": "Freedoom Phase 2", "patch": "", "mods": []}
}

class FileDialogButton(Gtk.Button):
	dlg_title = GObject.Property(type=str, default="Open File", flags=GObject.ParamFlags.READWRITE)
	dlg_parent = GObject.Property(type=Gtk.Widget, default=None, flags=GObject.ParamFlags.READWRITE)
	folder_select = GObject.Property(type=bool, default=False, flags=GObject.ParamFlags.READWRITE)
	btn_icon = GObject.Property(type=str, default="", flags=GObject.ParamFlags.READWRITE)

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		# Initialize class variables
		self.selected_file = None
		self.default_folder = None
		if self.btn_icon == "":
			self.btn_icon = "folder-symbolic" if self.folder_select == True else "document-open-symbolic"

		# Add button widget
		self.content = Adw.ButtonContent(label="", icon_name=self.btn_icon, halign=Gtk.Align.START)
		image = self.content.get_first_child()
		if image is not None: image.set_margin_end(6)
		self.set_child(self.content)

		# Create dialog
		self.dialog = Gtk.FileChooserNative.new(title=self.dlg_title, parent=self.dlg_parent, action=Gtk.FileChooserAction.SELECT_FOLDER if self.folder_select == True else Gtk.FileChooserAction.OPEN)
		self.dialog.set_select_multiple(False)
		self.dialog.set_modal(True)
		self.dialog.connect("response", self.on_dialog_response)

		# Set handler for button click
		self.connect("clicked", self.on_clicked)

	def set_label(self):
		self.content.set_label(self.selected_file.get_basename() if self.selected_file is not None else "(None)")

	def set_file_filter(self, file_filter):
		if file_filter is not None:
			ffilter = Gtk.FileFilter()
			ffilter.set_name(file_filter["name"])
			for pattern in file_filter["patterns"]:
				ffilter.add_pattern(pattern)
			self.dialog.add_filter(ffilter)

	def set_selected_file(self, sel_file):
		self.selected_file = Gio.File.new_for_path(sel_file) if sel_file != "" else None
		self.set_label()

	def get_selected_file(self):
		return(self.selected_file.get_path() if self.selected_file is not None else "")

	def set_default_folder(self, def_folder):
		self.default_folder = Gio.File.new_for_path(def_folder) if def_folder != "" else None
		self.set_label()

	def on_clicked(self, button):
		if self.selected_file is not None:
			self.dialog.set_file(self.selected_file)
		else:
			if self.default_folder is not None:
				self.dialog.set_current_folder(self.default_folder)

		self.dialog.show()

	def on_dialog_response(self, dialog, response):
		if response == Gtk.ResponseType.ACCEPT:
			self.selected_file = dialog.get_file()
			self.set_label()

class PreferencesWindow(Adw.PreferencesWindow):
	win_parent = GObject.Property(type=Gtk.Window, default=None, flags=GObject.ParamFlags.READWRITE)

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.set_default_size(520, -1)
		self.set_title("Zandronum Preferences")
		self.set_transient_for(self.win_parent)
		self.set_destroy_with_parent(True)
		self.set_modal(True)
		self.set_search_enabled(False)

		# Executable button
		self.exec_btn = FileDialogButton(valign=Gtk.Align.CENTER, width_request=300, dlg_title="Select Zandronum Executable", dlg_parent=self, btn_icon="application-x-executable-symbolic")

		self.exec_listrow = Adw.ActionRow(title="Application _Path", activatable=True, selectable=True)
		self.exec_listrow.add_suffix(self.exec_btn)
		self.exec_listrow.set_activatable_widget(self.exec_btn)
		self.exec_listrow.set_use_underline(True)

		# IWAD dir button
		self.iwaddir_btn = FileDialogButton(valign=Gtk.Align.CENTER, width_request=300, dlg_title="Select IWAD Directory", dlg_parent=self, folder_select=True)

		self.iwaddir_listrow = Adw.ActionRow(title="IWAD _Directory", activatable=True, selectable=True)
		self.iwaddir_listrow.add_suffix(self.iwaddir_btn)
		self.iwaddir_listrow.set_activatable_widget(self.iwaddir_btn)
		self.iwaddir_listrow.set_use_underline(True)

		# Mods switch
		self.mods_switch = Gtk.Switch(valign=Gtk.Align.CENTER)

		self.mods_listrow = Adw.ActionRow(title="Enable Hi-Res _Graphics", activatable=True, selectable=True)
		self.mods_listrow.add_suffix(self.mods_switch)
		self.mods_listrow.set_activatable_widget(self.mods_switch)
		self.mods_listrow.set_use_underline(True)

		# Preferences group
		self.prefs_group = Adw.PreferencesGroup(title="Preferences")
		self.prefs_group.add(self.exec_listrow)
		self.prefs_group.add(self.iwaddir_listrow)
		self.prefs_group.add(self.mods_listrow)

		# Preferences page
		self.page = Adw.PreferencesPage()
		self.page.add(self.prefs_group)

		self.add(self.page)

class MainWindow(Adw.ApplicationWindow):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.set_default_size(620, -1)
		self.set_title("Zandronum Launcher")

		# Actions
		self.action_menu_reset = Gio.SimpleAction.new("menu_reset", None)
		self.action_menu_reset.connect("activate", self.on_menu_reset_clicked)
		self.add_action(self.action_menu_reset)

		self.action_menu_prefs = Gio.SimpleAction.new("menu_prefs", None)
		self.action_menu_prefs.connect("activate", self.on_menu_prefs_clicked)
		self.add_action(self.action_menu_prefs)
		app.set_accels_for_action("win.menu_prefs", ["<primary>comma"])

		self.action_key_quit = Gio.SimpleAction.new("key_quit", None)
		self.action_key_quit.connect("activate", self.on_keypress_quit)
		self.add_action(self.action_key_quit)
		app.set_accels_for_action("win.key_quit", ["q", "<primary>q"])

		self.action_key_launch = Gio.SimpleAction.new("key_launch", None)
		self.action_key_launch.connect("activate", self.on_keypress_launch)
		self.add_action(self.action_key_launch)
		app.set_accels_for_action("win.key_launch", ["<primary>Return", "<primary>KP_Enter"])

		# Header menu
		reset_menu = Gio.Menu.new()
		reset_menu.append("Reset to Defaults", "win.menu_reset")
		prefs_menu = Gio.Menu.new()
		prefs_menu.append("Zandronum Preferences...", "win.menu_prefs")

		header_menu = Gio.Menu.new()
		header_menu.append_section(None, reset_menu)
		header_menu.append_section(None, prefs_menu)

		self.header_popover = Gtk.PopoverMenu()
		self.header_popover.set_menu_model(header_menu)

		# Header
		self.header_bar = Adw.HeaderBar()

		self.launch_btn = Gtk.Button(label="Launch")
		self.launch_btn.add_css_class("suggested-action")
		self.launch_btn.add_css_class("default")
		self.launch_btn.connect("clicked", self.on_launch_btn_clicked)

		self.menu_btn = Gtk.MenuButton(icon_name="open-menu-symbolic")
		self.menu_btn.set_popover(self.header_popover)

		self.header_bar.pack_start(self.launch_btn)
		self.header_bar.pack_end(self.menu_btn)

		# IWAD (game) combo
		self.iwad_combo = Gtk.ComboBox(valign=Gtk.Align.CENTER, width_request=350)

		self.iwad_store = Gtk.ListStore(str, str)
		self.iwad_combo.set_model(self.iwad_store)

		iwad_renderer = Gtk.CellRendererText()

		self.iwad_combo.pack_start(iwad_renderer, True)
		self.iwad_combo.add_attribute(iwad_renderer, "text", 0)

		self.populate_iwad_combo()

		self.iwad_listrow = Adw.ActionRow(title="_Game", activatable=True, selectable=True)
		self.iwad_listrow.add_suffix(self.iwad_combo)
		self.iwad_listrow.set_activatable_widget(self.iwad_combo)
		self.iwad_listrow.set_use_underline(True)

		# PWAD file/clear buttons
		pwad_filter = {
			"name": "WAD files (*.wad, *.pk3, *.pk7, *.zip, *.7z)",
			"patterns": ["*.wad", "*.WAD", "*.pk3", "*.PK3", "*.pk7", "*.PK7", "*.zip", "*.ZIP", "*.7z", "*.7Z"]
		}

		self.pwadfile_btn = FileDialogButton(valign=Gtk.Align.CENTER, width_request=304, dlg_title="Select WAD File", dlg_parent=self)
		self.pwadfile_btn.set_file_filter(pwad_filter)
		self.pwadfile_btn.set_default_folder(app.config_dir)
		self.pwadfile_btn.set_selected_file(app.main_config["launcher"]["file"])

		self.pwadclear_btn = Gtk.Button(icon_name="edit-clear-symbolic", valign=Gtk.Align.CENTER)
		self.pwadclear_btn.connect("clicked", self.on_pwadclear_btn_clicked)

		self.pwad_listrow = Adw.ActionRow(title="Optional WAD _File", activatable=True, selectable=True)
		self.pwad_listrow.add_suffix(self.pwadfile_btn)
		self.pwad_listrow.add_suffix(self.pwadclear_btn)
		self.pwad_listrow.set_activatable_widget(self.pwadfile_btn)
		self.pwad_listrow.set_use_underline(True)

		# Custom params entry
		self.params_entry = Gtk.Entry(valign=Gtk.Align.CENTER, width_request=350)
		self.params_entry.set_text(app.main_config["launcher"]["params"])

		self.params_listrow = Adw.ActionRow(title="_Custom Switches", activatable=True, selectable=True)
		self.params_listrow.add_suffix(self.params_entry)
		self.params_listrow.set_activatable_widget(self.params_entry)
		self.params_listrow.set_use_underline(True)

		# Additional expander row
		self.add_expandrow = Adw.ExpanderRow(title="_Additional Parameters", activatable=True, selectable=True)
		self.add_expandrow.add_row(self.params_listrow)
		self.add_expandrow.set_show_enable_switch(True)
		self.add_expandrow.set_enable_expansion(app.main_config["launcher"]["params_on"])
		self.add_expandrow.set_expanded(app.main_config["launcher"]["params_on"])
		self.add_expandrow.set_use_underline(True)

		# Preferences group
		self.prefs_group = Adw.PreferencesGroup(title="Launch Parameters")
		self.prefs_group.add(self.iwad_listrow)
		self.prefs_group.add(self.pwad_listrow)
		self.prefs_group.add(self.add_expandrow)

		# Preferences box
		self.prefs_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		self.prefs_box.set_spacing(30)
		self.prefs_box.set_margin_top(24)
		self.prefs_box.set_margin_bottom(36)
		self.prefs_box.set_margin_start(36)
		self.prefs_box.set_margin_end(36)
		self.prefs_box.append(self.prefs_group)

		# Window box
		self.win_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

		self.win_box.append(self.header_bar)
		self.win_box.append(self.prefs_box)
		
		# self.set_child(self.win_box)
		self.set_content(self.win_box)

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
		self.action_key_launch.set_enabled(True if len(self.iwad_store) > 0 else False)

	def on_keypress_quit(self, action, param):
		self.destroy()

	def on_keypress_launch(self, action, param):
		app.launch_flag = True

		self.destroy()

	def on_pwadclear_btn_clicked(self, button):
		self.pwadfile_btn.set_selected_file("")

	def on_launch_btn_clicked(self, button):
		app.launch_flag = True

		self.destroy()

	def on_menu_reset_clicked(self, action, param):
		try:
			self.iwad_combo.set_active(0)
		except:
			self.iwad_combo.set_active(-1)
		self.pwadfile_btn.set_selected_file("")
		self.params_entry.set_text("")
		self.add_expandrow.set_enable_expansion(False)

	def on_menu_prefs_clicked(self, action, param):
		prefs_window = PreferencesWindow(win_parent=self)

		prefs_window.exec_btn.set_selected_file(app.main_config["zandronum"]["exec_file"])
		prefs_window.iwaddir_btn.set_selected_file(app.main_config["zandronum"]["iwad_dir"])
		prefs_window.mods_switch.set_active(app.main_config["zandronum"]["use_mods"])

		prefs_window.connect("close-request", self.on_preferences_window_close)

		prefs_window.show()

	def on_preferences_window_close(self, window):
		exec_file = window.exec_btn.get_selected_file()

		if exec_file != "":
			app.main_config["zandronum"]["exec_file"] = exec_file

		iwad_dir = window.iwaddir_btn.get_selected_file()

		if iwad_dir != "" and iwad_dir != app.main_config["zandronum"]["iwad_dir"]:
			app.main_config["zandronum"]["iwad_dir"] = iwad_dir
			self.populate_iwad_combo()

		app.main_config["zandronum"]["use_mods"] = window.mods_switch.get_active()

	def get_iwad_combo_selection(self):
		iwad_item = self.iwad_combo.get_active_iter()

		try:
			iwad_filename = self.iwad_store[iwad_item][1]
		except:
			iwad_filename = ""

		return(iwad_filename)

class LauncherApp(Adw.Application):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.connect('activate', self.on_activate)

		# Launch Zandronum flag
		self.launch_flag = False

		# App dirs
		self.app_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
		self.patch_dir = os.path.join(self.app_dir, "patches")
		self.mod_dir = os.path.join(self.app_dir, "mods")

		# Config dir
		self.config_dir = os.path.join(os.getenv('HOME'), ".config/zandronum")

		if os.path.exists(self.config_dir) == False:
			os.makedirs(self.config_dir, exist_ok=True)

		# Zandronum INI file
		self.zandronum_ini_file = os.path.join(self.config_dir, "zandronum.ini")

		if os.path.exists(self.zandronum_ini_file) == False:
			zandronum_ini_src = os.path.join(app_dir, "config/zandronum.ini")

			shutil.copyfile(zandronum_ini_src, zandronum_ini_file)

		# Parse configuration file
		self.launcher_config_file = os.path.join(self.config_dir, "launcher.conf")

		parser = configparser.ConfigParser()
		parser.read(self.launcher_config_file)

		default_exec_file = "/usr/bin/zandronum"
		default_iwad_dir = os.path.join(self.app_dir, "iwads")

		self.main_config = { "launcher": {}, "zandronum": {} }

		self.main_config["launcher"]["iwad"] = parser.get("launcher", "iwad", fallback="")
		self.main_config["launcher"]["file"] = parser.get("launcher", "file", fallback="")
		self.main_config["launcher"]["params"] = parser.get("launcher", "params", fallback="")
		try:
			self.main_config["launcher"]["params_on"] = parser.getboolean("launcher", "params_on", fallback=False)
		except:
			self.main_config["launcher"]["params_on"] = False

		self.main_config["zandronum"]["exec_file"] = parser.get("zandronum", "exec_file", fallback=default_exec_file)
		self.main_config["zandronum"]["iwad_dir"] = parser.get("zandronum", "iwad_dir", fallback=default_iwad_dir)
		try:
			self.main_config["zandronum"]["use_mods"] = parser.getboolean("zandronum", "use_mods", fallback=True)
		except:
			self.main_config["zandronum"]["use_mods"] = True

		if self.main_config["zandronum"]["exec_file"] == "" or os.path.exists(self.main_config["zandronum"]["exec_file"]) == False:
			self.main_config["zandronum"]["exec_file"] = default_exec_file

		if self.main_config["zandronum"]["iwad_dir"] == "" or os.path.exists(self.main_config["zandronum"]["iwad_dir"]) == False:
			self.main_config["zandronum"]["iwad_dir"] = default_iwad_dir

	def on_activate(self, app):
		self.main_window = MainWindow(application=app)
		self.main_window.present()

	def write_launcher_config(self):
		# Read control values into config
		self.main_config["launcher"]["iwad"] = self.main_window.get_iwad_combo_selection()
		self.main_config["launcher"]["file"] = self.main_window.pwadfile_btn.get_selected_file()
		self.main_config["launcher"]["params"] = self.main_window.params_entry.get_text()
		self.main_config["launcher"]["params_on"] = self.main_window.add_expandrow.get_enable_expansion()

		# Save config
		parser = configparser.ConfigParser()
		parser.read_dict(self.main_config)

		with open(self.launcher_config_file, 'w') as configfile:
			parser.write(configfile)

	def launch_zandronum(self):
		# Initialize Zandronum command line with executable
		cmdline = self.main_config["zandronum"]["exec_file"]

		# Get IWAD name
		iwad_name = self.main_config["launcher"]["iwad"]

		# Add IWAD file if present
		if iwad_name != "":
			iwad_file = os.path.join(self.main_config["zandronum"]["iwad_dir"], iwad_name)

			if os.path.exists(iwad_file):
				cmdline += ' -iwad "{:s}"'.format(iwad_file)

				# Add patch file if present
				patch_name = doom_iwads[iwad_name]["patch"]
				if patch_name != "":
					patch_file = os.path.join(self.patch_dir, patch_name)

					if os.path.exists(patch_file):
						cmdline += ' -file "{:s}"'.format(patch_file)

				# Add mod files if use hi-res graphics option is true
				if self.main_config["zandronum"]["use_mods"] == True:
					mod_list = doom_iwads[iwad_name]["mods"]

					for mod_name in mod_list:
						if mod_name != "":
							mod_file = os.path.join(self.mod_dir, mod_name)

							if os.path.exists(mod_file):
								cmdline += ' -file "{:s}"'.format(mod_file)

				# Add PWAD file if present
				pwad_file = self.main_config["launcher"]["file"]
				if os.path.exists(pwad_file): cmdline += ' -file "{:s}"'.format(pwad_file)

				# Add extra params if present and enabled
				if self.main_config["launcher"]["params_on"] == True:
					extra_params = self.main_config["launcher"]["params"]
					if extra_params != "": cmdline += ' {:s}'.format(extra_params)
			else:
				print("Zandronum-Launcher: ERROR: IWAD file not found")
				return
		else:
			print("Zandronum-Launcher: ERROR: No IWAD file specified")
			return

		# Launch Zandronum
		subprocess.Popen(shlex.split(cmdline))

# Main app
app = LauncherApp(application_id="com.github.drakkar.zandronumlauncher")
app.run(sys.argv)

app.write_launcher_config()

if app.launch_flag == True:
	app.launch_zandronum()

app.main_window.destroy()
