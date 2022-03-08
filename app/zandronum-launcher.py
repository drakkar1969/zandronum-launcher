#!/usr/bin/env python

import gi, sys, os, configparser, subprocess, shlex
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio, GObject, Gdk

# IWAD filenames/descriptions/mod files
doom_iwads = {
	"doom.wad": {
		"name": "The Ultimate Doom",
		"mods": {
			"textures": ["hires-doom-a.pk3", "hires-doom-b.pk3"],
			"objects": ["objects.pk3"],
			"monsters": ["monsters.pk3"],
			"menus": ["jfo-udoom.pk3"],
			"hud": ["hud-stuff.pk3"]
		}
	},
	"doom2.wad": {
		"name": "Doom II: Hell on Earth",
		"mods": {
			"textures": ["hires-doom-a.pk3", "hires-doom-b.pk3", "hires-doom2.pk3"],
			"objects": ["objects.pk3"],
			"monsters": ["monsters.pk3"],
			"menus": ["jfo-doom2.pk3"],
			"hud": ["hud-stuff.pk3"]
		}
	},
	"plutonia.wad": {
		"name": "Final Doom - The Plutonia Experiment",
		"mods": {
			"textures": ["hires-doom-a.pk3", "hires-doom-b.pk3", "hires-doom2.pk3", "hires-plut.pk3"],
			"objects": ["objects.pk3"],
			"monsters": ["monsters.pk3"],
			"menus": ["jfo-plut.pk3"],
			"hud": ["hud-stuff.pk3"]
		}
	},
	"tnt.wad": {
		"name": "Final Doom - TNT: Evilution",
		"mods": {
			"textures": ["hires-doom-a.pk3", "hires-doom-b.pk3", "hires-doom2.pk3", "hires-tnt.pk3"],
			"objects": ["objects.pk3"],
			"monsters": ["monsters.pk3"],
			"menus": ["jfo-tnt.pk3"],
			"hud": ["hud-stuff.pk3"]
		}
	},
	"freedoom1.wad": {
		"name": "Freedoom Phase 1",
		"mods": {}
	},
	"freedoom2.wad": {
		"name": "Freedoom Phase 2",
		"mods": {}
	},
	"heretic.wad": {
		"name": "Heretic",
		"mods": {
			"textures": ["hires-heretic.pk3"],
		}
	},
	"hexen.wad": {
		"name": "Hexen",
		"mods": {
			"textures": ["hires-hexen.pk3"],
		}
	},
}

# Global path variables
app_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
ui_dir = os.path.join(app_dir, "ui")

