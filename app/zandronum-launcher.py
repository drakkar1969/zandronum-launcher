#!/usr/bin/env python

import gi, sys, os, configparser, subprocess, shlex, json
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio, GObject

# Global path variables
app_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
ui_dir = os.path.join(app_dir, "ui")

#------------------------------------------------------------------------------
#-- CLASS: FILEDIALOGBUTTON
#------------------------------------------------------------------------------
@Gtk.Template(filename=os.path.join(ui_dir, "filedialogbutton.ui"))
class FileDialogButton(Gtk.Box):
	__gtype_name__ = "FileDialogButton"

	#-----------------------------------
	# Button signals
	#-----------------------------------
	__gsignals__ = {
		"files-changed": (GObject.SignalFlags.RUN_FIRST, None, ())
	}

	#-----------------------------------
	# Button properties
	#-----------------------------------
	_icon_name = ""
	_folder_select = False
	_can_clear = False
	_can_reset = False
	_is_linked = True

	# Simple properties
	dialog_parent = GObject.Property(type=Gtk.Window, default=None)
	title = GObject.Property(type=str, default="Open File")
	file_filter = GObject.Property(type=Gtk.FileFilter, default=None)
	multi_select = GObject.Property(type=bool, default=False)

	# icon_name property
	@GObject.Property(type=str, default="")
	def icon_name(self):
		return(self._icon_name)

	@icon_name.setter
	def icon_name(self, value):
		self._icon_name = value

		if self._icon_name == "":
			self.image.set_from_icon_name("folder-symbolic" if self._folder_select == True else "document-open-symbolic")
		else:
			self.image.set_from_icon_name(self._icon_name)

	# folder_select property
	@GObject.Property(type=bool, default=False)
	def folder_select(self):
		return(self._folder_select)

	@folder_select.setter
	def folder_select(self, value):
		self._folder_select = value

		if self._icon_name == "":
			self.image.set_from_icon_name("folder-symbolic" if self._folder_select == True else "document-open-symbolic")

	# can_clear property
	@GObject.Property(type=bool, default=False)
	def can_clear(self):
		return(self._can_clear)

	@can_clear.setter
	def can_clear(self, value):
		self._can_clear = value

		self.clear_btn.set_visible(self._can_clear)

	# can_reset property
	@GObject.Property(type=bool, default=False)
	def can_reset(self):
		return(self._can_reset)

	@can_reset.setter
	def can_reset(self, value):
		self._can_reset = value

		self.reset_btn.set_visible(self._can_reset)

	# is_linked property
	@GObject.Property(type=bool, default=True)
	def is_linked(self):
		return(self._is_linked)

	@is_linked.setter
	def is_linked(self, value):
		self._is_linked = value

		if self._is_linked == True:
			self.add_css_class("linked")
			self.set_spacing(0)
			self.clear_btn.remove_css_class("flat")
			self.reset_btn.remove_css_class("flat")
		else:
			self.remove_css_class("linked")
			self.set_spacing(6)
			self.clear_btn.add_css_class("flat")
			self.reset_btn.add_css_class("flat")

	#-----------------------------------
	# File properties
	#-----------------------------------
	_gfile_default_folder = None
	_gfile_default_file = None
	_gstore_selected_files = None

	# default_folder property
	@GObject.Property(type=str, default="")
	def default_folder(self):
		return(self._gfile_default_folder.get_path() if self._gfile_default_folder is not None else "")

	@default_folder.setter
	def default_folder(self, value):
		self._gfile_default_folder = Gio.File.new_for_path(value) if value != "" else None

	# default_file property
	@GObject.Property(type=str, default="")
	def default_file(self):
		return(self._gfile_default_file.get_path() if self._gfile_default_file is not None else "")

	@default_file.setter
	def default_file(self, value):
		self._gfile_default_file = Gio.File.new_for_path(value) if value != "" else None

		self.set_reset_btn_state()

	# selected_files property
	@GObject.Property(type=str, default="")
	def selected_files(self):
		filelist = []

		for i in range(self._gstore_selected_files.get_n_items()):
			gfile = self._gstore_selected_files.get_item(i)

			if gfile is not None: filelist.append(gfile.get_path())

		return(",".join(filelist))

	@selected_files.setter
	def selected_files(self, value):
		self._gstore_selected_files.remove_all()

		if value != "":
			for f in value.split(","):
				if f != "": self._gstore_selected_files.append(Gio.File.new_for_path(f))

		n_files = self._gstore_selected_files.get_n_items()

		if n_files == 0:
			self.label.set_text("(None)")
		else:
			if n_files == 1:
				gfile = self._gstore_selected_files.get_item(0)
				self.label.set_text(gfile.get_basename() if gfile is not None else "(None)")
			else:
				self.label.set_text(f"({n_files} files)")

		self.set_clear_btn_state()
		self.set_reset_btn_state()

		self.emit("files-changed")

	# Helper functions
	def set_clear_btn_state(self):
		self.clear_btn.set_sensitive(self._gstore_selected_files.get_n_items() != 0)

	def set_reset_btn_state(self):
		if self._gfile_default_file is None:
			self.reset_btn.set_sensitive(False)
		else:
			self.reset_btn.set_sensitive(self.default_file != self.selected_files)

	#-----------------------------------
	# Class widget variables
	#-----------------------------------
	image = Gtk.Template.Child()
	label = Gtk.Template.Child()
	file_btn = Gtk.Template.Child()
	clear_btn = Gtk.Template.Child()
	reset_btn = Gtk.Template.Child()

	#-----------------------------------
	# Init function
	#-----------------------------------
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self._gstore_selected_files = Gio.ListStore()

	#-----------------------------------
	# Signal handlers
	#-----------------------------------
	@Gtk.Template.Callback()
	def on_activate(self, button, group_cycling):
		self.file_btn.activate()

	@Gtk.Template.Callback()
	def on_file_btn_clicked(self, button):
		self.dialog = Gtk.FileChooserNative(title=self.title, transient_for=self.dialog_parent, action=Gtk.FileChooserAction.SELECT_FOLDER if self._folder_select == True else Gtk.FileChooserAction.OPEN)

		self.dialog.set_modal(True)

		self.dialog.set_select_multiple(self.multi_select)

		if self.file_filter is not None: self.dialog.add_filter(self.file_filter)

		if self._gstore_selected_files.get_n_items() != 0:
			self.dialog.set_file(self._gstore_selected_files.get_item(0))
		else:
			if self._gfile_default_folder is not None:
				self.dialog.set_current_folder(self._gfile_default_folder)

		if self._folder_select == True: self.dialog.set_accept_label("_Select")

		self.dialog.connect("response", self.on_dialog_response)

		self.dialog.show()

	def on_dialog_response(self, dialog, response):
		if response == Gtk.ResponseType.ACCEPT:
			gfiles = dialog.get_files()

			if gfiles is not None:
				filelist = []

				for i in range(gfiles.get_n_items()):
					gfile = gfiles.get_item(i)

					if gfile is not None: filelist.append(gfile.get_path())

				self.selected_files = ",".join(filelist)

		self.dialog = None

	@Gtk.Template.Callback()
	def on_clear_btn_clicked(self, button):
		self.selected_files = ""

	@Gtk.Template.Callback()
	def on_reset_btn_clicked(self, button):
		self.selected_files = self.default_file

	#-----------------------------------
	# Property helper functions
	#-----------------------------------
	def set_dialog_parent(self, value):
		self.dialog_parent = value

	def set_default_folder(self, value):
		if self.default_folder != value: self.default_folder = value
		
	def set_selected_files(self, value):
		if self.selected_files != value: self.selected_files = value

	def get_selected_files(self):
		return(self.selected_files)

	def set_default_file(self, value):
		if self.default_file != value: self.default_file = value

