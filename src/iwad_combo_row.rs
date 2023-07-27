use gtk::{gio, glib};
use adw::subclass::prelude::*;
use adw::prelude::*;
use glib::once_cell::sync::OnceCell;

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
    #[derive(Default, gtk::CompositeTemplate)]
    #[template(resource = "/com/github/ZandronumLauncher/ui/iwad_combo_row.ui")]
    pub struct IWadComboRow {
        #[template_child]
        pub model: TemplateChild<gio::ListStore>,

        pub iwads: OnceCell<Vec<IWadObject>>,
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
        @extends adw::ComboRow, adw::ActionRow, adw::PreferencesRow, gtk::ListBoxRow, gtk::Widget,
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

        let mut iwads: Vec<IWadObject> = vec![];

        iwads.push(IWadObject::new(
            "The Ultimate Doom",
            "doom.wad",
            &["hires-doom-a.pk3", "hires-doom-b.pk3"],
            &["objects.pk3"],
            &["monsters.pk3"],
            &["jfo-udoom.pk3"],
            &["hud-stuff.pk3"]
        ));

        iwads.push(IWadObject::new(
            "Doom II: Hell on Earth",
            "doom2.wad",
            &["hires-doom-a.pk3", "hires-doom-b.pk3", "hires-doom2.pk3"],
            &["objects.pk3"],
            &["monsters.pk3"],
            &["jfo-doom2.pk3"],
            &["hud-stuff.pk3"]
        ));

        iwads.push(IWadObject::new(
            "Final Doom - The Plutonia Experiment",
            "plutonia.wad",
            &["hires-doom-a.pk3", "hires-doom-b.pk3", "hires-doom2.pk3", "hires-plut.pk3"],
            &["objects.pk3"],
            &["monsters.pk3"],
            &["jfo-plut.pk3"],
            &["hud-stuff.pk3"]
        ));

        iwads.push(IWadObject::new(
            "Final Doom - TNT: Evilution",
            "tnt.wad",
            &["hires-doom-a.pk3", "hires-doom-b.pk3", "hires-doom2.pk3", "hires-tnt.pk3"],
            &["objects.pk3"],
            &["monsters.pk3"],
            &["jfo-tnt.pk3"],
            &["hud-stuff.pk3"]
        ));

        iwads.push(IWadObject::new(
            "Freedoom Phase 1",
            "freedoom1.wad",
            &[],
            &[],
            &[],
            &[],
            &[]
        ));

        iwads.push(IWadObject::new(
            "Freedoom Phase 2",
            "freedoom2.wad",
            &[],
            &[],
            &[],
            &[],
            &[]
        ));

        iwads.push(IWadObject::new(
            "Heretic",
            "heretic.wad",
            &["hires-heretic.pk3"],
            &[],
            &[],
            &[],
            &[]
        ));

        iwads.push(IWadObject::new(
            "Hexen",
            "hexen.wad",
            &["hires-hexen.pk3"],
            &[],
            &[],
            &[],
            &[]
        ));

        imp.iwads.set(iwads).unwrap();
    }

    //-----------------------------------
    // Public populate function
    //-----------------------------------
    pub fn populate(&self, folder: &str) {
        let imp = self.imp();

        let options = MatchOptions {
            case_sensitive: false,
            require_literal_separator: false,
            require_literal_leading_dot: false
        };

        if let Ok(entries) = glob_with(&format!("{folder}/*.wad"), options) {
            // Get list of IWADs in folder
            if let Some(iwads) = imp.iwads.get() {
                let mut iwad_objects: Vec<IWadObject> = entries.into_iter()
                    .flatten()
                    .filter_map(|entry| {
                        iwads.clone().into_iter()
                            .find(|iwad| {
                                if let Some(file) = entry.file_name() {
                                    if iwad.iwad() == file.to_string_lossy() {
                                        return true
                                    }
                                }

                                false
                            })
                    })
                    .collect();

                iwad_objects.sort_unstable_by(|a, b| a.name().cmp(&b.name()));

                // Add IWADs to combo row
                imp.model.splice(0, imp.model.n_items(), &iwad_objects);
            }
        }
    }

    //-----------------------------------
    // Public set selected iwad file function
    //-----------------------------------
    pub fn set_selected_iwad_file(&self, iwad_file: &str) {
        let index = self.imp().model.find_with_equal_func(|iwad| {
            let iwad = iwad.downcast_ref::<IWadObject>()
                .expect("Must be a 'IWadObject'");

            iwad.iwad() == iwad_file
        });

        if let Some(index) = index {
            self.set_selected(index);
        }
    }

    //-----------------------------------
    // Public selected iwad function
    //-----------------------------------
    pub fn selected_iwad(&self) -> Option<IWadObject> {
        self.selected_item()
            .and_downcast::<IWadObject>()
    }
}
