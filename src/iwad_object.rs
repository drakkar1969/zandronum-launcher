use std::cell::RefCell;

use gtk::glib;
use gtk::subclass::prelude::*;
use gtk::prelude::ObjectExt;

//------------------------------------------------------------------------------
// MODULE: IWadObject
//------------------------------------------------------------------------------
mod imp {
    use super::*;

    //-----------------------------------
    // Private structure
    //-----------------------------------
    #[derive(Default, glib::Properties)]
    #[properties(wrapper_type = super::IWadObject)]
    pub struct IWadObject {
        #[property(get, set)]
        name: RefCell<String>,
        #[property(get, set)]
        iwad: RefCell<String>,
        #[property(get, set)]
        textures: RefCell<Vec<String>>,
        #[property(get, set)]
        objects: RefCell<Vec<String>>,
        #[property(get, set)]
        monsters: RefCell<Vec<String>>,
        #[property(get, set)]
        menus: RefCell<Vec<String>>,
        #[property(get, set)]
        hud: RefCell<Vec<String>>,
    }

    //-----------------------------------
    // Subclass
    //-----------------------------------
    #[glib::object_subclass]
    impl ObjectSubclass for IWadObject {
        const NAME: &'static str = "IWadObject";
        type Type = super::IWadObject;
    }

    impl ObjectImpl for IWadObject {
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
// IMPLEMENTATION: IWadObject
//------------------------------------------------------------------------------
glib::wrapper! {
    pub struct IWadObject(ObjectSubclass<imp::IWadObject>);
}

impl IWadObject {
    //-----------------------------------
    // New function
    //-----------------------------------
    pub fn new(name: &str, iwad: &str, textures: &[&str], objects: &[&str], monsters: &[&str], menus: &[&str], hud: &[&str]) -> Self {
        // Build PropObject
        glib::Object::builder()
            .property("name", name)
            .property("iwad", iwad)
            .property("textures", textures)
            .property("objects", objects)
            .property("monsters", monsters)
            .property("menus", menus)
            .property("hud", hud)
            .build()
    }
}
