#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gi, os, sys, configparser, subprocess
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk

#-------------------------------------------------------------------------
# GLOBAL VARIABLES
#-------------------------------------------------------------------------
# Config dir
config_dir = "{:s}/.config/zandronum".format(os.getenv('HOME'))

# Launcher config file
launcher_config_file = "{:s}/launcher.conf".format(config_dir)

# Allowed IWAD filenames/descriptions
doom_iwads = {
	"doom.wad": "The Ultimate Doom",
	"doom2.wad": "Doom II: Hell on Earth",
	"plutonia.wad": "Final Doom - The Plutonia Experiment",
	"tnt.wad": "Final Doom - TNT: Evilution",
	"freedoom1.wad": "Freedoom Phase 1",
	"freedoom2.wad": "Freedoom Phase 2",
	"freedm.wad": "Freedoom Deathmatch"
}
found_iwads = {}

# File chooser filters
file_filters = {
	"pwad": {
		"name": "PWAD files (*.wad, *.pk3, *.pk7, *.zip, *.7z)",
		"patterns": ["*.wad", "*.WAD", "*.pk3", "*.PK3", "*.pk7", "*.PK7", "*.zip", "*.ZIP", "*.7z", "*.7Z"]
	},
	"ini": {
		"name": "INI files (*.ini)",
		"patterns": ["*.ini", "*.INI"]
	}
}

#-------------------------------------------------------------------------
# FUNCTION: parse_launcher_conf
#-------------------------------------------------------------------------
def parse_launcher_conf(config_file):
	parser = configparser.ConfigParser()
	parser.read(config_file)

	params = {}
	lparams = {}
	zparams = {}

	lparams["iwad"] = parser.get("launcher", "iwad", fallback="")
	lparams["file"] = parser.get("launcher", "file", fallback="")
	lparams["warp"] = parser.get("launcher", "warp", fallback="")
	lparams["params"] = parser.get("launcher", "params", fallback="")

	zparams["ini"] = parser.get("zandronum", "ini", fallback="{:s}/zandronum.ini".format(config_dir))
	zparams["exec"] = parser.get("zandronum", "exec", fallback="/usr/bin/zandronum")

	params["launcher"] = lparams
	params["zandronum"] = zparams

	return(params)

#-------------------------------------------------------------------------
# FUNCTION: parse_zandronum_ini
#-------------------------------------------------------------------------
def parse_zandronum_ini(ini_file):
	parser = configparser.ConfigParser(strict=False)
	parser.read(ini_file)

	dirs = {}

	dirs["iwad_dir"] = parser.get("IWADSearch.Directories", "Path", fallback="{:s}/IWADs".format(config_dir))
	dirs["pwad_dir"] = parser.get("FileSearch.Directories", "Path", fallback="{:s}/WADs".format(config_dir))

	return(dirs)

#-------------------------------------------------------------------------
# FUNCTION: set_file_filters
#-------------------------------------------------------------------------
def set_file_filters(widget, filters):
	file_filter = Gtk.FileFilter()
	file_filter.set_name(filters["name"])

	for filt in filters["patterns"]:
		file_filter.add_pattern(filt)

	widget.add_filter(file_filter)

#-------------------------------------------------------------------------
# FUNCTION: initialize_widgets
#-------------------------------------------------------------------------
def initialize_widgets():
	# Game combobox
	game_combo.remove_all()
	found_iwads.clear()

	game_index = 0

	if os.path.exists(zandronum_dirs["iwad_dir"]):
		iwads = os.listdir(zandronum_dirs["iwad_dir"])
		iwads.sort()

		for i in range(len(iwads)):
			iwad_lc = iwads[i].lower()

			if iwad_lc in doom_iwads:
				found_iwads[iwads[i]] = doom_iwads[iwad_lc]
				game_combo.append_text(doom_iwads[iwad_lc])

			if iwad_lc == main_params["launcher"]["iwad"]:
				game_index = i

	try:
		game_combo.set_active(game_index)
	except:
		game_combo.set_active(-1)

	# Launch button
	launch_btn.set_sensitive(True if len(found_iwads) > 0 else False)

	# PWAD file button
	pwad_btn.unselect_all()

	pwad_btn.set_current_folder(zandronum_dirs["pwad_dir"])
	pwad_btn.set_filename(main_params["launcher"]["file"])

	# Entries
	warp_entry.set_text(main_params["launcher"]["warp"])
	params_entry.set_text(main_params["launcher"]["params"])

#-------------------------------------------------------------------------
# FUNCTION: reset_widgets
#-------------------------------------------------------------------------
def reset_widgets():
	try:
		game_combo.set_active(0)
	except:
		game_combo.set_active(-1)
	pwad_btn.unselect_all()
	warp_entry.set_text("")
	params_entry.set_text("")

