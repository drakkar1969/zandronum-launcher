#!/usr/bin/env python

import gi, sys, os, json, subprocess, shlex
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio, GObject, Pango

# Global path variable
app_dir = os.path.abspath(os.path.dirname(sys.argv[0]))

# Global gresource file
gresource = Gio.Resource.load(os.path.join(app_dir, "com.github.ZandronumLauncher.gresource"))
gresource._register()

#------------------------------------------------------------------------------
#-- CLASS: DIALOGSELECTROW
#------------------------------------------------------------------------------
@Gtk.Template(resource_path="/com/github/ZandronumLauncher/ui/dialogselectrow.ui")
class DialogSelectRow(Adw.ActionRow):
	__gtype_name__ = "DialogSelectRow"

	#-----------------------------------
	# Class widget variables
	#-----------------------------------
	label = Gtk.Template.Child()
	image = Gtk.Template.Child()
	file_btn = Gtk.Template.Child()
	clear_btn = Gtk.Template.Child()
	reset_btn = Gtk.Template.Child()

	#-----------------------------------
	# Button signals
	#-----------------------------------
	__gsignals__ = {
		"files-changed": (GObject.SignalFlags.RUN_FIRST, None, ())
	}

	#-----------------------------------
	# Button properties
	#-----------------------------------
	# icon_name property
	_icon_name = ""

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
	_folder_select = False

	@GObject.Property(type=bool, default=False)
	def folder_select(self):
		return(self._folder_select)

	@folder_select.setter
	def folder_select(self, value):
		self._folder_select = value

		if self._icon_name == "":
			self.image.set_from_icon_name("folder-symbolic" if self._folder_select == True else "document-open-symbolic")

	# can_clear property
	_can_clear = False

	@GObject.Property(type=bool, default=False)
	def can_clear(self):
		return(self._can_clear)

	@can_clear.setter
	def can_clear(self, value):
		self._can_clear = value

		self.clear_btn.set_visible(self._can_clear)

	# can_reset property
	_can_reset = False

	@GObject.Property(type=bool, default=False)
	def can_reset(self):
		return(self._can_reset)

	@can_reset.setter
	def can_reset(self, value):
		self._can_reset = value

		self.reset_btn.set_visible(self._can_reset)

	#-----------------------------------
	# File properties
	#-----------------------------------
	# base_folder property
	base_folder = GObject.Property(type=str, default="")

	def set_base_folder(self, value):
		self.base_folder = value

	# default_file property
	_default_file = ""

	@GObject.Property(type=str, default="")
	def default_file(self):
		return(self._default_file)

	@default_file.setter
	def default_file(self, value):
		self._default_file = value

		self.set_reset_btn_state()

	def set_default_file(self, value):
		self.default_file = value

	# selected_files property
	_selected_files = []

	@GObject.Property(type=GObject.TYPE_STRV, default=[])
	def selected_files(self):
		return(self._selected_files)

	@selected_files.setter
	def selected_files(self, value):
		self._selected_files = value

		n_files = len(self._selected_files)

		if n_files == 0:
			self.label.set_text("(None)")
		else:
			if n_files == 1:
				self.label.set_text(os.path.basename(self.selected_files[0]))
			else:
				self.label.set_text(f"({n_files} files)")

		self.set_clear_btn_state()
		self.set_reset_btn_state()

		self.emit("files-changed")

	def get_selected_files(self):
		return(self.selected_files)

	def get_selected_file(self):
		return(self.selected_files[0] if len(self.selected_files) > 0 else "")

	def set_selected_files(self, value):
		self.selected_files = value

	def set_selected_file(self, value):
		self.selected_files = [value]

	# Helper functions
	def set_clear_btn_state(self):
		self.clear_btn.set_sensitive(len(self._selected_files) != 0)

	def set_reset_btn_state(self):
		if self._default_file == "" or len(self._selected_files) != 1:
			self.reset_btn.set_sensitive(False)
		else:
			self.reset_btn.set_sensitive(self._default_file != self._selected_files[0])

	#-----------------------------------
	# Dialog properties
	#-----------------------------------
	dialog_parent = GObject.Property(type=Gtk.Window, default=None)
	dialog_title = GObject.Property(type=str, default="Open File")
	dialog_multi_select = GObject.Property(type=bool, default=False)
	dialog_file_filter = GObject.Property(type=Gtk.FileFilter, default=None)

	def set_dialog_parent(self, value):
		self.dialog_parent = value

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
	def on_file_btn_clicked(self, button):
		self.dialog = Gtk.FileChooserNative(title=self.dialog_title, transient_for=self.dialog_parent, action=Gtk.FileChooserAction.SELECT_FOLDER if self._folder_select == True else Gtk.FileChooserAction.OPEN)

		self.dialog.set_modal(True)
		self.dialog.set_accept_label("_Select")

		self.dialog.set_select_multiple(self.dialog_multi_select)

		if self.dialog_file_filter is not None: self.dialog.add_filter(self.dialog_file_filter)

		if len(self._selected_files) > 0:
			self.dialog.set_file(Gio.File.new_for_path(self._selected_files[0]))
		else:
			if self.base_folder != "":
				self.dialog.set_current_folder(Gio.File.new_for_path(self.base_folder))

		self.dialog.connect("response", self.on_dialog_response)

		self.dialog.show()

	def on_dialog_response(self, dialog, response):
		if response == Gtk.ResponseType.ACCEPT:
			self.selected_files = [gfile.get_path() for gfile in dialog.get_files() if gfile is not None]

	@Gtk.Template.Callback()
	def on_clear_btn_clicked(self, button):
		self.selected_files = []

	@Gtk.Template.Callback()
	def on_reset_btn_clicked(self, button):
		self.selected_files = [self._default_file]

