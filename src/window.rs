use std::path::Path;
use std::error::Error;
use std::fmt;
use std::process::Command;

use gtk::{gio, glib};
use adw::subclass::prelude::*;
use adw::prelude::*;
use glib::{clone, closure_local};
use glib::once_cell::sync::OnceCell;

use shlex;

use crate::APP_ID;
use crate::ZLApplication;
use crate::iwad_combo_row::IWadComboRow;
use crate::file_select_row::FileSelectRow;
use crate::preferences_window::PreferencesWindow;
use crate::cheats_window::CheatsWindow;

//------------------------------------------------------------------------------
// ERROR: LaunchError
//------------------------------------------------------------------------------
#[derive(Debug)]
struct LaunchError {
    msg: String
}

impl LaunchError {
    fn new(msg: &str) -> LaunchError {
        LaunchError{msg: msg.to_string()}
    }
}

impl fmt::Display for LaunchError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{}", self.msg)
    }
}

impl Error for LaunchError {}

//------------------------------------------------------------------------------
// MODULE: ZLWindow
//------------------------------------------------------------------------------
mod imp {
    use super::*;

    //-----------------------------------
    // Private structure
    //-----------------------------------
    #[derive(Default, gtk::CompositeTemplate)]
    #[template(resource = "/com/github/ZandronumLauncher/ui/window.ui")]
    pub struct ZLWindow {
        #[template_child]
        pub iwad_comborow: TemplateChild<IWadComboRow>,
        #[template_child]
        pub pwad_filerow: TemplateChild<FileSelectRow>,
        #[template_child]
        pub params_entryrow: TemplateChild<adw::EntryRow>,
        #[template_child]
        pub launch_button: TemplateChild<gtk::Button>,

        #[template_child]
        pub prefs_window: TemplateChild<PreferencesWindow>,
        #[template_child]
        pub cheats_window: TemplateChild<CheatsWindow>,

        pub gsettings: OnceCell<gio::Settings>,
    }

    //-----------------------------------
    // Subclass
    //-----------------------------------
    #[glib::object_subclass]
    impl ObjectSubclass for ZLWindow {
        const NAME: &'static str = "ZLWindow";
        type Type = super::ZLWindow;
        type ParentType = adw::ApplicationWindow;

        fn class_init(klass: &mut Self::Class) {
            IWadComboRow::ensure_type();
            FileSelectRow::ensure_type();
            PreferencesWindow::ensure_type();
            CheatsWindow::ensure_type();

            klass.bind_template();
        }

        fn instance_init(obj: &glib::subclass::InitializingObject<Self>) {
            obj.init_template();
        }
    }

    impl ObjectImpl for ZLWindow {
        //-----------------------------------
        // Constructor
        //-----------------------------------
        fn constructed(&self) {
            let obj = self.obj();

            self.parent_constructed();

            obj.setup_widgets();
            obj.setup_signals();

            obj.init_from_gsettings();

            obj.setup_actions();
            obj.setup_shortcuts();
        }
    }

    impl WidgetImpl for ZLWindow {}
    impl WindowImpl for ZLWindow {
        //-----------------------------------
        // Window close handler
        //-----------------------------------
        fn close_request(&self) -> glib::Propagation {
            self.obj().save_gsettings();

            glib::Propagation::Proceed
        }
    }
    impl ApplicationWindowImpl for ZLWindow {}
    impl AdwApplicationWindowImpl for ZLWindow {}
}

//------------------------------------------------------------------------------
// IMPLEMENTATION: ZLWindow
//------------------------------------------------------------------------------
glib::wrapper! {
    pub struct ZLWindow(ObjectSubclass<imp::ZLWindow>)
        @extends gtk::Widget, gtk::Window, gtk::ApplicationWindow, adw::ApplicationWindow,
        @implements gio::ActionGroup, gio::ActionMap, gtk::Accessible, gtk::Buildable,
                    gtk::ConstraintTarget, gtk::Native, gtk::Root, gtk::ShortcutManager;
}