#-------------------------------------------------------------------------
# CLASS: EventHandlers
#-------------------------------------------------------------------------
class EventHandlers:
	def on_window_main_key_press_event(self, widget, event):
		# Close window if ESC key pressed
		if event.keyval == Gdk.KEY_Escape:
			main_window.destroy()
		# Launch Zandronum if ENTER key pressed
		if event.keyval == Gdk.KEY_Return or event.keyval == Gdk.KEY_KP_Enter:
			self.on_btn_launch_clicked(None)

	def on_menu_clearpwad_clicked(self, button):
		pwad_btn.unselect_all()

	def on_menu_reset_clicked(self, button):
		reset_widgets()

	def on_menu_inifile_clicked(self, button):
		global main_params
		global zandronum_dirs

		prefs_inifile_btn.set_filename(main_params["zandronum"]["ini"])
		prefs_execfile_btn.set_filename(main_params["zandronum"]["exec"])

		dlg_response = prefs_dialog.run()

		if(dlg_response == Gtk.ResponseType.OK):
			zandronum_ini = prefs_inifile_btn.get_filename()

			if (zandronum_ini is not None) and (zandronum_ini != main_params["zandronum"]["ini"]):
				main_params["zandronum"]["ini"] = zandronum_ini

				zandronum_dirs = parse_zandronum_ini(zandronum_ini)

				initialize_widgets()
				reset_widgets()

			zandronum_exec = prefs_execfile_btn.get_filename()

			if (zandronum_exec is not None) and (zandronum_exec != main_params["zandronum"]["exec"]):
				main_params["zandronum"]["exec"] = zandronum_exec

		prefs_dialog.hide()

	def on_btn_launch_clicked(self, button):
		global zandronum_launch
		global zandronum_params

		# Initialize Zandronum launch params
		zandronum_params = [main_params["zandronum"]["exec"]]

		# Get game combox selection
		game_text = game_combo.get_active_text()
		try:
			game_file = list(found_iwads.keys())[list(found_iwads.values()).index(game_text)]
			zandronum_params.extend(["-iwad", zandronum_dirs["iwad_dir"] + game_file])
		except:
			game_file = ""

		# Get PWAD file
		pwad_file = pwad_btn.get_filename()
		if pwad_file is None:
			pwad_file = ""
		else:
			zandronum_params.extend(["-file", pwad_file])

		# Get warp level
		warp_level = warp_entry.get_text()
		if warp_level != "":
			zandronum_params.append("-warp")
			zandronum_params.extend(list(warp_level.split(" ")))

		# Get extra params
		extra_params = params_entry.get_text()
		if extra_params != "":
			zandronum_params.extend(list(extra_params.split(" ")))

		# Update launcher params
		main_params["launcher"] = {
			"iwad": game_file.lower(),
			"file": pwad_file,
			"warp": warp_level,
			"params": extra_params
		}

		# Close window
		main_window.destroy()

		# Set flag to launch Zandronum
		zandronum_launch = True

#-------------------------------------------------------------------------
# MAIN SCRIPT
#-------------------------------------------------------------------------
# Parse configuration files
main_params = parse_launcher_conf(launcher_config_file)
zandronum_dirs = parse_zandronum_ini(main_params["zandronum"]["ini"])

# Set Zandronum launch variable
zandronum_launch = False

# Set application name (match .desktop name)
GLib.set_prgname("Zandronum-Launcher")

# Create dialog with glade template
builder = Gtk.Builder()
builder.add_from_file("{:s}/zandronum-launcher.ui".format(os.path.abspath(os.path.dirname(sys.argv[0]))))
builder.connect_signals(EventHandlers())

# Get main window
main_window = builder.get_object("window_main")
main_window.connect("destroy", Gtk.main_quit)

# Get widgets
game_combo = builder.get_object("combo_game")
pwad_btn = builder.get_object("btn_pwad")
warp_entry = builder.get_object("entry_warp")
params_entry = builder.get_object("entry_params")
launch_btn = builder.get_object("btn_launch")

# Get dialogs
prefs_dialog = builder.get_object("dialog_prefs")
prefs_inifile_btn = builder.get_object("btn_inifile")
prefs_execfile_btn = builder.get_object("btn_execfile")

# Set file chooser filters
set_file_filters(widget=pwad_btn, filters=file_filters["pwad"])
set_file_filters(widget=prefs_inifile_btn, filters=file_filters["ini"])

# Initialize widgets
initialize_widgets()

# Show main window
main_window.show_all()
Gtk.main()

# Destroy dialogs
prefs_dialog.destroy()

# Save preferences
parser = configparser.ConfigParser()
parser.read_dict(main_params)

with open(launcher_config_file, 'w') as configfile:
	parser.write(configfile)

# Launch Zandronum
if zandronum_launch == True:
	zandronum_output = subprocess.run(zandronum_params)
