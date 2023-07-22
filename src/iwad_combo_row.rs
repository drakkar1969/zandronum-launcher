use std::cell::RefCell;

use gtk::{gio, glib};
use adw::subclass::prelude::*;
use gtk::prelude::*;

use glob::{glob_with, MatchOptions};

use crate::iwad_object::IWadObject;

//------------------------------------------------------------------------------
// MODULE: IWadComboRow
//------------------------------------------------------------------------------
mod imp {
    use super::*;

    //-----------------------------------
    // Private structure
    //-----------------------------------
    #[derive(Default, gtk::CompositeTemplate, glib::Properties)]
    #[template(resource = "/com/github/ZandronumLauncher/ui/iwad_combo_row.ui")]
    #[properties(wrapper_type = super::IWadComboRow)]
    pub struct IWadComboRow {
        #[template_child]
        pub model: TemplateChild<gio::ListStore>,

        #[property(get, set)]
        icon: RefCell<String>,

        pub iwads: RefCell<Vec<IWadObject>>,
    }

    //-----------------------------------
    // Subclass
    //-----------------------------------
    #[glib::object_subclass]
    impl ObjectSubclass for IWadComboRow {
        const NAME: &'static str = "IWadComboRow";
        type Type = super::IWadComboRow;
        type ParentType = adw::ComboRow;

        fn class_init(klass: &mut Self::Class) {
            IWadObject::ensure_type();

            klass.bind_template();
        }

        fn instance_init(obj: &glib::subclass::InitializingObject<Self>) {
            obj.init_template();
        }
    }

    impl ObjectImpl for IWadComboRow {
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

            obj.setup_data();
        }
    }

    impl WidgetImpl for IWadComboRow {}
    impl ListBoxRowImpl for IWadComboRow {}
    impl PreferencesRowImpl for IWadComboRow {}
    impl ActionRowImpl for IWadComboRow {}
    impl ComboRowImpl for IWadComboRow {}
}

//------------------------------------------------------------------------------
// IMPLEMENTATION: IWadComboRow
//------------------------------------------------------------------------------
glib::wrapper! {
    pub struct IWadComboRow(ObjectSubclass<imp::IWadComboRow>)
        @extends adw::ActionRow, adw::PreferencesRow, gtk::ListBoxRow, gtk::Widget,
        @implements gtk::Accessible, gtk::Actionable, gtk::Buildable, gtk::ConstraintTarget;
}

impl IWadComboRow {
    //-----------------------------------
    // New function
    //-----------------------------------
    pub fn new() -> Self {
        glib::Object::builder().build()
    }

    //-----------------------------------
    // Setup data
    //-----------------------------------
    fn setup_data(&self) {
        let imp = self.imp();

        let mut iwads = imp.iwads.borrow_mut();

        iwads.push(IWadObject::new(
            "The Ultimate Doom",
            "doom.wad"
        ));

        iwads.push(IWadObject::new(
            "Doom II: Hell on Earth",
            "doom2.wad"
        ));

        iwads.push(IWadObject::new(
            "Final Doom - The Plutonia Experiment",
            "plutonia.wad"
        ));

        iwads.push(IWadObject::new(
            "Final Doom - TNT: Evilution",
            "tnt.wad"
        ));

        iwads.push(IWadObject::new(
            "Freedoom Phase 1",
            "freedoom1.wad"
        ));

        iwads.push(IWadObject::new(
            "Freedoom Phase 2",
            "freedoom2.wad"
        ));

        iwads.push(IWadObject::new(
            "Heretic",
            "heretic.wad"
        ));

        iwads.push(IWadObject::new(
            "Hexen",
            "hexen.wad"
        ));
    }

    //-----------------------------------
    // Public populate function
    //-----------------------------------
    pub fn populate(&self, folders: &Vec<String>) {
        let imp = self.imp();

        let options = MatchOptions {
            case_sensitive: false,
            require_literal_separator: false,
            require_literal_leading_dot: false
        };

        for folder in folders {
            if let Ok(entries) = glob_with(&format!("{folder}/*.wad"), options) {
                let iwads = imp.iwads.borrow();

                let files: Vec<IWadObject> = entries.into_iter()
                    .flatten()
                    .filter_map(|entry| {
                        iwads.clone().into_iter()
                            .find(|iwad| {
                                if let Some(file) = entry.as_path().file_name() {
                                    if iwad.iwad() == file.to_string_lossy() {
                                        return true
                                    }
                                }

                                false
                            })
                    })
                    .collect();

                imp.model.splice(0, imp.model.n_items(), &files);
            }
        }
    }
}
