#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gi, os, sys, configparser, subprocess
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk

# Get Zandronum config directory
zandronum_config_dir = "{:s}/.config/zandronum".format(os.getenv('HOME'))

# Get Zandronum IWAD/PWAD directories
zandronum_config = configparser.ConfigParser(strict=False)
zandronum_config.read("{:s}/zandronum.ini".format(zandronum_config_dir))

zandronum_iwad_dir = zandronum_config.get("IWADSearch.Directories", "Path", fallback="{:s}/IWADs".format(zandronum_config_dir))
zandronum_pwad_dir = zandronum_config.get("FileSearch.Directories", "Path", fallback="{:s}/WADs".format(zandronum_config_dir))

# Get launcher config
launcher_config = configparser.ConfigParser()
launcher_config.read("{:s}/launcher.conf".format(zandronum_config_dir))

launcher_iwad = launcher_config.get("zandronum", "iwad", fallback="")
launcher_file = launcher_config.get("zandronum", "pwad", fallback="")
launcher_warp = launcher_config.get("zandronum", "warp", fallback="")
launcher_params = launcher_config.get("zandronum", "params", fallback="")

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
pwad_filters = ["*.wad", "*.WAD", "*.pk3", "*.PK3", "*.pk7", "*.PK7", "*.zip", "*.ZIP", "*.7z", "*.7Z"]

# Zandronum launch variables
zandronum_launch = False
zandronum_params = ["/usr/bin/zandronum"]

# Event handlers
class EventHandlers:
	def on_window_main_key_press_event(self, widget, event):
		# Close window if ESC key pressed
		if event.keyval == Gdk.KEY_Escape:
			main_window.destroy()

	def on_menu_clearpwad_clicked(self, button):
		pwad_btn.set_filename("")

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
		launcher_config["zandronum"] = {
			"iwad": game_file.lower(),
			"pwad": pwad_file,
			"warp": warp_level,
			"params": extra_params
		}

		with open("{:s}/launcher.conf".format(zandronum_config_dir), 'w') as configfile:
			launcher_config.write(configfile)

		# Close window
		main_window.destroy()

		# Set flag to launch Zandronum
		zandronum_launch = True

def initialize_controls():
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
		if iwad_lc == launcher_iwad:
			game_index = i

	try:
		game_combo.set_active(game_index)
	except:
		game_combo.set_active(-1)

	# PWAD file button
	pwad_btn.set_current_folder(zandronum_pwad_dir)
	pwad_btn.set_filename(launcher_file)

	# Entries
	warp_entry.set_text(launcher_warp)
	params_entry.set_text(launcher_params)

# Set application name (match .desktop name)
GLib.set_prgname("Zandronum-Launcher")

# Create dialog with glade template
builder = Gtk.Builder()
builder.add_from_file("{:s}/zandronum-launcher.ui".format(os.path.abspath(os.path.dirname(sys.argv[0]))))
builder.connect_signals(EventHandlers())

# Get main window
main_window = builder.get_object("window_main")
main_window.connect("destroy", Gtk.main_quit)

# Get controls
game_combo = builder.get_object("combo_game")
pwad_btn = builder.get_object("btn_pwad")
warp_entry = builder.get_object("entry_warp")
params_entry = builder.get_object("entry_params")

# Set PWAD file chooser filters
file_filter = Gtk.FileFilter()
file_filter.set_name("PWAD files")

for filt in pwad_filters:
	file_filter.add_pattern(filt)

pwad_btn.add_filter(file_filter)

# Initialize controls
initialize_controls()

# Show main window
main_window.show_all()
Gtk.main()

# Launch Zandronum
if zandronum_launch == True:
	zandronum_output = subprocess.run(zandronum_params)
