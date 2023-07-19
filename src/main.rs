mod app;
mod window;
mod iwad_combo_row;
mod iwad_object;

use gtk::{gio, glib};
use gtk::prelude::*;

use app::ZLApplication;

const APP_ID: &str = "com.github.ZandronumLauncher";

fn main() -> glib::ExitCode {
    // Register and include resources
    gio::resources_register_include!("resources.gresource")
        .expect("Failed to register resources");

    // Run app
    let app = ZLApplication::new(APP_ID, &gio::ApplicationFlags::empty());

    app.run()
}
