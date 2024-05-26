use gtk::{gio, glib};
use adw::prelude::*;
use adw::subclass::prelude::*;

use crate::window::ZLWindow;

//------------------------------------------------------------------------------
// MODULE: LauncherApplication
//------------------------------------------------------------------------------
mod imp {
    use super::*;

    //-----------------------------------
    // Private structure
    //-----------------------------------
    #[derive(Default)]
    pub struct LauncherApplication {}

    //-----------------------------------
    // Subclass
    //-----------------------------------
    #[glib::object_subclass]
    impl ObjectSubclass for LauncherApplication {
        const NAME: &'static str = "LauncherApplication";
        type Type = super::LauncherApplication;
        type ParentType = adw::Application;
    }

    impl ObjectImpl for LauncherApplication {
        //-----------------------------------
        // Constructor
        //-----------------------------------
        fn constructed(&self) {
            self.parent_constructed();

            self.obj().setup_actions();
        }
    }

    impl ApplicationImpl for LauncherApplication {
        //-----------------------------------
        // Activate handler
        //-----------------------------------
        fn activate(&self) {
            let application = self.obj();

            // Show main window
            let window = if let Some(window) = application.active_window() {
                window
            } else {
                let window = ZLWindow::new(&application);
                window.upcast()
            };

            window.present();
        }
    }

    impl GtkApplicationImpl for LauncherApplication {}
    impl AdwApplicationImpl for LauncherApplication {}

    impl LauncherApplication {}
}

//------------------------------------------------------------------------------
// IMPLEMENTATION: LauncherApplication
//------------------------------------------------------------------------------
glib::wrapper! {
    pub struct LauncherApplication(ObjectSubclass<imp::LauncherApplication>)
        @extends gio::Application, gtk::Application, adw::Application,
        @implements gio::ActionGroup, gio::ActionMap;
}

impl LauncherApplication {
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

        let about_dialog = adw::AboutDialog::builder()
            .application_name("Zandronum Launcher")
            .application_icon("zandronum")
            .developer_name("draKKar1969")
            .version("2.0.5")
            .website("https://github.com/drakkar1969/zandronum-launcher/")
            .developers(vec!["draKKar1969"])
            .designers(vec!["draKKar1969"])
            .copyright("© 2023 draKKar1969")
            .license_type(gtk::License::Gpl30)
            .build();

        about_dialog.present(&window);
    }
}