#------------------------------------------------------------------------------
#-- CLASS: PREFERENCESWINDOW
#------------------------------------------------------------------------------
@Gtk.Template(filename=os.path.join(ui_dir, "preferences.ui"))
class PreferencesWindow(Adw.PreferencesWindow):
	__gtype_name__ = "PreferencesWindow"

	#-----------------------------------
	# Class widget variables
	#-----------------------------------
	exec_btn = Gtk.Template.Child()
	iwaddir_btn = Gtk.Template.Child()
	pwaddir_btn = Gtk.Template.Child()
	texture_checkbtn = Gtk.Template.Child()
	object_checkbtn = Gtk.Template.Child()
	monster_checkbtn = Gtk.Template.Child()
	menu_checkbtn = Gtk.Template.Child()
	hud_checkbtn = Gtk.Template.Child()

	#-----------------------------------
	# Init function
	#-----------------------------------
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.exec_btn.set_dialog_parent(self)
		self.iwaddir_btn.set_dialog_parent(self)
		self.pwaddir_btn.set_dialog_parent(self)

#------------------------------------------------------------------------------
#-- CLASS: CHEATSWINDOW
#------------------------------------------------------------------------------
@Gtk.Template(filename=os.path.join(ui_dir, "cheats.ui"))
class CheatsWindow(Adw.PreferencesWindow):
	__gtype_name__ = "CheatsWindow"

	#-----------------------------------
	# Class widget variables
	#-----------------------------------
	switches_grid = Gtk.Template.Child()
	cheats_grid = Gtk.Template.Child()

	#-----------------------------------
	# Init function
	#-----------------------------------
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		doom_switches = {
			"Switch": "Description",
			"-fast": "Increases the speed and attack rate of\nmonsters. Requires the -warp parameter.",
			"-nomonsters": "Disable spawning of monsters. Requires\nthe -warp parameter.",
			"-nomusic": "Disable background music",
			"-nosfx": "Disable sound effects",
			"-nosound": "Disable music and sound effects",
			"-respawn": "Monsters return a few seconds after being\nkilled, like in Nightmare mode. Requires\nthe -warp parameter.",
			"-skill <s>": "Select difficulty level <s> (1 to 5). This\nparameter will warp to the first level of\nthe game (if no other -warp parameter\nis specified).",
			"-warp <m>\n-warp <e> <m>": "Start the game on level <m> (1 to 32).\nFor Ultimate Doom and Freedoom Phase\n1, both episode <e> (1 to 4) and map <m>\n(1 to 9) must be specified, separated by\na space."
		}

		doom_cheats = {
			"Cheat Code": "Effect",
			"IDBEHOLDA": "Automap",
			"IDBEHOLDI": "Temporary invisibility",
			"IDBEHOLDL": "Light amplification goggles",
			"IDBEHOLDR": "Radiation suit",
			"IDBEHOLDS": "Berserk pack",
			"IDBEHOLDV": "Temporary invulnerability",
			"IDCHOPPERS": "Chainsaw",
			"IDCLEV##": "Warp to episode #, map #",
			"IDCLIP": "No clipping (walk through objects)",
			"IDDQD": "God mode (invincibility)",
			"IDDT": "Display entire map and enemies (toggle)",
			"IDFA": "All weapons and 200% armor",
			"IDKFA": "All keys and weapons",
			"IDMYPOS": "Display location"
		}

		row = 0

		for switch in doom_switches:
			param_label = Gtk.Label(label=switch, halign=Gtk.Align.START)
			self.switches_grid.attach(param_label, 0, row, 1, 1)
			if row == 0: param_label.add_css_class("heading")
			else: param_label.set_selectable(True)

			desc_label = Gtk.Label(label=doom_switches[switch], halign=Gtk.Align.START)
			self.switches_grid.attach(desc_label, 1, row, 1, 1)
			if row == 0: desc_label.add_css_class("heading")

			row += 1

		row = 0

		for cheat in doom_cheats:
			cheat_label = Gtk.Label(label=cheat, halign=Gtk.Align.START)
			self.cheats_grid.attach(cheat_label, 0, row, 1, 1)
			if row == 0: cheat_label.add_css_class("heading")

			effect_label = Gtk.Label(label=doom_cheats[cheat], halign=Gtk.Align.START)
			self.cheats_grid.attach(effect_label, 1, row, 1, 1)
			if row == 0: effect_label.add_css_class("heading")

			row += 1