impl ZLWindow {
    //-----------------------------------
    // New function
    //-----------------------------------
    pub fn new(app: &ZLApplication) -> Self {
        glib::Object::builder().property("application", app).build()
    }

    //-----------------------------------
    // Setup widgets
    //-----------------------------------
    fn setup_widgets(&self) {
        let imp = self.imp();

        // Set preferences window parent
        imp.prefs_window.set_transient_for(Some(self));

        // Set cheats window parent
        imp.cheats_window.set_transient_for(Some(self));
    }

    //-----------------------------------
    // Setup signals
    //-----------------------------------
    fn setup_signals(&self) {
        let prefs = self.imp().prefs_window.get();

        // Preferences window IWAD folders property notify signal
        prefs.imp().iwad_filerow.connect_closure("changed", false, closure_local!(@watch self as obj => move |iwad_row: FileSelectRow| {
            let imp = obj.imp();

            imp.iwad_comborow.populate(&iwad_row.path());

            imp.launch_button.set_sensitive(imp.iwad_comborow.selected_iwad().is_some());
        }));

        // Preferences window PWAD folder changed signal
        prefs.imp().pwad_filerow.connect_closure("changed", false, closure_local!(@watch self as obj => move |pwad_row: FileSelectRow| {
            let imp = obj.imp();

            if pwad_row.path().is_empty() {
                imp.pwad_filerow.set_base_folder(None);
            } else {
                imp.pwad_filerow.set_base_folder(Some(&pwad_row.path()));
            }
        }));
    }

    //-----------------------------------
    // Init gsettings
    //-----------------------------------
    fn init_from_gsettings(&self) {
        let imp = self.imp();

        // Set config folder
        let config_folder = Some("$HOME/.config/zandronum");

        // Create gsettings
        let gsettings = gio::Settings::new(APP_ID);

        gsettings.delay();

        // Init preferences window
        let prefs = imp.prefs_window.imp();

        prefs.exec_filerow.set_path(Some(&gsettings.string("executable-file")));
        prefs.iwad_filerow.set_path(Some(&gsettings.string("iwad-folder")));
        prefs.pwad_filerow.set_path(Some(&gsettings.string("pwad-folder")));
        prefs.mods_filerow.set_path(Some(&gsettings.string("mods-folder")));

        prefs.exec_filerow.set_default_path(Some(&gsettings.default_value("executable-file").unwrap().to_string().replace("'", "")));
        prefs.iwad_filerow.set_default_path(Some(&gsettings.default_value("iwad-folder").unwrap().to_string().replace("'", "")));
        prefs.pwad_filerow.set_default_path(Some(&gsettings.default_value("pwad-folder").unwrap().to_string().replace("'", "")));
        prefs.mods_filerow.set_default_path(Some(&gsettings.default_value("mods-folder").unwrap().to_string().replace("'", "")));

        prefs.exec_filerow.set_base_folder(config_folder);
        prefs.iwad_filerow.set_base_folder(config_folder);
        prefs.pwad_filerow.set_base_folder(config_folder);
        prefs.mods_filerow.set_base_folder(config_folder);

        prefs.texture_switchrow.set_active(gsettings.boolean("enable-texture-mods"));
        prefs.object_switchrow.set_active(gsettings.boolean("enable-object-mods"));
        prefs.monster_switchrow.set_active(gsettings.boolean("enable-monster-mods"));
        prefs.menu_switchrow.set_active(gsettings.boolean("enable-menu-mods"));
        prefs.hud_switchrow.set_active(gsettings.boolean("enable-hud-mods"));

        // Init main window
        imp.iwad_comborow.set_selected_iwad_file(&gsettings.string("selected-iwad"));
        imp.pwad_filerow.set_paths(gsettings.strv("pwad-files"));
        imp.params_entryrow.set_text(&gsettings.string("extra-parameters"));

        // Store gsettings
        imp.gsettings.set(gsettings).unwrap();

        // Set initial focus on IWAD combo row
        imp.iwad_comborow.get().grab_focus();
    }

