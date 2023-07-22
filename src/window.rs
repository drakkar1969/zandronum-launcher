use std::cell::RefCell;

use gtk::{gio, glib};
use adw::subclass::prelude::*;
use adw::prelude::*;
use glib::clone;
use glib::once_cell::sync::OnceCell;

use crate::APP_ID;
use crate::ZLApplication;
use crate::iwad_combo_row::IWadComboRow;
use crate::iwad_object::IWadObject;
use crate::file_select_row::FileSelectRow;
use crate::preferences_window::PreferencesWindow;

//------------------------------------------------------------------------------
// MODULE: ZLWindow
//------------------------------------------------------------------------------
mod imp {
    use super::*;

    //-----------------------------------
    // Private structure
    //-----------------------------------
    #[derive(Default, gtk::CompositeTemplate, glib::Properties)]
    #[template(resource = "/com/github/ZandronumLauncher/ui/window.ui")]
    #[properties(wrapper_type = super::ZLWindow)]
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

        #[property(get, set)]
        selected_iwad: RefCell<String>,
        #[property(get, set)]
        pwad_files: RefCell<Vec<String>>,
        #[property(get, set)]
        extra_params: RefCell<String>,

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

            klass.bind_template();
        }

        fn instance_init(obj: &glib::subclass::InitializingObject<Self>) {
            obj.init_template();
        }
    }

    impl ObjectImpl for ZLWindow {
        //-----------------------------------
        // Default property functions
        //-----------------------------------
        fn properties() -> &'static [glib::ParamSpec] {
            Self::derived_properties()
        }

        fn set_property(&self, id: usize, value: &glib::Value, pspec: &glib::ParamSpec) {
            self.derived_set_property(id, value, pspec)
        }

        fn property(&self, id: usize, pspec: &glib::ParamSpec) -> glib::Value {
            self.derived_property(id, pspec)
        }

        //-----------------------------------
        // Constructor
        //-----------------------------------
        fn constructed(&self) {
            let obj = self.obj();

            self.parent_constructed();

            obj.setup_widgets();
            obj.setup_signals();

            obj.init_gsettings();
            obj.load_gsettings();

            obj.setup_actions();
            obj.setup_shortcuts();
        }
    }

    impl WidgetImpl for ZLWindow {}
    impl WindowImpl for ZLWindow {
        //-----------------------------------
        // Window close handler
        //-----------------------------------
        fn close_request(&self) -> glib::signal::Inhibit {
            self.obj().save_gsettings();

            glib::signal::Inhibit(false)
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

        // Bind properties to widgets
        self.bind_property("selected-iwad", &imp.iwad_comborow.get(), "selected")
            .transform_to(|binding, selected: String| {
                let combo_row = binding.target()
                    .and_downcast::<IWadComboRow>()
                    .expect("Must be a 'IWadComboRow'");

                combo_row.imp().model.find_with_equal_func(|iwad| {
                    let iwad = iwad.downcast_ref::<IWadObject>()
                        .expect("Must be a 'IWadObject'");

                    iwad.iwad() == selected
                })
            })
            .flags(glib::BindingFlags::SYNC_CREATE)
            .build();
        self.bind_property("pwad-files", &imp.pwad_filerow.get(), "files")
            .flags(glib::BindingFlags::SYNC_CREATE | glib::BindingFlags::BIDIRECTIONAL)
            .build();
        self.bind_property("extra-params", &imp.params_entryrow.get(), "text")
            .flags(glib::BindingFlags::SYNC_CREATE | glib::BindingFlags::BIDIRECTIONAL)
            .build();

        // Set preferences window parent
        imp.prefs_window.set_transient_for(Some(self));
    }

    //-----------------------------------
    // Setup signals
    //-----------------------------------
    fn setup_signals(&self) {
        let imp = self.imp();

        // Preferences window IWAD folders property notify signal
        imp.prefs_window.connect_iwad_folder_notify(clone!(@weak self as obj, @weak imp => move |_| {
            imp.iwad_comborow.populate(&imp.prefs_window.iwad_folder());
        }));

        // Preferences window IWAD folders property notify signal
        imp.prefs_window.connect_pwad_folder_notify(clone!(@weak imp => move |_| {
            let folder = imp.prefs_window.pwad_folder();

            if folder == "" {
                imp.pwad_filerow.set_current_folder(None::<String>);
            } else {
                imp.pwad_filerow.set_current_folder(Some(folder));
            }
        }));
    }

    //-----------------------------------
    // Init gsettings
    //-----------------------------------
    fn init_gsettings(&self) {
        let gsettings = gio::Settings::new(APP_ID);

        gsettings.delay();

        self.imp().gsettings.set(gsettings).unwrap();
    }

    //-----------------------------------
    // Load gsettings
    //-----------------------------------
    fn load_gsettings(&self) {
        let imp = self.imp();

        if let Some(gsettings) = imp.gsettings.get() {
            // Bind gsettings
            gsettings.bind("selected-iwad", self, "selected-iwad").build();
            gsettings.bind("pwad-files", self, "pwad-files").build();
            gsettings.bind("extra-parameters", self, "extra-params").build();

            gsettings.bind("executable-file", &imp.prefs_window.get(), "exec-file").build();
            gsettings.bind("iwad-folder", &imp.prefs_window.get(), "iwad-folder").build();
            gsettings.bind("pwad-folder", &imp.prefs_window.get(), "pwad-folder").build();
        }
    }

    //-----------------------------------
    // Save gsettings
    //-----------------------------------
    fn save_gsettings(&self) {
        let imp = self.imp();

        if let Some(gsettings) = imp.gsettings.get() {
            // Get selected IWAD
            if let Some(iwad) = imp.iwad_comborow.selected_item()
                .and_downcast::<IWadObject>()
            {
                self.set_selected_iwad(iwad.iwad());
            }

            // Save gsettings
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
                // obj.set_sensitive(false);
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
                            imp.pwad_filerow.set_files(vec![]);
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

        // Add actions to window
        self.add_action_entries([launch_action, reset_action, prefs_action]);
    }

    //-----------------------------------
    // Setup shortcuts
    //-----------------------------------
    fn setup_shortcuts(&self) {
        // Create shortcut controller
        let controller = gtk::ShortcutController::new();

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

        // Add shortcut controller to window
        self.add_controller(controller);
    }
}
