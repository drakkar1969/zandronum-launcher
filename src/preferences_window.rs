use gtk::glib;
use adw::subclass::prelude::*;
use adw::prelude::*;
use glib::clone;

use crate::file_select_row::FileSelectRow;

//------------------------------------------------------------------------------
// MODULE: PreferencesWindow
//------------------------------------------------------------------------------
mod imp {
    use super::*;

    //-----------------------------------
    // Private structure
    //-----------------------------------
    #[derive(Default, gtk::CompositeTemplate)]
    #[template(resource = "/com/github/ZandronumLauncher/ui/preferences_window.ui")]
    pub struct PreferencesWindow {
        #[template_child]
        pub exec_filerow: TemplateChild<FileSelectRow>,
        #[template_child]
        pub iwad_filerow: TemplateChild<FileSelectRow>,
        #[template_child]
        pub pwad_filerow: TemplateChild<FileSelectRow>,
        #[template_child]
        pub mods_filerow: TemplateChild<FileSelectRow>,

        #[template_child]
        pub texture_switchrow: TemplateChild<adw::SwitchRow>,
        #[template_child]
        pub object_switchrow: TemplateChild<adw::SwitchRow>,
        #[template_child]
        pub monster_switchrow: TemplateChild<adw::SwitchRow>,
        #[template_child]
        pub menu_switchrow: TemplateChild<adw::SwitchRow>,
        #[template_child]
        pub hud_switchrow: TemplateChild<adw::SwitchRow>,

        #[template_child]
        pub reset_button: TemplateChild<gtk::Button>,
    }

    //-----------------------------------
    // Subclass
    //-----------------------------------
    #[glib::object_subclass]
    impl ObjectSubclass for PreferencesWindow {
        const NAME: &'static str = "PreferencesWindow";
        type Type = super::PreferencesWindow;
        type ParentType = adw::PreferencesWindow;

        fn class_init(klass: &mut Self::Class) {
            klass.bind_template();
        }

        fn instance_init(obj: &glib::subclass::InitializingObject<Self>) {
            obj.init_template();
        }
    }

    impl ObjectImpl for PreferencesWindow {
        //-----------------------------------
        // Constructor
        //-----------------------------------
        fn constructed(&self) {
            self.parent_constructed();

            self.obj().setup_signals();
        }
    }

    impl WidgetImpl for PreferencesWindow {}
    impl WindowImpl for PreferencesWindow {}
    impl AdwWindowImpl for PreferencesWindow {} 
    impl PreferencesWindowImpl for PreferencesWindow {}
}

//------------------------------------------------------------------------------
// IMPLEMENTATION: PreferencesWindow
//------------------------------------------------------------------------------
glib::wrapper! {
    pub struct PreferencesWindow(ObjectSubclass<imp::PreferencesWindow>)
        @extends adw::Window, gtk::Window, gtk::Widget,
        @implements gtk::Accessible, gtk::Buildable, gtk::ConstraintTarget, gtk::Native, gtk::Root, gtk::ShortcutManager;
}

impl PreferencesWindow {
    //-----------------------------------
    // New function
    //-----------------------------------
    pub fn new() -> Self {
        glib::Object::builder().build()
    }

    //-----------------------------------
    // Setup signals
    //-----------------------------------
    fn setup_signals(&self) {
        let imp = self.imp();

        // Preferences reset button clicked signal
        imp.reset_button.connect_clicked(clone!(@weak self as obj, @weak imp => move |_| {
            let reset_dialog = adw::AlertDialog::new(
                Some("Reset Preferences?"),
                Some("Reset all preferences to their default values.")
            );

            reset_dialog.add_responses(&[("cancel", "_Cancel"), ("reset", "_Reset")]);
            reset_dialog.set_default_response(Some("reset"));

            reset_dialog.set_response_appearance("reset", adw::ResponseAppearance::Destructive);

            reset_dialog.choose(
                &obj,
                None::<&gio::Cancellable>,
                clone!(@weak imp => move |response| {
                    if response == "reset" {
                        imp.exec_filerow.reset_paths();
                        imp.iwad_filerow.reset_paths();
                        imp.pwad_filerow.reset_paths();
                        imp.mods_filerow.reset_paths();

                        imp.texture_switchrow.set_active(true);
                        imp.object_switchrow.set_active(true);
                        imp.monster_switchrow.set_active(true);
                        imp.menu_switchrow.set_active(true);
                        imp.hud_switchrow.set_active(true);
                    }
                })
            );
        }));
    }
}