#------------------------------------------------------------------------------
#-- CLASS: MAINWINDOW
#------------------------------------------------------------------------------
@Gtk.Template(filename=os.path.join(ui_dir, "window.ui"))
class MainWindow(Adw.ApplicationWindow):
	__gtype_name__ = "MainWindow"

	#-----------------------------------
	# Class widget variables
	#-----------------------------------
	shortcut_window = Gtk.Template.Child()
	iwad_store = Gtk.Template.Child()
	iwad_combo = Gtk.Template.Child()
	pwad_btn = Gtk.Template.Child()
	params_expandrow = Gtk.Template.Child()
	params_entry = Gtk.Template.Child()
	launch_btn = Gtk.Template.Child()
	toast_overlay = Gtk.Template.Child()
	prefs_window = Gtk.Template.Child()
	cheats_window = Gtk.Template.Child()

	#-----------------------------------
	# Init function
	#-----------------------------------
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		# Shortcut window
		self.set_help_overlay(self.shortcut_window)
		app.set_accels_for_action("win.show-help-overlay", ["<ctrl>question"])

		# Actions
		action_list = [
			[ "reset-widgets", self.on_reset_widgets_action ],
			[ "show-preferences", self.on_show_preferences_action ],
			[ "show-cheats", self.on_show_cheats_action],
			[ "quit-app", self.on_quit_app_action ]
		]

		self.add_action_entries(action_list)

		app.set_accels_for_action("win.reset-widgets", ["<ctrl>r"])
		app.set_accels_for_action("win.show-preferences", ["<ctrl>comma"])
		app.set_accels_for_action("win.show-cheats", ["F1"])
		app.set_accels_for_action("win.quit-app", ["<ctrl>q"])

		# Widget initialization
		self.populate_iwad_combo(app.main_config["launcher"]["iwad"])

		self.pwad_btn.set_dialog_parent(self)
		self.pwad_btn.set_default_folder(app.main_config["paths"]["pwad_dir"])
		self.pwad_btn.set_selected_files(app.main_config["launcher"]["file"])

		enable_params = app.main_config["launcher"].getboolean("params_on")
		self.params_expandrow.set_enable_expansion(enable_params)
		self.params_expandrow.set_expanded(enable_params)

		self.params_entry.set_text(app.main_config["launcher"]["params"])

		self.set_focus(self.iwad_combo)

		# Preferences initialization
		self.prefs_window.set_transient_for(self)

		self.prefs_window.exec_btn.set_default_file(app.default_exec_file)
		self.prefs_window.exec_btn.set_selected_files(app.main_config["paths"]["exec_file"])

		self.prefs_window.iwaddir_btn.set_default_file(app.default_iwad_dir)
		self.prefs_window.iwaddir_btn.set_selected_files(app.main_config["paths"]["iwad_dir"])

		self.prefs_window.pwaddir_btn.set_default_file(app.default_pwad_dir)
		self.prefs_window.pwaddir_btn.set_selected_files(app.main_config["paths"]["pwad_dir"])

		self.prefs_window.texture_checkbtn.set_active(app.main_config["mods"].getboolean("textures"))
		self.prefs_window.object_checkbtn.set_active(app.main_config["mods"].getboolean("objects"))
		self.prefs_window.monster_checkbtn.set_active(app.main_config["mods"].getboolean("monsters"))
		self.prefs_window.menu_checkbtn.set_active(app.main_config["mods"].getboolean("menus"))
		self.prefs_window.hud_checkbtn.set_active(app.main_config["mods"].getboolean("hud"))

		# Help initialization
		self.cheats_window.set_transient_for(self)

	# Add IWADs to combo
	def populate_iwad_combo(self, iwad_selected):
		if iwad_selected is None: iwad_selected = ""

		self.iwad_store.set_sort_column_id(Gtk.TREE_SORTABLE_UNSORTED_SORT_COLUMN_ID, Gtk.SortType.ASCENDING)

		self.iwad_store.clear()

		with os.scandir(app.main_config["paths"]["iwad_dir"]) as filelist:
			for f in filelist:
				iwad_lc = f.name.lower()

				if iwad_lc in app.doom_iwads:
					self.iwad_store.insert_with_values(-1, [0, 1], [app.doom_iwads[iwad_lc]["name"], iwad_lc])

		self.iwad_store.set_sort_column_id(0, Gtk.SortType.ASCENDING)

		if self.iwad_combo.set_active_id(iwad_selected) == False:
			self.iwad_combo.set_active(0)

		self.launch_btn.set_sensitive(self.iwad_combo.get_active_id() is not None)

	#-----------------------------------
	# Action handlers
	#-----------------------------------
	def on_reset_widgets_action(self, action, param, user_data):
		self.iwad_combo.set_active(0)
		self.pwad_btn.set_selected_files("")
		self.params_entry.set_text("")
		self.params_expandrow.set_enable_expansion(False)

	def on_show_preferences_action(self, action, param, user_data):
		self.prefs_window.show()

	def on_show_cheats_action(self, action, param, user_data):
		self.cheats_window.show()

	def on_quit_app_action(self, action, param, user_data):
		self.close()

	#-----------------------------------
	# Signal handlers
	#-----------------------------------
	@Gtk.Template.Callback()
	def on_iwad_combo_changed(self, combo):
		iwad_selected = combo.get_active_id()

		app.main_config["launcher"]["iwad"] = iwad_selected if iwad_selected is not None else ""

	@Gtk.Template.Callback()
	def on_pwad_btn_files_changed(self, button):
		app.main_config["launcher"]["file"] = button.get_selected_files()
		pass

	@Gtk.Template.Callback()
	def on_params_row_enabled(self, exprow, prop_name):
		app.main_config["launcher"]["params_on"] = str(exprow.get_enable_expansion() and app.main_config["launcher"]["params"] != "")

	@Gtk.Template.Callback()
	def on_params_entry_changed(self, entry):
		app.main_config["launcher"]["params"] = entry.get_text()

		app.main_config["launcher"]["params_on"] = str(self.params_expandrow.get_enable_expansion() and app.main_config["launcher"]["params"] != "")

	@Gtk.Template.Callback()
	def on_params_entry_clear(self, entry, icon):
		self.params_entry.set_text("")

	@Gtk.Template.Callback()
	def on_launch_btn_clicked(self, button):
		self.set_sensitive(False)

		if self.launch_zandronum() == True: self.close()
		else: self.set_sensitive(True)

	@Gtk.Template.Callback()
	def on_prefs_window_close(self, window):
		app.main_config["paths"]["exec_file"] = self.prefs_window.exec_btn.get_selected_files()

		iwad_dir = self.prefs_window.iwaddir_btn.get_selected_files()

		if iwad_dir != app.main_config["paths"]["iwad_dir"]:
			app.main_config["paths"]["iwad_dir"] = iwad_dir
			self.populate_iwad_combo(self.iwad_combo.get_active_id())

		pwad_dir = self.prefs_window.pwaddir_btn.get_selected_files()

		if pwad_dir != app.main_config["paths"]["pwad_dir"]:
			app.main_config["paths"]["pwad_dir"] = pwad_dir
			self.pwad_btn.set_default_folder(pwad_dir)

		app.main_config["mods"]["textures"] = str(self.prefs_window.texture_checkbtn.get_active())
		app.main_config["mods"]["objects"] = str(self.prefs_window.object_checkbtn.get_active())
		app.main_config["mods"]["monsters"] = str(self.prefs_window.monster_checkbtn.get_active())
		app.main_config["mods"]["menus"] = str(self.prefs_window.menu_checkbtn.get_active())
		app.main_config["mods"]["hud"] = str(self.prefs_window.hud_checkbtn.get_active())

	#-----------------------------------
	# Launch Zandronum function
	#-----------------------------------
	def launch_zandronum(self):
		# Return with error if Zandronum executable does not exist
		if os.path.exists(app.main_config["paths"]["exec_file"]) == False:
			self.show_toast('ERROR: Zandronum executable not found')
			return(False)

		# Initialize Zandronum command line with executable
		cmdline = app.main_config["paths"]["exec_file"]

		# Return with error if IWAD name is empty
		if app.main_config["launcher"]["iwad"] == "":
			self.show_toast('ERROR: No IWAD file specified')
			return(False)

		# Return with error if IWAD file does not exist
		iwad_file = os.path.join(app.main_config["paths"]["iwad_dir"], app.main_config["launcher"]["iwad"])

		if os.path.exists(iwad_file) == False:
			self.show_toast(f'ERROR: IWAD file {app.main_config["launcher"]["iwad"]} not found')
			return(False)

		# Add IWAD file
		cmdline += f' -iwad "{iwad_file}"'

		# Add hi-res graphics if options are true
		mod_dict = app.doom_iwads[app.main_config["launcher"]["iwad"]]["mods"]

		for key, modlist in mod_dict.items():
			if app.main_config["mods"].getboolean(key) == True:
				for mod_name in modlist:
					if mod_name != "":
						mod_file = os.path.join(app.mod_dir, mod_name)

						if os.path.exists(mod_file): cmdline += f' -file "{mod_file}"'

		# Add PWAD files if present
		for wad_file in app.main_config["launcher"]["file"].split(","):
			if wad_file != "" and os.path.exists(wad_file):
				cmdline += f' -file "{wad_file}"'

		# Add extra params if present and enabled
		if app.main_config["launcher"].getboolean("params_on") == True and app.main_config["launcher"]["params"] != "":
			cmdline += f' {app.main_config["launcher"]["params"]}'

		# Launch Zandronum
		subprocess.Popen(shlex.split(cmdline))

		return(True)

	def show_toast(self, toast_title):
		self.toast_overlay.add_toast(Adw.Toast(title=toast_title, priority=Adw.ToastPriority.HIGH))