@Gtk.Template(filename=os.path.join(ui_dir, "filedialogbutton.ui"))
class FileDialogButton(Gtk.Box):
	__gtype_name__ = "FileDialogButton"

	__gsignals__ = {
		"file-changed": (GObject.SignalFlags.RUN_FIRST, None, ())
	}

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
	dlg_parent = GObject.Property(type=Gtk.Window, default=None, flags=GObject.ParamFlags.READWRITE)
	dlg_filter = GObject.Property(type=Gtk.FileFilter, default=None, flags=GObject.ParamFlags.READWRITE)

	# Class widget variables
	image = Gtk.Template.Child()
	label = Gtk.Template.Child()
	file_btn = Gtk.Template.Child()
	clear_btn = Gtk.Template.Child()
	reset_btn = Gtk.Template.Child()

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

		self.label.set_text(self.selected_file.get_basename() if self.selected_file is not None else "(None)")

		self.clear_btn.set_visible(self.can_clear)
		self.reset_btn.set_visible(self.can_reset)

		if self.can_clear == True: self.set_clear_btn_state()
		if self.can_reset == True: self.set_reset_btn_state()

	@Gtk.Template.Callback()
	def on_activate(self, button, group_cycling):
		self.file_btn.activate()

	@Gtk.Template.Callback()
	def on_icon_name_notify(self, button, prop_name):
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
	def on_can_clear_notify(self, button, prop_name):
		self.clear_btn.set_visible(self.can_clear)

		if self.can_clear == True: self.set_clear_btn_state()

	@Gtk.Template.Callback()
	def on_can_reset_notify(self, button, prop_name):
		self.reset_btn.set_visible(self.can_reset)

		if self.can_reset == True: self.set_reset_btn_state()

	@Gtk.Template.Callback()
	def on_selected_file_notify(self, button, prop_name):
		self.label.set_text(self.selected_file.get_basename() if self.selected_file is not None else "(None)")

		if self.can_clear == True: self.set_clear_btn_state()
		if self.can_reset == True: self.set_reset_btn_state()

		self.emit("file-changed")

	@Gtk.Template.Callback()
	def on_default_file_notify(self, button, prop_name):
		if self.can_reset == True: self.set_reset_btn_state()

	@Gtk.Template.Callback()
	def on_file_btn_clicked(self, button):
		self.dialog = Gtk.FileChooserNative(title=self.dlg_title, transient_for=self.dlg_parent, action=Gtk.FileChooserAction.SELECT_FOLDER if self.folder_select == True else Gtk.FileChooserAction.OPEN)

		self.dialog.set_modal(True)

		if self.dlg_filter is not None:
			self.dialog.add_filter(self.dlg_filter)

		if self.selected_file is not None:
			self.dialog.set_file(self.selected_file)
		else:
			if self.default_folder is not None:
				self.dialog.set_current_folder(self.default_folder)

		self.dialog.connect("response", self.on_dialog_response)

		self.dialog.show()

	def on_dialog_response(self, dialog, response):
		if response == Gtk.ResponseType.ACCEPT:
			new_file = dialog.get_file()

			if self.selected_file is None: self.selected_file = new_file
			else:
				if not self.selected_file.equal(new_file): self.selected_file = new_file

		self.dialog = None

	@Gtk.Template.Callback()
	def on_clear_btn_clicked(self, button):
		self.selected_file = None

	@Gtk.Template.Callback()
	def on_reset_btn_clicked(self, button):
		self.selected_file = self.default_file

	def set_dialog_parent(self, parent):
		self.dlg_parent = parent

	def set_default_folder(self, folder_path):
		self.default_folder = Gio.File.new_for_path(folder_path) if folder_path != "" else None
		
	def set_selected_file(self, file_path):
		if file_path == "":
			if self.selected_file is not None: self.selected_file = None 
		else:
			new_file = Gio.File.new_for_path(file_path)

			if self.selected_file is None: self.selected_file = new_file
			else:
				if not self.selected_file.equal(new_file): self.selected_file = new_file 

	def get_selected_file(self):
		return(self.selected_file.get_path() if self.selected_file is not None else "")

	def set_default_file(self, file_path):
		self.default_file = Gio.File.new_for_path(file_path) if file_path != "" else None

@Gtk.Template(filename=os.path.join(ui_dir, "preferences.ui"))
class PreferencesWindow(Adw.PreferencesWindow):
	__gtype_name__ = "PreferencesWindow"

	# Class widget variables
	exec_btn = Gtk.Template.Child()
	iwaddir_btn = Gtk.Template.Child()
	pwaddir_btn = Gtk.Template.Child()
	texture_switch = Gtk.Template.Child()
	object_switch = Gtk.Template.Child()
	monster_switch = Gtk.Template.Child()
	menu_switch = Gtk.Template.Child()
	hud_switch = Gtk.Template.Child()

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.exec_btn.set_dialog_parent(self)
		self.iwaddir_btn.set_dialog_parent(self)
		self.pwaddir_btn.set_dialog_parent(self)

@Gtk.Template(filename=os.path.join(ui_dir, "cheats.ui"))
class CheatsWindow(Adw.PreferencesWindow):
	__gtype_name__ = "CheatsWindow"

	switches_grid = Gtk.Template.Child()
	cheats_grid = Gtk.Template.Child()

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		doom_switches = {
			"Switch": "Description",
			"-fast": "Increases the speed and attack rate\nof monsters. Requires the -warp\nparameter.",
			"-nomonsters": "Disable spawning of monsters. Requires\nthe -warp parameter.",
			"-nomusic": "Disable background music",
			"-nosfx": "Disable sound effects",
			"-nosound": "Disable music and sound effects",
			"-respawn": "Monsters return a few seconds after\nbeing killed, like in Nightmare mode.\nRequires the -warp parameter.",
			"-skill <s>": "Select difficulty level <s> (1 to 5).\nThis parameter will warp to the first\nlevel of the game (if no other -warp\nparameter is specified).",
			"-warp <m>\n-warp <e> <m>": "Start the game on level <m> (1 to 32).\nFor Ultimate Doom and Freedoom Phase\n1 both episode <e> (1 to 4) and map <m>\n(1 to 9) must be specified, separated by\na space."
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
			"IDMUS##": "Change music (episode #, map #)",
			"IDMYPOS": "Display location"
		}

		row = 0

		for switch in doom_switches:
			param_label = Gtk.Label(label=switch, halign=Gtk.Align.START)
			self.switches_grid.attach(param_label, 0, row, 1, 1)
			if row == 0: param_label.add_css_class("heading")

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