#------------------------------------------------------------------------------
#-- CLASS: PREFERENCESWINDOW
#------------------------------------------------------------------------------
@Gtk.Template(resource_path="/com/github/ZandronumLauncher/ui/preferences.ui")
class PreferencesWindow(Adw.PreferencesWindow):
	__gtype_name__ = "PreferencesWindow"

	#-----------------------------------
	# Class widget variables
	#-----------------------------------
	exec_selectrow = Gtk.Template.Child()
	iwaddir_selectrow = Gtk.Template.Child()
	pwaddir_selectrow = Gtk.Template.Child()
	moddir_selectrow = Gtk.Template.Child()

	modgroup_check = Gtk.Template.Child()
	texture_check = Gtk.Template.Child()
	object_check = Gtk.Template.Child()
	monster_check = Gtk.Template.Child()
	menu_check = Gtk.Template.Child()
	hud_check = Gtk.Template.Child()

	#-----------------------------------
	# Init function
	#-----------------------------------
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.exec_selectrow.set_dialog_parent(self)
		self.iwaddir_selectrow.set_dialog_parent(self)
		self.pwaddir_selectrow.set_dialog_parent(self)
		self.moddir_selectrow.set_dialog_parent(self)

		# Flags for check button toggle handlers
		self.mod_is_changing = False
		self.modgroup_is_changing = False

	#-----------------------------------
	# Signal handlers
	#-----------------------------------
	@Gtk.Template.Callback()
	def on_modgroup_check_toggled(self, checkbutton):
		if self.mod_is_changing == False:
			self.modgroup_is_changing = True

			self.modgroup_check.set_inconsistent(False)

			self.texture_check.set_active(checkbutton.get_active())
			self.object_check.set_active(checkbutton.get_active())
			self.monster_check.set_active(checkbutton.get_active())
			self.menu_check.set_active(checkbutton.get_active())
			self.hud_check.set_active(checkbutton.get_active())

			self.modgroup_is_changing = False

	@Gtk.Template.Callback()
	def on_mod_check_toggled(self, checkbutton):
		if self.modgroup_is_changing == False:
			btn_list = [self.texture_check, self.object_check, self.monster_check, self.menu_check, self.hud_check]

			on_list = [1 for btn in btn_list if btn.get_active()]

			self.mod_is_changing = True

			self.modgroup_check.set_active(len(on_list) == len(btn_list))
			self.modgroup_check.set_inconsistent(len(on_list) != 0 and len(on_list) != len(btn_list))

			self.mod_is_changing = False

