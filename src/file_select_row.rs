use std::cell::{Cell, RefCell};

use gtk::{gio, glib};
use adw::subclass::prelude::*;
use gtk::prelude::*;
use glib::clone;
use glib::subclass::Signal;
use glib::once_cell::sync::Lazy;

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
        pub select_button: TemplateChild<gtk::Button>,
        #[template_child]
        pub label: TemplateChild<gtk::Label>,
        #[template_child]
        pub image: TemplateChild<gtk::Image>,
        #[template_child]
        pub clear_button: TemplateChild<gtk::Button>,

        #[property(get, set = Self::set_select, construct, builder(SelectType::default()))]
        select: Cell<SelectType>,
        #[property(get, set = Self::set_icon, nullable, construct)]
        icon: RefCell<Option<String>>,
        #[property(get, set = Self::set_can_clear, construct)]
        can_clear: Cell<bool>,

        #[property(get, set, default = "Select File", construct)]
        dialog_title: RefCell<String>,
        #[property(get, set, nullable, construct)]
        filter: RefCell<Option<gtk::FileFilter>>,

        pub base_folder: RefCell<Option<gio::File>>,
        pub files: RefCell<gio::ListStore>,
        pub default_file: RefCell<Option<gio::File>>,
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
        // Custom signals
        //-----------------------------------
        fn signals() -> &'static [Signal] {
            static SIGNALS: Lazy<Vec<Signal>> = Lazy::new(|| {
                vec![
                    Signal::builder("changed")
                        .build(),
                ]
            });
            SIGNALS.as_ref()
        }

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
            obj.setup_signals();
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
            if self.icon.borrow().is_none() {
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
                if self.select.get() == SelectType::Folder {
                    self.image.set_icon_name(Some("folder-symbolic"));
                } else {
                    self.image.set_icon_name(Some("document-open-symbolic"));
                }
            }

            self.icon.replace(icon.map(|icon| icon.to_string()));
        }

        //-----------------------------------
        // Can clear property custom setter
        //-----------------------------------
        fn set_can_clear(&self, can_clear: bool) {
            self.clear_button.set_visible(can_clear);

            self.can_clear.replace(can_clear);
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

    //-----------------------------------
    // Setup widgets
    //-----------------------------------
    fn setup_widgets(&self) {
        let model = gio::ListStore::new(gio::File::static_type());

        self.imp().files.replace(model);
    }

    //-----------------------------------
    // Setup signals
    //-----------------------------------
    #[allow(deprecated)]
    fn setup_signals(&self) {
        let imp = self.imp();

        // Select button clicked signal
        imp.select_button.connect_clicked(clone!(@weak self as obj. @weak imp => move |_| {
            // Get root window
            let root = obj.root()
                .and_downcast::<gtk::Window>()
                .expect("Must be a 'Window'");

            // Create file dialog
            let dialog = gtk::FileChooserDialog::builder()
                .title(obj.dialog_title())
                .modal(true)
                .transient_for(&root)
                .action(if obj.select() == SelectType::Folder {
                        gtk::FileChooserAction::SelectFolder
                    } else {
                        gtk::FileChooserAction::Open
                    })
                .select_multiple(obj.select() == SelectType::Multiple)
                .build();

            dialog.add_buttons(&[("Select", gtk::ResponseType::Accept), ("Cancel", gtk::ResponseType::Cancel)]);

            // Set filters for dialog
            if obj.select() != SelectType::Folder {
                let filter = gtk::FileFilter::new();
                filter.set_name(Some("All Files"));
                filter.add_pattern("*");

                dialog.add_filter(&filter);

                if let Some(filter) = obj.filter() {
                    dialog.add_filter(&filter);
                    dialog.set_filter(&filter);
                }
            }

            // Set initial location for dialog
            let files = imp.files.borrow();

            if files.n_items() > 0 {
                dialog.set_file(&files.item(0).and_downcast::<gio::File>().unwrap())
                    .expect("Could not set current file for dialog");
            } else {
                let base_folder = imp.base_folder.borrow();

                if base_folder.is_some() {
                    dialog.set_current_folder(base_folder.as_ref())
                        .expect("Could not set current folder for dialog");
                }
            }

            // Connect dialog response signal handler
            dialog.connect_response(clone!(@weak obj, @weak imp => move |dialog, response| {
                if response == gtk::ResponseType::Accept {
                    let files = imp.files.borrow();

                    files.splice(0, files.n_items(), &dialog.files().iter::<gio::File>().flatten().collect::<Vec<gio::File>>());

                    obj.set_state();
                }

                dialog.close();
            }));

            dialog.show();
        }));

        // Clear button clicked signal
        imp.clear_button.connect_clicked(clone!(@weak self as obj, @weak imp => move |_| {
            let files = imp.files.borrow();

            files.remove_all();

            obj.set_state();
        }));
    }

    //-----------------------------------
    // Set state helper function
    //-----------------------------------
    fn set_state(&self) {
        let imp = self.imp();

        let files = imp.files.borrow();

        let n_files = files.n_items();

        if n_files == 0 {
            imp.label.set_label("(None)");
        } else if n_files == 1 {
            let file = files.item(0).and_downcast::<gio::File>().unwrap();

            if let Some(filename) = file.basename() {
                imp.label.set_label(&filename.display().to_string());
            } else if let Some(path) = file.path() {
                imp.label.set_label(&path.display().to_string());
            } else {
                imp.label.set_label("(None)");
            }
        } else {
            imp.label.set_label(&format!("({n_files} files)"))
        }

        imp.clear_button.set_sensitive(n_files > 0);

        self.emit_by_name::<()>("changed", &[]);
    }

    //-----------------------------------
    // Path to file helper function
    //-----------------------------------
    fn path_to_file(&self, path: &str) -> gio::File {
        if let Ok(file) = shellexpand::env(&path) {
            gio::File::for_path(file.to_string())
        } else {
            gio::File::for_path(path.to_string())
        }
    }

    //-----------------------------------
    // Public base folder functions
    //-----------------------------------
    pub fn set_base_folder(&self, path: Option<&str>) {
        let folder = path.map(|path| self.path_to_file(path));

        self.imp().base_folder.replace(folder);
    }

    //-----------------------------------
    // Public paths functions
    //-----------------------------------
    pub fn paths(&self) -> glib::StrV {
        let files = self.imp().files.borrow();

        files.iter::<gio::File>()
            .map(|file| {
                file.ok()
                    .and_then(|file| file.path())
                    .map(|path| path.display().to_string())
            })
            .flatten()
            .collect::<Vec<String>>()
            .into()
    }

    pub fn set_paths(&self, paths: glib::StrV) {
        let files = self.imp().files.borrow();

        files.splice(0, files.n_items(), &paths.iter()
            .map(|path| self.path_to_file(path.to_str()))
            .collect::<Vec<gio::File>>()
        );

        self.set_state();
    }

    //-----------------------------------
    // Public path functions
    //-----------------------------------
    pub fn path(&self) -> String {
        let files = self.imp().files.borrow();

        if files.n_items() > 0 {
            files.item(0)
                .and_downcast::<gio::File>()
                .and_then(|file| file.path())
                .unwrap()
                .display().to_string()
        } else {
            "".to_string()
        }
    }

    pub fn set_path(&self, path: Option<&str>) {
        let files = self.imp().files.borrow();

        if let Some(path) = path {
            files.splice(0, files.n_items(), &[self.path_to_file(path)])
        } else {
            files.remove_all();
        }

        self.set_state();
    }

    //-----------------------------------
    // Public default path functions
    //-----------------------------------
    pub fn set_default_path(&self, path: Option<&str>) {
        let file = path.map(|path| self.path_to_file(path));

        self.imp().default_file.replace(file);
    }

    pub fn reset_paths(&self) {
        let imp = self.imp();

        let default_file = imp.default_file.borrow();
        let files = imp.files.borrow();

        if default_file.is_some() {
            files.splice(0, files.n_items(), &[default_file.clone().unwrap()]);
        } else {
            files.remove_all();
        }

        self.set_state();
    }
}