    //-----------------------------------
    // Save gsettings
    //-----------------------------------
    fn save_gsettings(&self) {
        let imp = self.imp();

        if let Some(gsettings) = imp.gsettings.get() {
            // Get selected IWAD
            let selected_iwad = imp.iwad_comborow.selected_iwad()
                .map_or("".to_string(), |iwad| iwad.iwad());

            // Save main window settings
            gsettings.set_string("selected-iwad", &selected_iwad).unwrap();
            gsettings.set_strv("pwad-files", imp.pwad_filerow.paths()).unwrap();
            gsettings.set_string("extra-parameters", &imp.params_entryrow.text()).unwrap();

            // Save preferences window settings
            let prefs = imp.prefs_window.imp();

            gsettings.set_string("executable-file", &prefs.exec_filerow.path()).unwrap();
            gsettings.set_string("iwad-folder", &prefs.iwad_filerow.path()).unwrap();
            gsettings.set_string("pwad-folder", &prefs.pwad_filerow.path()).unwrap();
            gsettings.set_string("mods-folder", &prefs.mods_filerow.path()).unwrap();

            gsettings.set_boolean("enable-texture-mods", prefs.texture_switchrow.is_active()).unwrap();
            gsettings.set_boolean("enable-object-mods", prefs.object_switchrow.is_active()).unwrap();
            gsettings.set_boolean("enable-monster-mods", prefs.monster_switchrow.is_active()).unwrap();
            gsettings.set_boolean("enable-menu-mods", prefs.menu_switchrow.is_active()).unwrap();
            gsettings.set_boolean("enable-hud-mods", prefs.hud_switchrow.is_active()).unwrap();

            gsettings.apply();
        }
    }

    //-----------------------------------
    // Setup actions
    //-----------------------------------
    fn setup_actions(&self) {
        let imp = self.imp();

        // Add launch Zandronum action
        let launch_action = gio::ActionEntry::<ZLWindow>::builder("launch-zandronum")
            .activate(clone!(@weak self as obj => move |_, _, _| {
                obj.set_sensitive(false);

                if let Err(launch_error) = obj.launch_zandronum() {
                    obj.set_sensitive(true);

                    let error_dialog = adw::MessageDialog::new(
                        Some(&obj),
                        Some("Error"),
                        Some(&launch_error.to_string())
                    );

                    error_dialog.add_responses(&[("close", "_Close")]);

                    error_dialog.present();
                } else {
                    obj.close();
                }
            }))
            .build();

        // Add reset widgets action
        let reset_action = gio::ActionEntry::<ZLWindow>::builder("reset-widgets")
            .activate(clone!(@weak self as obj, @weak imp => move |_, _, _| {
                let reset_dialog = adw::MessageDialog::new(
                    Some(&obj),
                    Some("Reset Parameters?"),
                    Some("Reset all parameters to their default values.")
                );
    
                reset_dialog.add_responses(&[("cancel", "_Cancel"), ("reset", "_Reset")]);
                reset_dialog.set_default_response(Some("reset"));
    
                reset_dialog.set_response_appearance("reset", adw::ResponseAppearance::Destructive);
    
                reset_dialog.choose(
                    None::<&gio::Cancellable>,
                    clone!(@weak imp => move |response| {
                        if response == "reset" {
                            imp.iwad_comborow.set_selected(0);
                            imp.pwad_filerow.set_paths(glib::StrV::new());
                            imp.params_entryrow.set_text("");
                        }
                    })
                );
            }))
            .build();

        // Add show preferences action
        let prefs_action = gio::ActionEntry::<ZLWindow>::builder("show-preferences")
            .activate(clone!(@weak imp => move |_, _, _| {
                imp.prefs_window.present();
            }))
            .build();

        // Add show preferences action
        let cheats_action = gio::ActionEntry::<ZLWindow>::builder("show-cheats")
            .activate(clone!(@weak imp => move |_, _, _| {
                imp.cheats_window.present();
            }))
            .build();

        // Add actions to window
        self.add_action_entries([launch_action, reset_action, prefs_action, cheats_action]);
    }