#------------------------------------------------------------------------------
#-- CLASS: CHEATSWINDOW
#------------------------------------------------------------------------------
@Gtk.Template(resource_path="/com/github/ZandronumLauncher/ui/cheats.ui")
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
			"-fast": "Increases the speed and attack rate of monsters. Requires the -warp parameter.",
			"-nomonsters": "Disable spawning of monsters. Requires the -warp parameter.",
			"-nomusic": "Disable background music",
			"-nosfx": "Disable sound effects",
			"-nosound": "Disable music and sound effects",
			"-respawn": "Monsters return a few seconds after being killed. Requires the -warp parameter.",
			"-skill <s>": "Select difficulty level <s> (1 to 5). This parameter will warp to the first level of the game (if no other -warp parameter is specified).",
			"-warp <m>\n-warp <e> <m>": "Start the game on level <m> (1 to 32). For Ultimate Doom and Freedoom Phase 1, both episode <e> (1 to 4) and map <m> (1 to 9) must be specified, separated by a space.",
			"-width x\n-height y": "Specify desired screen resolution."
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

		for i, key in enumerate(doom_switches):
			param_label = Gtk.Label(label=key, halign=Gtk.Align.START)
			self.switches_grid.attach(param_label, 0, i, 1, 1)

			if i == 0: param_label.add_css_class("heading")
			else: param_label.set_selectable(True)

			desc_label = Gtk.Label(label=doom_switches[key], halign=Gtk.Align.START, wrap_mode=Pango.WrapMode.WORD, wrap=True, width_chars=40, max_width_chars=40, xalign=0)
			self.switches_grid.attach(desc_label, 1, i, 1, 1)

			if i == 0: desc_label.add_css_class("heading")

		for i, key in enumerate(doom_cheats):
			cheat_label = Gtk.Label(label=key, halign=Gtk.Align.START)
			self.cheats_grid.attach(cheat_label, 0, i, 1, 1)

			if i == 0: cheat_label.add_css_class("heading")

			effect_label = Gtk.Label(label=doom_cheats[key], halign=Gtk.Align.START)
			self.cheats_grid.attach(effect_label, 1, i, 1, 1)

			if i == 0: effect_label.add_css_class("heading")

