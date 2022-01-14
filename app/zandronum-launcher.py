#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gi, os, sys, configparser, subprocess, shlex, shutil
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk

#-------------------------------------------------------------------------
# GLOBAL VARIABLES
#-------------------------------------------------------------------------
# App dir
app_dir = os.path.abspath(os.path.dirname(sys.argv[0]))

# Config dir
config_dir = os.path.join(os.getenv('HOME'), ".config/zandronum")

# Launcher config file
launcher_config_file = os.path.join(config_dir, "launcher.conf")

# IWAD filenames/descriptions/mod files
doom_iwads = {
	"doom.wad": {"name": "The Ultimate Doom", "patch": "", "mods": ["hud-stuff.pk3", "zdoom-1.pk3", "zdoom-2.pk3", "jfo-udoom.pk3"]},
	"doom2.wad": {"name": "Doom II: Hell on Earth", "patch": "", "mods": ["hud-stuff.pk3", "zdoom-1.pk3", "zdoom-2.pk3", "zdoom-doom2.pk3", "jfo-doom2.pk3"]},
	"plutonia.wad": {"name": "Final Doom - The Plutonia Experiment", "patch": "", "mods": ["hud-stuff.pk3", "zdoom-1.pk3", "zdoom-2.pk3", "zdoom-doom2.pk3", "zdoom-plut.pk3", "jfo-plut.pk3"]},
	"tnt.wad": {"name": "Final Doom - TNT: Evilution", "patch": "tnt31-patch.wad", "mods": ["hud-stuff.pk3", "zdoom-1.pk3", "zdoom-2.pk3", "zdoom-doom2.pk3", "zdoom-tnt.pk3", "jfo-tnt.pk3"]},
	"freedoom1.wad": {"name": "Freedoom Phase 1", "patch": "", "mods": []},
	"freedoom2.wad": {"name": "Freedoom Phase 2", "patch": "", "mods": []}
}

# File chooser filters
file_filters = {
	"pwad": {
		"name": "PWAD files (*.wad, *.pk3, *.pk7, *.zip, *.7z)",
		"patterns": ["*.wad", "*.WAD", "*.pk3", "*.PK3", "*.pk7", "*.PK7", "*.zip", "*.ZIP", "*.7z", "*.7Z"]
	}
}

