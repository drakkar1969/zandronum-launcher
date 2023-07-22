use gtk::{gio, glib};
use adw::subclass::prelude::*;
use gtk::prelude::*;
use glib::clone;
use glib::once_cell::sync::OnceCell;

use crate::APP_ID;
use crate::ZLApplication;
use crate::iwad_combo_row::IWadComboRow;
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
        pub prefs_window: TemplateChild<PreferencesWindow>,

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
        // Constructor
        //-----------------------------------
        fn constructed(&self) {
            let obj = self.obj();

            self.parent_constructed();

            obj.init_gsettings();
            obj.load_gsettings();

            obj.setup_widgets();
            obj.setup_signals();
            obj.setup_actions();
            obj.setup_shortcuts();
        }

        //-----------------------------------
        // Destructor
        //-----------------------------------
        // fn dispose(&self) {
        //     self.package_view_popup.get().unwrap().unparent();
        // }
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
            // Save gsettings
            gsettings.apply();
        }
    }

    //-----------------------------------
    // Setup widgets
    //-----------------------------------
    fn setup_widgets(&self) {
        let imp = self.imp();

        // Populate IWAD combo row
        imp.iwad_comborow.populate(&imp.prefs_window.iwad_folder());

        // Set current folder for PWAD select row
        let folder = imp.prefs_window.pwad_folder();

        if folder == "" {
            imp.pwad_filerow.set_current_folder(None::<String>);
        } else {
            imp.pwad_filerow.set_current_folder(Some(folder));
        }

        // Set preferences window parent
        imp.prefs_window.set_transient_for(Some(self));
    }

    //-----------------------------------
    // Setup signals
    //-----------------------------------
    fn setup_signals(&self) {
        let imp = self.imp();

        // Preferences window IWAD folders property notify signal
        imp.prefs_window.connect_iwad_folder_notify(clone!(@weak imp => move |_| {
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
    // Setup actions
    //-----------------------------------
    fn setup_actions(&self) {
        let imp = self.imp();

        // Add show preferences action
        let prefs_action = gio::ActionEntry::<ZLWindow>::builder("show-preferences")
            .activate(clone!(@weak imp => move |_, _, _| {
                imp.prefs_window.present();
            }))
            .build();

        // Add preference actions to window
        self.add_action_entries([prefs_action]);
    }

    //-----------------------------------
    // Setup shortcuts
    //-----------------------------------
    fn setup_shortcuts(&self) {
        // Create shortcut controller
        let controller = gtk::ShortcutController::new();

        // Add show preferences shortcut
        controller.add_shortcut(gtk::Shortcut::new(
            gtk::ShortcutTrigger::parse_string("<ctrl>comma"),
            Some(gtk::NamedAction::new("win.show-preferences"))
        ));

        // Add shortcut controller to window
        self.add_controller(controller);
    }
}