@Gtk.Template(filename=os.path.join(ui_dir, "window.ui"))
class MainWindow(Adw.ApplicationWindow):
	__gtype_name__ = "MainWindow"

	# Class widget variables
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

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		# Shortcut window
		self.set_help_overlay(self.shortcut_window)
		app.set_accels_for_action("win.show-help-overlay", ["<ctrl>question"])

		# Actions
		app_entries = [
			[ "reset-widgets", self.on_reset_widgets_action ],
			[ "show-preferences", self.on_show_preferences_action ],
			[ "show-cheats", self.on_show_cheats_action],
			[ "quit-app", self.on_quit_app_action ]
		]

		self.add_action_entries(app_entries)

		app.set_accels_for_action("win.reset-widgets", ["<ctrl>r"])
		app.set_accels_for_action("win.show-preferences", ["<ctrl>comma"])
		app.set_accels_for_action("win.show-cheats", ["F1"])
		app.set_accels_for_action("win.quit-app", ["<ctrl>q"])

		# Widget initialization
		self.populate_iwad_combo(app.main_config["launcher"]["iwad"])

		self.pwad_btn.set_dialog_parent(self)
		self.pwad_btn.set_default_folder(app.main_config["paths"]["pwad_dir"])
		self.pwad_btn.set_selected_file(app.main_config["launcher"]["file"])

		enable_params = app.main_config["launcher"].getboolean("params_on")
		self.params_expandrow.set_enable_expansion(enable_params)
		self.params_expandrow.set_expanded(enable_params)

		self.params_entry.set_text(app.main_config["launcher"]["params"])

		self.set_focus(self.iwad_combo)

		# Preferences initialization
		self.prefs_window.set_transient_for(self)

		self.prefs_window.exec_btn.set_default_file(app.default_exec_file)
		self.prefs_window.exec_btn.set_selected_file(app.main_config["paths"]["exec_file"])

		self.prefs_window.iwaddir_btn.set_default_file(app.default_iwad_dir)
		self.prefs_window.iwaddir_btn.set_selected_file(app.main_config["paths"]["iwad_dir"])

		self.prefs_window.pwaddir_btn.set_default_file(app.default_pwad_dir)
		self.prefs_window.pwaddir_btn.set_selected_file(app.main_config["paths"]["pwad_dir"])

		self.prefs_window.texture_switch.set_active(app.main_config["mods"].getboolean("textures"))
		self.prefs_window.object_switch.set_active(app.main_config["mods"].getboolean("objects"))
		self.prefs_window.monster_switch.set_active(app.main_config["mods"].getboolean("monsters"))
		self.prefs_window.menu_switch.set_active(app.main_config["mods"].getboolean("menus"))
		self.prefs_window.hud_switch.set_active(app.main_config["mods"].getboolean("hud"))

		# Help initialization
		self.cheats_window.set_transient_for(self)

	def populate_iwad_combo(self, iwad_selected):
		if iwad_selected is None: iwad_selected = ""

		self.iwad_store.set_sort_column_id(Gtk.TREE_SORTABLE_UNSORTED_SORT_COLUMN_ID, Gtk.SortType.ASCENDING)

		self.iwad_store.clear()

		with os.scandir(app.main_config["paths"]["iwad_dir"]) as filelist:
			for f in filelist:
				iwad_lc = f.name.lower()

				if iwad_lc in doom_iwads:
					self.iwad_store.insert_with_values(-1, [0, 1], [doom_iwads[iwad_lc]["name"], iwad_lc])

		self.iwad_store.set_sort_column_id(0, Gtk.SortType.ASCENDING)

		if self.iwad_combo.set_active_id(iwad_selected) == False:
			self.iwad_combo.set_active(0)

		self.launch_btn.set_sensitive(self.iwad_combo.get_active_id() is not None)

	@Gtk.Template.Callback()
	def on_iwad_combo_changed(self, combo):
		iwad_selected = combo.get_active_id()

		app.main_config["launcher"]["iwad"] = iwad_selected if iwad_selected is not None else ""

	@Gtk.Template.Callback()
	def on_pwad_btn_file_changed(self, button):
		app.main_config["launcher"]["file"] = button.get_selected_file()

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

	def on_quit_app_action(self, action, param, user_data):
		self.close()

	def on_reset_widgets_action(self, action, param, user_data):
		self.iwad_combo.set_active(0)
		self.pwad_btn.set_selected_file("")
		self.params_entry.set_text("")
		self.params_expandrow.set_enable_expansion(False)

	def on_show_cheats_action(self, action, param, user_data):
		self.cheats_window.show()

	def on_show_preferences_action(self, action, param, user_data):
		self.prefs_window.show()

	@Gtk.Template.Callback()
	def on_prefs_window_close(self, window):
		app.main_config["paths"]["exec_file"] = self.prefs_window.exec_btn.get_selected_file()

		iwad_dir = self.prefs_window.iwaddir_btn.get_selected_file()

		if iwad_dir != app.main_config["paths"]["iwad_dir"]:
			app.main_config["paths"]["iwad_dir"] = iwad_dir
			self.populate_iwad_combo(self.iwad_combo.get_active_id())

		pwad_dir = self.prefs_window.pwaddir_btn.get_selected_file()

		app.main_config["paths"]["pwad_dir"] = pwad_dir
		self.pwad_btn.set_default_folder(pwad_dir)

		app.main_config["mods"]["textures"] = str(self.prefs_window.texture_switch.get_active())
		app.main_config["mods"]["objects"] = str(self.prefs_window.object_switch.get_active())
		app.main_config["mods"]["monsters"] = str(self.prefs_window.monster_switch.get_active())
		app.main_config["mods"]["menus"] = str(self.prefs_window.menu_switch.get_active())
		app.main_config["mods"]["hud"] = str(self.prefs_window.hud_switch.get_active())

	@Gtk.Template.Callback()
	def on_window_close(self, window):
		self.prefs_window.destroy()
		self.cheats_window.destroy()

	def launch_zandronum(self):
		# Return with error if Zandronum executable does not exist
		if os.path.exists(app.main_config["paths"]["exec_file"]) == False:
			self.show_toast("ERROR: Zandronum executable not found")
			return(False)

		# Initialize Zandronum command line with executable
		cmdline = app.main_config["paths"]["exec_file"]

		# Return with error if IWAD name is empty
		if app.main_config["launcher"]["iwad"] == "":
			self.show_toast("ERROR: No IWAD file specified")
			return(False)

		iwad_file = os.path.join(app.main_config["paths"]["iwad_dir"], app.main_config["launcher"]["iwad"])

		# Return with error if IWAD file does not exist
		if os.path.exists(iwad_file) == False:
			self.show_toast("ERROR: IWAD file {:s} not found".format(app.main_config["launcher"]["iwad"]))
			return(False)

		# Add IWAD file
		cmdline += ' -iwad "{:s}"'.format(iwad_file)

		# Add hi-res graphics if options are true
		mod_dict = doom_iwads[app.main_config["launcher"]["iwad"]]["mods"]

		for mod in mod_dict:
			if app.main_config["mods"].getboolean(mod) == True:
				for mod_name in mod_dict[mod]:
					if mod_name != "":
						mod_file = os.path.join(app.mod_dir, mod_name)

						if os.path.exists(mod_file): cmdline += ' -file "{:s}"'.format(mod_file)

		# Add PWAD file if present
		if app.main_config["launcher"]["file"] != "" and os.path.exists(app.main_config["launcher"]["file"]):
			cmdline += ' -file "{:s}"'.format(app.main_config["launcher"]["file"])

		# Add extra params if present and enabled
		if app.main_config["launcher"].getboolean("params_on") == True and app.main_config["launcher"]["params"] != "":
				cmdline += ' {:s}'.format(app.main_config["launcher"]["params"])

		# Launch Zandronum
		subprocess.Popen(shlex.split(cmdline))

		return(True)

	def show_toast(self, toast_title):
		self.toast_overlay.add_toast(Adw.Toast(title=toast_title, priority=Adw.ToastPriority.HIGH))

class LauncherApp(Adw.Application):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.connect("startup", self.on_startup)
		self.connect("activate", self.on_activate)
		self.connect("shutdown", self.on_shutdown)

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

		# Parse configuration file
		self.launcher_config_file = os.path.join(self.config_dir, "launcher.conf")

		self.main_config = configparser.ConfigParser()

		self.main_config.read_dict({
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
				"monsters": True,
				"menus": "True",
				"hud": "True"
			}
		})

		self.main_config.read(self.launcher_config_file)

	def on_activate(self, app):
		self.main_window = MainWindow(application=app)
		self.main_window.present()

	def on_shutdown(self, app):
		# Write configuration file
		with open(self.launcher_config_file, "w") as configfile:
			self.main_config.write(configfile)

		# Destroy main window
		app.main_window.destroy()

# Main app
app = LauncherApp(application_id="com.github.zandronumlauncher")
app.run(sys.argv)
