use std::cell::RefCell;

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
    #[derive(Default, gtk::CompositeTemplate, glib::Properties)]
    #[properties(wrapper_type = super::PreferencesWindow)]
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
        pub reset_button: TemplateChild<gtk::Button>,

        #[property(get, set)]
        exec_file: RefCell<String>,
        #[property(get, set)]
        iwad_folder: RefCell<String>,
        #[property(get, set)]
        pwad_folder: RefCell<String>,
        #[property(get, set)]
        mods_folder: RefCell<String>,

        #[property(get, set)]
        default_exec_file: RefCell<String>,
        #[property(get, set)]
        default_iwad_folder: RefCell<String>,
        #[property(get, set)]
        default_pwad_folder: RefCell<String>,
        #[property(get, set)]
        default_mods_folder: RefCell<String>,
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
            self.parent_constructed();

            let obj = self.obj();

            obj.setup_widgets();
            // obj.setup_actions();
            obj.setup_signals();
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
    // Setup widgets
    //-----------------------------------
    fn setup_widgets(&self) {
        let imp = self.imp();

        // Binding helper functions
        fn str_to_vec(string: &str) -> Vec<String> {
            if string == "" {
                vec![]
            } else {
                vec![string.to_string()]
            }
        }

        fn vec_to_str(vec: Vec<String>) -> String {
            if vec.is_empty() {
                "".to_string()
            } else {
                vec[0].to_string()
            }
            
        }

        // Bind properties to widgets
        self.bind_property("exec-file", &imp.exec_filerow.get(), "files")
            .transform_to(|_, folder| Some(str_to_vec(folder)))
            .transform_from(|_, files| Some(vec_to_str(files)))
            .flags(glib::BindingFlags::SYNC_CREATE | glib::BindingFlags::BIDIRECTIONAL)
            .build();
        self.bind_property("iwad-folder", &imp.iwad_filerow.get(), "files")
            .transform_to(|_, folder| Some(str_to_vec(folder)))
            .transform_from(|_, files| Some(vec_to_str(files)))
            .flags(glib::BindingFlags::SYNC_CREATE | glib::BindingFlags::BIDIRECTIONAL)
            .build();
        self.bind_property("pwad-folder", &imp.pwad_filerow.get(), "files")
            .transform_to(|_, folder| Some(str_to_vec(folder)))
            .transform_from(|_, files| Some(vec_to_str(files)))
            .flags(glib::BindingFlags::SYNC_CREATE | glib::BindingFlags::BIDIRECTIONAL)
            .build();
        self.bind_property("mods-folder", &imp.mods_filerow.get(), "files")
            .transform_to(|_, folder| Some(str_to_vec(folder)))
            .transform_from(|_, files| Some(vec_to_str(files)))
            .flags(glib::BindingFlags::SYNC_CREATE | glib::BindingFlags::BIDIRECTIONAL)
            .build();
    }

    //-----------------------------------
    // Setup signals
    //-----------------------------------
    fn setup_signals(&self) {
        let imp = self.imp();

        // Preferences reset button clicked signal
        imp.reset_button.connect_clicked(clone!(@weak self as obj, @weak imp => move |_| {
            let reset_dialog = adw::MessageDialog::new(
                Some(&obj),
                Some("Reset Preferences?"),
                Some("Reset all preferences to their default values.")
            );

            reset_dialog.add_responses(&[("cancel", "_Cancel"), ("reset", "_Reset")]);
            reset_dialog.set_default_response(Some("reset"));

            reset_dialog.set_response_appearance("reset", adw::ResponseAppearance::Destructive);

            reset_dialog.choose(
                None::<&gio::Cancellable>,
                clone!(@weak obj=> move |response| {
                    if response == "reset" {
                        obj.set_exec_file(obj.default_exec_file());
                        obj.set_iwad_folder(obj.default_iwad_folder());
                        obj.set_pwad_folder(obj.default_pwad_folder());
                        obj.set_mods_folder(obj.default_mods_folder());
                    }
                })
            );
        }));
    }
}