    //-----------------------------------
    // Setup shortcuts
    //-----------------------------------
    fn setup_shortcuts(&self) {
        // Create shortcut controller
        let controller = gtk::ShortcutController::new();

        // Add launch Zandronum shortcut
        controller.add_shortcut(gtk::Shortcut::new(
            gtk::ShortcutTrigger::parse_string("<ctrl>Return|<ctrl>KP_Enter"),
            Some(gtk::NamedAction::new("win.launch-zandronum"))
        ));

        // Add reset widgets shortcut
        controller.add_shortcut(gtk::Shortcut::new(
            gtk::ShortcutTrigger::parse_string("<ctrl>R"),
            Some(gtk::NamedAction::new("win.reset-widgets"))
        ));

        // Add show preferences shortcut
        controller.add_shortcut(gtk::Shortcut::new(
            gtk::ShortcutTrigger::parse_string("<ctrl>comma"),
            Some(gtk::NamedAction::new("win.show-preferences"))
        ));

        // Add show cheats shortcut
        controller.add_shortcut(gtk::Shortcut::new(
            gtk::ShortcutTrigger::parse_string("F1"),
            Some(gtk::NamedAction::new("win.show-cheats"))
        ));

        // Add shortcut controller to window
        self.add_controller(controller);
    }

    //-----------------------------------
    // Launch Zandronum function
    //-----------------------------------
    fn launch_zandronum(&self) -> Result<bool, LaunchError> {
        let imp = self.imp();

        let prefs = imp.prefs_window.imp();

        // Return with error if Zandronum executable does not exist
        let exec_file = prefs.exec_filerow.path();

        if Path::new(&exec_file).try_exists().unwrap_or_default() == false {
            return Err(LaunchError::new("Zandronum executable file not found"))
        }

        // Initialize Zandronum command line with executable
        let mut cmdline = exec_file;

        // Get selected IWAD - return with error if none
        let Some(iwad) = imp.iwad_comborow.selected_iwad() else {
            return Err(LaunchError::new("No IWAD file specified"));
        };

        // Return with error if IWAD file does not exist
        let iwad_file = Path::new(&prefs.iwad_filerow.path()).join(&iwad.iwad());

        if iwad_file.try_exists().unwrap_or_default() == false {
            return Err(LaunchError::new(&format!("IWAD file '{}' not found", iwad.iwad())))
        }

        // Add IWAD file to command line
        cmdline += &format!(" -iwad \"{}\"", iwad_file.display());

        // Add PWAD files to command line
        for pwad_file in imp.pwad_filerow.paths() {
            if Path::new(&pwad_file).try_exists().unwrap_or_default() == true {
                cmdline += &format!(" -file \"{}\"", pwad_file);
            }
        }

        // Add extra parameters to command line
        if imp.params_entryrow.text() != "" {
            cmdline += &format!(" {}", imp.params_entryrow.text());
        }

        // Add mod files (hi-res graphics) to command line
        let mut mod_files: Vec<String> = vec![];

        if prefs.texture_switchrow.is_active() {
            mod_files.extend(iwad.textures());
        }

        if prefs.object_switchrow.is_active() {
            mod_files.extend(iwad.objects());
        }

        if prefs.monster_switchrow.is_active() {
            mod_files.extend(iwad.monsters());
        }

        if prefs.menu_switchrow.is_active() {
            mod_files.extend(iwad.menus());
        }

        if prefs.hud_switchrow.is_active() {
            mod_files.extend(iwad.hud());
        }

        for modd in mod_files {
            let mod_file = Path::new(&prefs.mods_filerow.path()).join(&modd);

            if Path::new(&mod_file).try_exists().unwrap_or_default() == true {
                cmdline += &format!(" -file \"{}\"", mod_file.display());
            }
        }

        // Launch Zandronum
        if let Some(params) = shlex::split(&cmdline).filter(|params| !params.is_empty()) {
            Command::new(&params[0])
                .args(&params[1..])
                .spawn()
                .unwrap();
        }

        Ok(true)
    }
}
