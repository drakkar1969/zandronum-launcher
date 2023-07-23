use std::cell::RefCell;

use gtk::glib;
use gtk::subclass::prelude::*;
use gtk::prelude::ObjectExt;

//------------------------------------------------------------------------------
// MODULE: CheatObject
//------------------------------------------------------------------------------
mod imp {
    use super::*;

    //-----------------------------------
    // Private structure
    //-----------------------------------
    #[derive(Default, glib::Properties)]
    #[properties(wrapper_type = super::CheatObject)]
    pub struct CheatObject {
        #[property(get, set)]
        label: RefCell<String>,
        #[property(get, set)]
        value: RefCell<String>,
    }

    //-----------------------------------
    // Subclass
    //-----------------------------------
    #[glib::object_subclass]
    impl ObjectSubclass for CheatObject {
        const NAME: &'static str = "CheatObject";
        type Type = super::CheatObject;
    }

    impl ObjectImpl for CheatObject {
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
    }
}

//------------------------------------------------------------------------------
// IMPLEMENTATION: CheatObject
//------------------------------------------------------------------------------
glib::wrapper! {
    pub struct CheatObject(ObjectSubclass<imp::CheatObject>);
}

impl CheatObject {
    //-----------------------------------
    // New function
    //-----------------------------------
    pub fn new(label: &str, value: &str) -> Self {
        // Build PropObject
        glib::Object::builder()
            .property("label", label)
            .property("value", value)
            .build()
    }
}