#-------------------------------------------------------------------------
# FUNCTION: parse_launcher_conf
#-------------------------------------------------------------------------
def parse_launcher_conf(config_file):
	parser = configparser.ConfigParser()
	parser.read(config_file)

	config = { "launcher": {}, "zandronum": {} }

	config["launcher"]["iwad"] = parser.get("launcher", "iwad", fallback="")
	config["launcher"]["file"] = parser.get("launcher", "file", fallback="")
	config["launcher"]["warp"] = parser.get("launcher", "warp", fallback="")
	config["launcher"]["params"] = parser.get("launcher", "params", fallback="")

	config["zandronum"]["exec"] = parser.get("zandronum", "exec", fallback="/usr/bin/zandronum")
	config["zandronum"]["mods"] = parser.getboolean("zandronum", "mods", fallback=True)

	return(config)

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
	game_store.clear()

	game_index = 0

	iwads = os.listdir(os.path.join(app_dir, "iwads"))
	iwads.sort()

	for i in range(len(iwads)):
		if iwads[i] in doom_iwads:
			game_store.append([doom_iwads[iwads[i]]["name"], iwads[i]])

		if iwads[i] == main_config["launcher"]["iwad"]:
			game_index = i

	try:
		game_combo.set_active(game_index)
	except:
		game_combo.set_active(-1)

	# Launch button
	launch_btn.set_sensitive(True if len(game_store) > 0 else False)

	# PWAD file button
	pwad_btn.unselect_all()

	pwad_btn.set_current_folder(config_dir)
	pwad_btn.set_filename(main_config["launcher"]["file"])

	# Entries
	warp_entry.set_text(main_config["launcher"]["warp"])
	params_entry.set_text(main_config["launcher"]["params"])

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
		# Check modifiers
		ctrl = (event.state & Gdk.ModifierType.CONTROL_MASK)
		shift = (event.state & Gdk.ModifierType.SHIFT_MASK)
		alt = (event.state & Gdk.ModifierType.MOD1_MASK)
		mod_state = (ctrl | shift | alt)

		# Close window if ESC key pressed (and no modifiers)
		if event.keyval == Gdk.KEY_Escape and mod_state == 0:
			main_window.destroy()

		# Launch Zandronum if ENTER key pressed (and no modifiers)
		if (event.keyval == Gdk.KEY_Return or event.keyval == Gdk.KEY_KP_Enter) and mod_state == 0:
			self.on_btn_launch_clicked(launch_btn)

		# Close window if Ctrl + q pressed
		if Gdk.keyval_name(event.keyval) == 'q' and ctrl and alt == 0 and shift == 0:
			main_window.destroy()

	def on_btn_clear_pwad_clicked(self, button):
		pwad_btn.unselect_all()

	def on_menu_reset_clicked(self, button):
		reset_widgets()

	def on_menu_settings_clicked(self, button):
		global main_config
		global zandronum_dirs

		prefs_execfile_btn.set_filename(main_config["zandronum"]["exec"])
		prefs_mods_switch.set_active(main_config["zandronum"]["mods"])

		dlg_response = prefs_dialog.run()

		if(dlg_response == Gtk.ResponseType.OK):
			zandronum_exec = prefs_execfile_btn.get_filename()

			if (zandronum_exec is not None):
				main_config["zandronum"]["exec"] = zandronum_exec

			main_config["zandronum"]["mods"] = prefs_mods_switch.get_active()

		prefs_dialog.hide()

	def on_btn_launch_clicked(self, button):
		# Initialize Zandronum command line with executable
		cmdline = main_config["zandronum"]["exec"]

		# Get game combox selection
		game_item = game_combo.get_active_iter()
		try:
			game_file = game_store[game_item][1]
			cmdline += ' -iwad "{:s}/iwads/{:s}"'.format(app_dir, game_file)

			# Load patch
			patch_file = doom_iwads[game_file]["patch"]
			if patch_file != "":
				cmdline += ' -file "{:s}/iwads/{:s}"'.format(app_dir, patch_file)

			# Load mods
			if main_config["zandronum"]["mods"] == True:
				game_mods = doom_iwads[game_file]["mods"]
				
				for mod_file in game_mods:
					cmdline += ' -file "{:s}/mods/{:s}"'.format(app_dir, mod_file)
		except:
			game_file = ""

		# Get PWAD file
		pwad_file = pwad_btn.get_filename()
		if pwad_file is None:
			pwad_file = ""
		else:
			cmdline += ' -file "{:s}"'.format(pwad_file)

		# Get warp level
		warp_level = warp_entry.get_text()
		if warp_level != "":
			cmdline += ' -warp {:s}'.format(warp_level)

		# Get extra params
		extra_params = params_entry.get_text()
		if extra_params != "":
			cmdline += ' {:s}'.format(extra_params)

		# Update launcher params
		main_config["launcher"] = {
			"iwad": game_file,
			"file": pwad_file,
			"warp": warp_level,
			"params": extra_params
		}

		# Close window
		main_window.destroy()

		# Launch Zandronum
		subprocess.Popen(shlex.split(cmdline))

#-------------------------------------------------------------------------
# MAIN SCRIPT
#-------------------------------------------------------------------------
# Create config dirs if do not exist
if os.path.exists(config_dir) == False:
	os.makedirs(config_dir, exist_ok=True)

save_dir = os.path.join(config_dir, "Savegames")

if os.path.exists(save_dir) == False:
	os.makedirs(save_dir, exist_ok=True)

screen_dir = os.path.join(config_dir, "Screenshots")

if os.path.exists(screen_dir) == False:
	os.makedirs(screen_dir, exist_ok=True)

# Copy Zandronum INI if does not exist
zandronum_ini_dest = os.path.join(config_dir, "zandronum.ini")
zandronum_ini_src = os.path.join(app_dir, "config/zandronum.ini")

if os.path.exists(zandronum_ini_dest) == False:
	shutil.copyfile(zandronum_ini_src, zandronum_ini_dest)

# Parse configuration file
main_config = parse_launcher_conf(launcher_config_file)

# Set application name (match .desktop name)
GLib.set_prgname("Zandronum-Launcher")

# Create dialog with glade template
builder = Gtk.Builder()
builder.add_from_file(os.path.join(app_dir, "zandronum-launcher.ui"))
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
prefs_execfile_btn = builder.get_object("btn_execfile")
prefs_mods_switch = builder.get_object("switch_mods")

# Prepare game combo
game_store = Gtk.ListStore(str, str)
game_combo.set_model(game_store)

game_renderer = Gtk.CellRendererText()

game_combo.pack_start(game_renderer, True)
game_combo.add_attribute(game_renderer, "text", 0)

# Set file chooser filters
set_file_filters(widget=pwad_btn, filters=file_filters["pwad"])

# Initialize widgets
initialize_widgets()

# Show main window
main_window.show_all()
Gtk.main()

# Destroy dialogs
prefs_dialog.destroy()

# Save preferences
parser = configparser.ConfigParser()
parser.read_dict(main_config)

with open(launcher_config_file, 'w') as configfile:
	parser.write(configfile)