use std::cell::{Cell, RefCell};

use gtk::glib;
use adw::subclass::prelude::*;
use gtk::prelude::*;

//------------------------------------------------------------------------------
// ENUM: SelectType
//------------------------------------------------------------------------------
#[derive(Debug, Eq, PartialEq, Clone, Copy, glib::Enum)]
#[repr(u32)]
#[enum_type(name = "SelectType")]
pub enum SelectType {
    File = 0,
    Multiple = 1,
    Folder = 2,
}

impl Default for SelectType {
    fn default() -> Self {
        SelectType::File
    }
}

//------------------------------------------------------------------------------
// MODULE: FileSelectRow
//------------------------------------------------------------------------------
mod imp {
    use super::*;

    //-----------------------------------
    // Private structure
    //-----------------------------------
    #[derive(Default, gtk::CompositeTemplate, glib::Properties)]
    #[template(resource = "/com/github/ZandronumLauncher/ui/file_select_row.ui")]
    #[properties(wrapper_type = super::FileSelectRow)]
    pub struct FileSelectRow {
        #[template_child]
        pub label: TemplateChild<gtk::Label>,
        #[template_child]
        pub image: TemplateChild<gtk::Image>,

        #[property(get, set = Self::set_select, construct, builder(SelectType::default()))]
        select: Cell<SelectType>,
        #[property(get, set = Self::set_icon, nullable)]
        icon: RefCell<Option<String>>,
    }

    //-----------------------------------
    // Subclass
    //-----------------------------------
    #[glib::object_subclass]
    impl ObjectSubclass for FileSelectRow {
        const NAME: &'static str = "FileSelectRow";
        type Type = super::FileSelectRow;
        type ParentType = adw::ActionRow;

        fn class_init(klass: &mut Self::Class) {
            klass.bind_template();
        }

        fn instance_init(obj: &glib::subclass::InitializingObject<Self>) {
            obj.init_template();
        }
    }

    impl ObjectImpl for FileSelectRow {
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
        }
    }

    impl WidgetImpl for FileSelectRow {}
    impl ListBoxRowImpl for FileSelectRow {}
    impl PreferencesRowImpl for FileSelectRow {}
    impl ActionRowImpl for FileSelectRow {}
    impl FileSelectRow {
        //-----------------------------------
        // Select property custom setter
        //-----------------------------------
        fn set_select(&self, select: SelectType) {
            if self.obj().icon().is_none() {
                if select == SelectType::Folder {
                    self.image.set_icon_name(Some("folder-symbolic"));
                } else {
                    self.image.set_icon_name(Some("document-open-symbolic"));
                }
            }

            self.select.replace(select);
        }

        //-----------------------------------
        // Icon property custom setter
        //-----------------------------------
        fn set_icon(&self, icon: Option<&str>) {
            if icon.is_some() {
                self.image.set_icon_name(icon);
            } else {
                if self.obj().select() == SelectType::Folder {
                    self.image.set_icon_name(Some("folder-symbolic"));
                } else {
                    self.image.set_icon_name(Some("document-open-symbolic"));
                }
            }

            self.icon.replace(icon.map(|icon| icon.to_string()));
        }
    }
}

//------------------------------------------------------------------------------
// IMPLEMENTATION: FileSelectRow
//------------------------------------------------------------------------------
glib::wrapper! {
    pub struct FileSelectRow(ObjectSubclass<imp::FileSelectRow>)
        @extends adw::ActionRow, adw::PreferencesRow, gtk::ListBoxRow, gtk::Widget,
        @implements gtk::Accessible, gtk::Actionable, gtk::Buildable, gtk::ConstraintTarget;
}

impl FileSelectRow {
    //-----------------------------------
    // New function
    //-----------------------------------
    pub fn new() -> Self {
        glib::Object::builder().build()
    }
}
