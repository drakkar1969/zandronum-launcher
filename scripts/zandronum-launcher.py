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
	"doom.wad": "The Ultimate DOOM",
	"doom2.wad": "DOOM 2: Hell on Earth",
	"plutonia.wad": "Final Doom: Plutonia Experiment",
	"tnt.wad": "Final Doom: TNT - Evilution",
	"freedoom1.wad": "FreeDOOM: Phase 1",
	"freedoom2.wad": "FreeDOOM: Phase 2"
}
found_iwads = {}

# File chooser filters
file_filters = {
	"pwad": ["*.wad", "*.WAD", "*.pk3", "*.PK3", "*.pk7", "*.PK7", "*.zip", "*.ZIP", "*.7z", "*.7Z"],
	"ini": ["*.ini", "*.INI"],
	"all": ["*.*"]
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
# FUNCTION: initialize_widgets
#-------------------------------------------------------------------------
def initialize_widgets():
	# Game combobox
	game_combo.remove_all()
	found_iwads.clear()

	game_index = 0

	iwads = os.listdir(zandronum_dirs["iwad_dir"])
	iwads.sort()

	for i in range(len(iwads)):
		iwad_lc = iwads[i].lower()
		if iwad_lc.endswith(".wad") and iwad_lc in doom_iwads:
			found_iwads[iwads[i]] = doom_iwads[iwad_lc]
			game_combo.append_text(doom_iwads[iwad_lc])
		if iwad_lc == launcher_params["launcher"]["iwad"]:
			game_index = i

	try:
		game_combo.set_active(game_index)
	except:
		game_combo.set_active(-1)

	# PWAD file button
	pwad_btn.unselect_all()

	pwad_btn.set_current_folder(zandronum_dirs["pwad_dir"])
	pwad_btn.set_filename(launcher_params["launcher"]["file"])

	# Entries
	warp_entry.set_text(launcher_params["launcher"]["warp"])
	params_entry.set_text(launcher_params["launcher"]["params"])

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

	def on_menu_clearpwad_clicked(self, button):
		pwad_btn.unselect_all()

	def on_menu_reset_clicked(self, button):
		reset_widgets()

	def on_menu_inifile_clicked(self, button):
		global launcher_params
		global zandronum_dirs

		prefs_inifile_btn.set_filename(launcher_params["zandronum"]["ini"])
		prefs_execfile_btn.set_filename(launcher_params["zandronum"]["exec"])

		dlg_response = prefs_dialog.run()

		if(dlg_response == Gtk.ResponseType.OK):
			zandronum_ini = prefs_inifile_btn.get_filename()

			if (zandronum_ini is not None) and (zandronum_ini != launcher_params["zandronum"]["ini"]):
				launcher_params["zandronum"]["ini"] = zandronum_ini

				zandronum_dirs = parse_zandronum_ini(zandronum_ini)

				print(zandronum_dirs)

				initialize_widgets()
				reset_widgets()

			zandronum_exec = prefs_execfile_btn.get_filename()

			if (zandronum_exec is not None) and (zandronum_exec != launcher_params["zandronum"]["exec"]):
				launcher_params["zandronum"]["exec"] = zandronum_exec

		prefs_dialog.hide()

	def on_btn_launch_clicked(self, button):
		global zandronum_launch
		global zandronum_params

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

		# Write config file
		parser = configparser.ConfigParser()
		parser["launcher"] = {
			"iwad": game_file.lower(),
			"file": pwad_file,
			"warp": warp_level,
			"params": extra_params
		}

		parser["zandronum"] = {
			"ini": launcher_params["zandronum"]["ini"],
			"exec": launcher_params["zandronum"]["exec"]
		}

		with open(launcher_config_file, 'w') as configfile:
			parser.write(configfile)

		# Close window
		main_window.destroy()

		# Set flag to launch Zandronum
		zandronum_launch = True

#-------------------------------------------------------------------------
# MAIN SCRIPT
#-------------------------------------------------------------------------
# Parse configuration files
launcher_params = parse_launcher_conf(launcher_config_file)
zandronum_dirs = parse_zandronum_ini(launcher_params["zandronum"]["ini"])

# Set Zandronum launch variables
zandronum_launch = False
zandronum_params = [launcher_params["zandronum"]["exec"]]

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

# Get dialogs
prefs_dialog = builder.get_object("dialog_prefs")
prefs_inifile_btn = builder.get_object("btn_inifile")
prefs_execfile_btn = builder.get_object("btn_execfile")

# Set file chooser filters
pwad_file_filter = Gtk.FileFilter()
pwad_file_filter.set_name("PWAD files")

for filt in file_filters["pwad"]:
	pwad_file_filter.add_pattern(filt)

pwad_btn.add_filter(pwad_file_filter)

ini_file_filter = Gtk.FileFilter()
ini_file_filter.set_name("INI files")

for filt in file_filters["ini"]:
	ini_file_filter.add_pattern(filt)

prefs_inifile_btn.add_filter(ini_file_filter)

exec_file_filter = Gtk.FileFilter()
exec_file_filter.set_name("All files")

for filt in file_filters["all"]:
	exec_file_filter.add_pattern(filt)

prefs_execfile_btn.add_filter(exec_file_filter)

# Initialize widgets
initialize_widgets()

# Show main window
main_window.show_all()
Gtk.main()

# Destroy dialogs
prefs_dialog.destroy()

# Launch Zandronum
if zandronum_launch == True:
	zandronum_output = subprocess.run(zandronum_params)
