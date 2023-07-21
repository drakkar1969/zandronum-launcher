use gtk::{gio, glib};
use adw::subclass::prelude::*;
use gtk::prelude::*;
use glib::clone;

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
        pub prefs_window: TemplateChild<PreferencesWindow>,
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

            obj.setup_widgets();
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
    impl WindowImpl for ZLWindow {}
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