#------------------------------------------------------------------------------
#-- CLASS: LAUNCHERAPP
#------------------------------------------------------------------------------
class LauncherApp(Adw.Application):
	#-----------------------------------
	# Init function
	#-----------------------------------
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.connect("startup", self.on_startup)
		self.connect("activate", self.on_activate)
		self.connect("shutdown", self.on_shutdown)

	#-----------------------------------
	# Signal handlers
	#-----------------------------------
	def on_startup(self, app):
		# Config dir
		self.config_dir = os.path.join(os.getenv("HOME"), ".config/zandronum")

		if os.path.exists(self.config_dir) == False:
			os.makedirs(self.config_dir)

		# Zandronum INI file
		self.zandronum_ini_file = os.path.join(self.config_dir, "zandronum.ini")

		if os.path.exists(self.zandronum_ini_file) == False:
			zandronum_ini_src = os.path.join(app_dir, "config/zandronum.ini")

			shutil.copyfile(zandronum_ini_src, zandronum_ini_file)

		# Default paths
		self.mod_dir = os.path.join(app_dir, "mods")

		self.default_exec_file = "/usr/bin/zandronum"
		self.default_iwad_dir = os.path.join(app_dir, "iwads")
		self.default_pwad_dir = os.path.join(self.config_dir, "WADs")

		# Read IWAD json file
		with open(os.path.join(app_dir, "iwads.json"), "r") as iwad_file:
			self.doom_iwads = json.load(iwad_file)

		# Parse configuration file
		self.launcher_config_file = os.path.join(self.config_dir, "launcher.conf")

		self.main_config = configparser.ConfigParser()

		default_config = {
			"launcher": {
				"iwad": "",
				"file": "",
				"params": "",
				"params_on": "False"
			},
			"paths": {
				"exec_file": self.default_exec_file,
				"iwad_dir": self.default_iwad_dir,
				"pwad_dir": self.default_pwad_dir
			},
			"mods": {
				"textures": "True",
				"objects": "True",
				"monsters": "True",
				"menus": "True",
				"hud": "True"
			}
		}

		self.main_config.read_dict(default_config)

		self.main_config.read(self.launcher_config_file)

		for section in self.main_config.sections():
			for key, value in self.main_config.items(section):
				if value == "" and default_config[section][key] != "":
					self.main_config[section][key] = default_config[section][key]

	def on_activate(self, app):
		self.main_window = MainWindow(application=app)
		self.main_window.present()

	def on_shutdown(self, app):
		# Write configuration file
		with open(self.launcher_config_file, "w") as configfile:
			self.main_config.write(configfile)

#------------------------------------------------------------------------------
#-- MAIN APP
#------------------------------------------------------------------------------
app = LauncherApp(application_id="com.github.zandronumlauncher")
app.run(sys.argv)