#------------------------------------------------------------------------------
#-- CLASS: MAINWINDOW
#------------------------------------------------------------------------------
@Gtk.Template(resource_path="/com/github/ZandronumLauncher/ui/window.ui")
class MainWindow(Adw.ApplicationWindow):
	__gtype_name__ = "MainWindow"

	#-----------------------------------
	# Class widget variables
	#-----------------------------------
	iwad_comborow = Gtk.Template.Child()
	iwad_stringlist = Gtk.Template.Child()
	pwad_selectrow = Gtk.Template.Child()
	params_entryrow = Gtk.Template.Child()
	params_clearbtn = Gtk.Template.Child()
	launch_btn = Gtk.Template.Child()

	shortcut_window = Gtk.Template.Child()
	prefs_window = Gtk.Template.Child()
	cheats_window = Gtk.Template.Child()

	#-----------------------------------
	# Init function
	#-----------------------------------
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		# Shortcut window
		self.set_help_overlay(self.shortcut_window)

		# Actions
		action_list = [
			[ "reset-widgets", self.on_reset_widgets_action ],
			[ "show-preferences", self.on_show_preferences_action ],
			[ "show-cheats", self.on_show_cheats_action ],
			[ "show-about", self.on_show_about_action ],
			[ "quit-app", self.on_quit_app_action ]
		]

		self.add_action_entries(action_list)

		# Keyboard shortcuts
		app.set_accels_for_action("win.reset-widgets", ["<ctrl>r"])
		app.set_accels_for_action("win.show-preferences", ["<ctrl>comma"])
		app.set_accels_for_action("win.show-help-overlay", ["<ctrl>question"])
		app.set_accels_for_action("win.show-cheats", ["F1"])
		app.set_accels_for_action("win.quit-app", ["<ctrl>q"])

		# Widget initialization
		self.populate_iwad_comborow(app.iwad_selected)

		self.pwad_selectrow.set_dialog_parent(self)
		self.pwad_selectrow.set_base_folder(app.pwad_folder)
		self.pwad_selectrow.set_selected_files(app.pwad_files)

		self.params_entryrow.set_text(app.extra_params)

		self.set_focus(self.iwad_comborow)

		# Preferences initialization
		self.prefs_window.set_transient_for(self)

		self.prefs_window.exec_selectrow.set_default_file(app.default_exec_file)
		self.prefs_window.exec_selectrow.set_selected_file(app.exec_file)

		self.prefs_window.iwaddir_selectrow.set_default_file(app.default_iwad_folder)
		self.prefs_window.iwaddir_selectrow.set_selected_file(app.iwad_folder)

		self.prefs_window.pwaddir_selectrow.set_default_file(app.default_pwad_folder)
		self.prefs_window.pwaddir_selectrow.set_selected_file(app.pwad_folder)

		self.prefs_window.moddir_selectrow.set_default_file(app.default_mods_folder)
		self.prefs_window.moddir_selectrow.set_selected_file(app.mods_folder)

		self.prefs_window.texture_check.set_active(app.mods_textures)
		self.prefs_window.object_check.set_active(app.mods_objects)
		self.prefs_window.monster_check.set_active(app.mods_monsters)
		self.prefs_window.menu_check.set_active(app.mods_menus)
		self.prefs_window.hud_check.set_active(app.mods_hud)

		# Help initialization
		self.cheats_window.set_transient_for(self)

	# Add IWADs to comborow
	def populate_iwad_comborow(self, iwad_selected):
		# Find iwad files in iwad folder and convert to lower case
		iwad_files = list(map(str.lower, os.listdir(app.iwad_folder)))

		# Get sorted list of iwad names from found iwad files
		iwad_names = [k for k,v in app.doom_iwads.items() if v["iwad"] in iwad_files]
		iwad_names.sort()

		# Clear iwad stringlist and add iwad names
		self.iwad_stringlist.splice(0, len(self.iwad_stringlist), iwad_names)

		# Set selected iwad
		try:
			self.iwad_comborow.set_selected(iwad_names.index(iwad_selected))
		except:
			self.iwad_comborow.set_selected(0)

		# Set launch button state
		self.launch_btn.set_sensitive(self.iwad_comborow.get_selected_item() is not None)

	#-----------------------------------
	# Action handlers
	#-----------------------------------
	def on_reset_widgets_action(self, action, param, user_data):
		self.iwad_comborow.set_selected(0)
		self.pwad_selectrow.set_selected_files([])
		self.params_entryrow.set_text("")

	def on_show_preferences_action(self, action, param, user_data):
		self.prefs_window.show()

	def on_show_cheats_action(self, action, param, user_data):
		self.cheats_window.show()

	def on_show_about_action(self, action, param, user_data):
		about_window = Adw.AboutWindow(
			application_name="Zandronum Launcher",
			application_icon="zandronum",
			developer_name="draKKar1969",
			version="1.2.0",
			website="https://github.com/drakkar1969/zandronum-launcher",
			developers=["draKKar1969"],
			designers=["draKKar1969"],
			license_type=Gtk.License.GPL_3_0,
			transient_for=self)

		about_window.show()

	def on_quit_app_action(self, action, param, user_data):
		self.close()

	#-----------------------------------
	# Signal handlers
	#-----------------------------------
	@Gtk.Template.Callback()
	def on_iwad_combo_changed(self, combo, param):
		if iwad_selected := combo.get_selected_item():
			app.iwad_selected = iwad_selected.get_string()

	@Gtk.Template.Callback()
	def on_pwad_selectrow_files_changed(self, button):
		app.pwad_files = button.get_selected_files()

	@Gtk.Template.Callback()
	def on_params_entryrow_changed(self, entry):
		extra_params = entry.get_text()
		app.extra_params = extra_params

		self.params_clearbtn.set_visible(extra_params != "")

	@Gtk.Template.Callback()
	def on_params_clearbtn_clicked(self, button):
		self.params_entryrow.set_text("")

	@Gtk.Template.Callback()
	def on_launch_btn_clicked(self, button):
		self.set_sensitive(False)

		if self.launch_zandronum() == True: self.close()
		else: self.set_sensitive(True)

	@Gtk.Template.Callback()
	def on_prefs_window_close(self, window):
		if (exec_file := window.exec_selectrow.get_selected_file()) != app.exec_file:
			app.exec_file = exec_file

		if (iwad_folder := window.iwaddir_selectrow.get_selected_file()) != app.iwad_folder:
			app.iwad_folder = iwad_folder
			self.populate_iwad_comborow(app.iwad_selected)

		if (pwad_folder := window.pwaddir_selectrow.get_selected_file()) != app.pwad_folder:
			app.pwad_folder = pwad_folder
			self.pwad_selectrow.set_base_folder(pwad_folder)

		if(mods_folder := window.moddir_selectrow.get_selected_file()) != app.mods_folder:
			app.mods_folder = mods_folder

		if (mods_textures := window.texture_check.get_active()) != app.mods_textures:
			app.mods_textures = mods_textures

		if (mods_objects := window.object_check.get_active()) != app.mods_objects:
			app.mods_objects = mods_objects
	
		if (mods_monsters := window.monster_check.get_active()) != app.mods_monsters:
			app.mods_monsters = mods_monsters

		if (mods_menus := window.menu_check.get_active()) != app.mods_menus:
			app.mods_menus = mods_menus

		if (mods_hud := window.hud_check.get_active()) != app.mods_hud:
			app.mods_hud = mods_hud

	#-----------------------------------
	# Launch Zandronum function
	#-----------------------------------
	def launch_zandronum(self):
		# Return with error if Zandronum executable does not exist
		if os.path.exists(app.exec_file) == False:
			print('ERROR: Zandronum executable not found')
			return(False)

		# Initialize Zandronum command line with executable
		cmdline = app.exec_file

		# Return with error if IWAD name is empty
		if app.iwad_selected == "":
			print('ERROR: No IWAD file specified')
			return(False)

		# Return with error if IWAD file does not exist
		iwad_file = os.path.join(app.iwad_folder, app.doom_iwads[app.iwad_selected]["iwad"])

		if os.path.exists(iwad_file) == False:
			print(f'ERROR: IWAD file {app.doom_iwads[app.iwad_selected]["iwad"]} not found')
			return(False)

		# Add IWAD file
		cmdline += f' -iwad "{iwad_file}"'

		# Add hi-res graphics if options are true and files are present
		mod_files = []

		if app.mods_textures == True:
			mod_files.extend(app.doom_iwads[app.iwad_selected]["mods"]["textures"])

		if app.mods_objects == True:
			mod_files.extend(app.doom_iwads[app.iwad_selected]["mods"]["objects"])

		if app.mods_monsters == True:
			mod_files.extend(app.doom_iwads[app.iwad_selected]["mods"]["monsters"])

		if app.mods_menus == True:
			mod_files.extend(app.doom_iwads[app.iwad_selected]["mods"]["menus"])

		if app.mods_hud == True:
			mod_files.extend(app.doom_iwads[app.iwad_selected]["mods"]["hud"])

		for mod in mod_files:
			mod_file = os.path.join(app.mods_folder, mod)

			if os.path.exists(mod_file): cmdline += f' -file "{mod_file}"'

		# Add PWAD files if present
		for pwad in app.pwad_files:
			if pwad != "" and os.path.exists(pwad):
				cmdline += f' -file "{pwad}"'

		# Add extra params if present
		if app.extra_params != "":
			cmdline += f' {app.extra_params}'

		# Launch Zandronum
		subprocess.Popen(shlex.split(cmdline))

		return(True)

