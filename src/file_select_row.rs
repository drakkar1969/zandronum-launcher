use std::cell::{Cell, RefCell, OnceCell};
use std::sync::OnceLock;

use gtk::{gio, glib};
use adw::subclass::prelude::*;
use gtk::prelude::*;
use glib::clone;
use glib::subclass::Signal;

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
        pub files: OnceCell<gio::ListStore>,
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

    #[glib::derived_properties]
    impl ObjectImpl for FileSelectRow {
        //-----------------------------------
        // Custom signals
        //-----------------------------------
        fn signals() -> &'static [Signal] {
            static SIGNALS: OnceLock<Vec<Signal>> = OnceLock::new();
            SIGNALS.get_or_init(|| {
                vec![
                    Signal::builder("changed")
                        .build(),
                ]
            })
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
        let model = gio::ListStore::new::<gio::File>();

        self.imp().files.set(model).unwrap();
    }

    //-----------------------------------
    // Setup signals
    //-----------------------------------
    fn setup_signals(&self) {
        let imp = self.imp();

        // Select button clicked signal
        imp.select_button.connect_clicked(clone!(@weak self as row, @weak imp => move |_| {
            // Create dialog
            let dialog = gtk::FileDialog::builder()
                .title(row.dialog_title())
                .modal(true)
                .accept_label("Select")
                .build();

            // Set filters for dialog
            if row.select() != SelectType::Folder {
                let all_filter = gtk::FileFilter::new();
                all_filter.set_name(Some("All Files"));
                all_filter.add_pattern("*");

                let dialog_filters = gio::ListStore::from_iter([all_filter]);

                if let Some(filter) = row.filter() {
                    dialog_filters.append(&filter);
                }

                dialog.set_filters(Some(&dialog_filters));
                dialog.set_default_filter(row.filter().as_ref());
            }

            // Set initial location for dialog
            let files = imp.files.get().unwrap();

            if files.n_items() > 0 {
                dialog.set_initial_file(files.item(0).and_downcast::<gio::File>().as_ref());
            } else {
                let base_folder = imp.base_folder.borrow();

                if base_folder.is_some() {
                    dialog.set_initial_folder(base_folder.as_ref());
                }
            }

            // Get root window
            let root = row.root()
                .and_downcast::<gtk::Window>()
                .expect("Must be a 'Window'");

            // Show dialog
            match row.select() {
                SelectType::File => {
                    dialog.open(Some(&root), None::<&gio::Cancellable>, clone!(@weak imp => move |result| {
                        if let Ok(file) = result {
                            let files = imp.files.get().unwrap();

                            files.splice(0, files.n_items(), &[file]);

                            row.set_state();
                        }
                    }));
                },
                SelectType::Multiple => {
                    dialog.open_multiple(Some(&root), None::<&gio::Cancellable>, clone!(@weak imp => move |result| {
                        if let Ok(file) = result {
                            let files = imp.files.get().unwrap();

                            files.splice(0, files.n_items(), &file.iter::<gio::File>().flatten().collect::<Vec<gio::File>>());

                            row.set_state();
                        }
                    }));
                },
                SelectType::Folder => {
                    dialog.select_folder(Some(&root), None::<&gio::Cancellable>, clone!(@weak imp => move |result| {
                        if let Ok(file) = result {
                            let files = imp.files.get().unwrap();

                            files.splice(0, files.n_items(), &[file]);

                            row.set_state();
                        }
                    }));
                }
            }
        }));

        // Clear button clicked signal
        imp.clear_button.connect_clicked(clone!(@weak self as row, @weak imp => move |_| {
            let files = imp.files.get().unwrap();

            files.remove_all();

            row.set_state();
        }));
    }

    //-----------------------------------
    // Set state helper function
    //-----------------------------------
    fn set_state(&self) {
        let imp = self.imp();

        let files = imp.files.get().unwrap();

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
    fn path_to_file(&self, path: &str) -> Option<gio::File> {
        let file: gio::File;

        if let Ok(path_exp) = shellexpand::env(&path) {
            file = gio::File::for_path(path_exp.to_string());
        } else {
            file = gio::File::for_path(path.to_string());
        }

        if file.query_exists(None::<&gio::Cancellable>) {
            Some(file)
        } else {
            None
        }
    }

    //-----------------------------------
    // Public base folder functions
    //-----------------------------------
    pub fn set_base_folder(&self, path: Option<&str>) {
        let folder = path.and_then(|path| self.path_to_file(path));

        self.imp().base_folder.replace(folder);
    }

    //-----------------------------------
    // Public paths functions
    //-----------------------------------
    pub fn paths(&self) -> glib::StrV {
        let files = self.imp().files.get().unwrap();

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
        let files = self.imp().files.get().unwrap();

        files.splice(0, files.n_items(), &paths.iter()
            .filter_map(|path| self.path_to_file(path.as_str()))
            .collect::<Vec<gio::File>>()
        );

        self.set_state();
    }

    //-----------------------------------
    // Public path functions
    //-----------------------------------
    pub fn path(&self) -> String {
        let files = self.imp().files.get().unwrap();

        if files.n_items() > 0 {
            files.item(0)
                .and_downcast::<gio::File>()
                .and_then(|file| file.path())
                .map(|path| path.display().to_string())
                .unwrap()
        } else {
            "".to_string()
        }
    }

    pub fn set_path(&self, path: Option<&str>) {
        let files = self.imp().files.get().unwrap();

        if let Some(path) = path.and_then(|path| self.path_to_file(path)) {
            files.splice(0, files.n_items(), &[path])
        } else {
            files.remove_all();
        }

        self.set_state();
    }

    //-----------------------------------
    // Public default path functions
    //-----------------------------------
    pub fn set_default_path(&self, path: Option<&str>) {
        let file = path.and_then(|path| self.path_to_file(path));

        self.imp().default_file.replace(file);
    }

    pub fn reset_paths(&self) {
        let imp = self.imp();

        let files = imp.files.get().unwrap();

        if let Some(default_file) = imp.default_file.borrow().clone() {
            files.splice(0, files.n_items(), &[default_file]);
        } else {
            files.remove_all();
        }

        self.set_state();
    }
}
