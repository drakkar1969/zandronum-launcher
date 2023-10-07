use gtk::{gio, glib};
use gtk::prelude::*;
use adw::subclass::prelude::*;

use crate::window::ZLWindow;

//------------------------------------------------------------------------------
// MODULE: ZLApplication
//------------------------------------------------------------------------------
mod imp {
    use super::*;

    //-----------------------------------
    // Private structure
    //-----------------------------------
    #[derive(Default)]
    pub struct ZLApplication {}

    //-----------------------------------
    // Subclass
    //-----------------------------------
    #[glib::object_subclass]
    impl ObjectSubclass for ZLApplication {
        const NAME: &'static str = "ZLApplication";
        type Type = super::ZLApplication;
        type ParentType = adw::Application;
    }

    impl ObjectImpl for ZLApplication {
        //-----------------------------------
        // Constructor
        //-----------------------------------
        fn constructed(&self) {
            self.parent_constructed();

            self.obj().setup_actions();
        }
    }

    impl ApplicationImpl for ZLApplication {
        //-----------------------------------
        // Activate handler
        //-----------------------------------
        fn activate(&self) {
            let application = self.obj();

            // Show main window
            let window = if let Some(window) = application.active_window() {
                window
            } else {
                let window = ZLWindow::new(&*application);
                window.upcast()
            };

            window.present();
        }
    }

    impl GtkApplicationImpl for ZLApplication {}
    impl AdwApplicationImpl for ZLApplication {}

    impl ZLApplication {}
}

//------------------------------------------------------------------------------
// IMPLEMENTATION: ZLApplication
//------------------------------------------------------------------------------
glib::wrapper! {
    pub struct ZLApplication(ObjectSubclass<imp::ZLApplication>)
        @extends gio::Application, gtk::Application, adw::Application,
        @implements gio::ActionGroup, gio::ActionMap;
}

impl ZLApplication {
    //-----------------------------------
    // New function
    //-----------------------------------
    pub fn new(application_id: &str, flags: &gio::ApplicationFlags) -> Self {
        glib::Object::builder()
            .property("application-id", application_id)
            .property("flags", flags)
            .build()
    }

    //-----------------------------------
    // Setup actions
    //-----------------------------------
    fn setup_actions(&self) {
        let quit_action = gio::ActionEntry::builder("quit-app")
            .activate(move |app: &Self, _, _| app.quit())
            .build();
        
        let about_action = gio::ActionEntry::builder("show-about")
            .activate(move |app: &Self, _, _| app.show_about())
            .build();

        self.add_action_entries([quit_action, about_action]);

        self.set_accels_for_action("app.quit-app", &["<ctrl>Q"]);
    }

    //-----------------------------------
    // Show about window
    //-----------------------------------
    fn show_about(&self) {
        let window = self.active_window().unwrap();

        let about_window = adw::AboutWindow::builder()
            .transient_for(&window)
            .application_name("Zandronum Launcher")
            .application_icon("zandronum")
            .developer_name("draKKar1969")
            .version("2.0.3")
            .website("https://github.com/drakkar1969/zandronum-launcher/")
            .developers(vec!["draKKar1969"])
            .designers(vec!["draKKar1969"])
            .copyright("© 2023 draKKar1969")
            .license_type(gtk::License::Gpl30)
            .build();

        about_window.present();
    }
}
