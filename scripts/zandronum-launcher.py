#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gi, os, sys, configparser, subprocess
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk

# Get config dir
config_dir = "{:s}/.config/zandronum".format(os.getenv('HOME'))

# Parse launcher config file
launcher_config_file = "{:s}/launcher.conf".format(config_dir)

launcher_parser = configparser.ConfigParser()
launcher_parser.read(launcher_config_file)

launcher_params = {}

launcher_params["iwad"] = launcher_parser.get("launcher", "iwad", fallback="")
launcher_params["file"] = launcher_parser.get("launcher", "pwad", fallback="")
launcher_params["warp"] = launcher_parser.get("launcher", "warp", fallback="")
launcher_params["params"] = launcher_parser.get("launcher", "params", fallback="")

launcher_params["zandronum_ini"] = launcher_parser.get("zandronum", "inifile", fallback="{:s}/zandronum.ini".format(config_dir))
launcher_params["zandronum_exec"] = launcher_parser.get("zandronum", "exec", fallback="/usr/bin/zandronum")

# Parse Zandronum ini file: get IWAD/PWAD directories
zandronum_parser = configparser.ConfigParser(strict=False)
zandronum_parser.read(launcher_params["zandronum_ini"])

zandronum_iwad_dir = zandronum_parser.get("IWADSearch.Directories", "Path", fallback="{:s}/IWADs".format(config_dir))
zandronum_pwad_dir = zandronum_parser.get("FileSearch.Directories", "Path", fallback="{:s}/WADs".format(config_dir))

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

# PWAD file chooser filters
file_filters = {
	"pwad": ["*.wad", "*.WAD", "*.pk3", "*.PK3", "*.pk7", "*.PK7", "*.zip", "*.ZIP", "*.7z", "*.7Z"]
}

# Zandronum launch variables
zandronum_launch = False
zandronum_params = [launcher_params["zandronum_exec"]]

# Event handlers
class EventHandlers:
	def on_window_main_key_press_event(self, widget, event):
		# Close window if ESC key pressed
		if event.keyval == Gdk.KEY_Escape:
			main_window.destroy()

	def on_menu_clearpwad_clicked(self, button):
		pwad_btn.unselect_all()

	def on_menu_reset_clicked(self, button):
		try:
			game_combo.set_active(0)
		except:
			game_combo.set_active(-1)
		pwad_btn.set_filename("")
		warp_entry.set_text("")
		params_entry.set_text("")

	def on_btn_launch_clicked(self, button):
		global zandronum_launch
		global zandronum_params

		# Get game combox selection
		game_text = game_combo.get_active_text()
		try:
			game_file = list(found_iwads.keys())[list(found_iwads.values()).index(game_text)]
			zandronum_params.extend(["-iwad", zandronum_iwad_dir + game_file])
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
		launcher_parser["launcher"] = {
			"iwad": game_file.lower(),
			"pwad": pwad_file,
			"warp": warp_level,
			"params": extra_params
		}

		with open(launcher_config_file, 'w') as configfile:
			launcher_parser.write(configfile)

		# Close window
		main_window.destroy()

		# Set flag to launch Zandronum
		zandronum_launch = True

def initialize_widgets():
	# Game combobox
	game_combo.remove_all()
	found_iwads.clear()

	game_index = 0

	iwads = os.listdir(zandronum_iwad_dir)
	iwads.sort()

	for i in range(len(iwads)):
		iwad_lc = iwads[i].lower()
		if iwad_lc.endswith(".wad") and iwad_lc in doom_iwads:
			found_iwads[iwads[i]] = doom_iwads[iwad_lc]
			game_combo.append_text(doom_iwads[iwad_lc])
		if iwad_lc == launcher_params["iwad"]:
			game_index = i

	try:
		game_combo.set_active(game_index)
	except:
		game_combo.set_active(-1)

	# PWAD file button
	pwad_btn.unselect_all()

	pwad_btn.set_current_folder(zandronum_pwad_dir)
	pwad_btn.set_filename(launcher_params["file"])

	# Entries
	warp_entry.set_text(launcher_params["warp"])
	params_entry.set_text(launcher_params["params"])

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

# Set PWAD file chooser filters
file_filter = Gtk.FileFilter()
file_filter.set_name("PWAD files")

for filt in file_filters["pwad"]:
	file_filter.add_pattern(filt)

pwad_btn.add_filter(file_filter)

# Initialize widgets
initialize_widgets()

# Show main window
main_window.show_all()
Gtk.main()

# Launch Zandronum
if zandronum_launch == True:
	zandronum_output = subprocess.run(zandronum_params)