#------------------------------------------------------------------------------
#-- CLASS: LAUNCHERAPP
#------------------------------------------------------------------------------
class LauncherApp(Adw.Application):
	#-----------------------------------
	# Properties
	#-----------------------------------
	_exec_file = ""

	@GObject.Property(type=str)
	def exec_file(self):
		return(os.path.expandvars(self._exec_file))

	@exec_file.setter
	def exec_file(self, value):
		self._exec_file = value

	_iwad_folder = ""

	@GObject.Property(type=str)
	def iwad_folder(self):
		return(os.path.expandvars(self._iwad_folder))

	@iwad_folder.setter
	def iwad_folder(self, value):
		self._iwad_folder = value

	_pwad_folder = ""

	@GObject.Property(type=str)
	def pwad_folder(self):
		return(os.path.expandvars(self._pwad_folder))

	@pwad_folder.setter
	def pwad_folder(self, value):
		self._pwad_folder = value

	_mods_folder = ""

	@GObject.Property(type=str)
	def mods_folder(self):
		return(os.path.expandvars(self._mods_folder))

	@mods_folder.setter
	def mods_folder(self, value):
		self._mods_folder = value

	mods_textures = GObject.Property(type=bool, default=True)
	mods_objects = GObject.Property(type=bool, default=True)
	mods_monsters = GObject.Property(type=bool, default=True)
	mods_menus = GObject.Property(type=bool, default=True)
	mods_hud = GObject.Property(type=bool, default=True)

	iwad_selected = GObject.Property(type=str)
	pwad_files = GObject.Property(type=GObject.TYPE_STRV)
	extra_params = GObject.Property(type=str)

	#-----------------------------------
	# Init function
	#-----------------------------------
	def __init__(self, **kwargs):
		super().__init__(**kwargs)

		# Connect signal handlers
		self.connect("startup", self.on_startup)
		self.connect("activate", self.on_activate)
		self.connect("shutdown", self.on_shutdown)

		# Initialize gsettings
		self.gsettings = Gio.Settings(schema_id="com.github.ZandronumLauncher")
		self.gsettings.delay()

		self.gsettings.bind("executable-file", self, "exec_file", Gio.SettingsBindFlags.DEFAULT)
		self.gsettings.bind("iwad-folder", self, "iwad_folder", Gio.SettingsBindFlags.DEFAULT)
		self.gsettings.bind("pwad-folder", self, "pwad_folder", Gio.SettingsBindFlags.DEFAULT)
		self.gsettings.bind("mods-folder", self, "mods_folder", Gio.SettingsBindFlags.DEFAULT)
		self.gsettings.bind("enable-texture-mods", self, "mods_textures", Gio.SettingsBindFlags.DEFAULT)
		self.gsettings.bind("enable-object-mods", self, "mods_objects", Gio.SettingsBindFlags.DEFAULT)
		self.gsettings.bind("enable-monster-mods", self, "mods_monsters", Gio.SettingsBindFlags.DEFAULT)
		self.gsettings.bind("enable-menu-mods", self, "mods_menus", Gio.SettingsBindFlags.DEFAULT)
		self.gsettings.bind("enable-hud-mods", self, "mods_hud", Gio.SettingsBindFlags.DEFAULT)
		self.gsettings.bind("selected-iwad", self, "iwad_selected", Gio.SettingsBindFlags.DEFAULT)
		self.gsettings.bind("pwad-files", self, "pwad_files", Gio.SettingsBindFlags.DEFAULT)
		self.gsettings.bind("extra-parameters", self, "extra_params", Gio.SettingsBindFlags.DEFAULT)

		# Initialize default values for settings
		self.default_exec_file = os.path.expandvars(self.gsettings.get_default_value("executable-file").get_string())
		self.default_iwad_folder = os.path.expandvars(self.gsettings.get_default_value("iwad-folder").get_string())
		self.default_pwad_folder = os.path.expandvars(self.gsettings.get_default_value("pwad-folder").get_string())
		self.default_mods_folder = os.path.expandvars(self.gsettings.get_default_value("mods-folder").get_string())

	#-----------------------------------
	# Signal handlers
	#-----------------------------------
	def on_startup(self, app):
		# Read IWAD json file
		with open(os.path.join(app_dir, "iwads.json"), "r") as iwad_file:
			self.doom_iwads = json.load(iwad_file)

	def on_activate(self, app):
		self.main_window = MainWindow(application=app)
		self.main_window.present()

	def on_shutdown(self, app):
		# Write gsettings
		self.gsettings.apply()

#------------------------------------------------------------------------------
#-- MAIN APP
#------------------------------------------------------------------------------
app = LauncherApp(application_id="com.github.ZandronumLauncher")
app.run(sys.argv)
