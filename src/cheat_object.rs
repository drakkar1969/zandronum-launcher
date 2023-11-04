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

    #[glib::derived_properties]
    impl ObjectImpl for CheatObject {}
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
        // Build CheatObject
        glib::Object::builder()
            .property("label", label)
            .property("value", value)
            .build()
    }
}
