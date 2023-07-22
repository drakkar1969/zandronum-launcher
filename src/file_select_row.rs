use std::cell::{Cell, RefCell};
use std::path::Path;

use gtk::{gio, glib};
use adw::subclass::prelude::*;
use gtk::prelude::*;
use glib::clone;

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
        #[property(get, set, nullable, construct)]
        current_folder: RefCell<Option<String>>,

        #[property(get, set = Self::set_files, construct)]
        files: RefCell<Vec<String>>,
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
            let obj = self.obj();

            self.parent_constructed();

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

        //-----------------------------------
        // Files property custom setter
        //-----------------------------------
        fn set_files(&self, files: Vec<String>) {
            let n_files = files.len();

            if n_files == 0 {
                self.label.set_label("(None)");
            } else if n_files == 1 {
                let path = Path::new(&files[0]);

                self.label.set_label(&path.file_name().unwrap().to_string_lossy());
            } else {
                self.label.set_label(&format!("({n_files} files)"))
            }

            self.clear_button.set_sensitive(n_files > 0);

            self.files.replace(files);
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
    // Setup signals
    //-----------------------------------
    #[allow(deprecated)]
    fn setup_signals(&self) {
        let imp = self.imp();

        // Select button clicked signal
        imp.select_button.connect_clicked(clone!(@weak self as obj => move |_| {
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
            if obj.files().len() > 0 {
                dialog.set_file(&gio::File::for_path(&obj.files()[0]))
                    .expect("Could not set current file for dialog");
            } else if let Some(folder) = obj.current_folder() {
                dialog.set_current_folder(Some(&gio::File::for_path(&folder)))
                    .expect("Could not set current folder for dialog");
            }

            // Connect dialog response signal handler
            dialog.connect_response(clone!(@weak obj => move |dialog, response| {
                if response == gtk::ResponseType::Accept {
                    let files = dialog.files();

                    let file_vec: Vec<String> = files.iter::<gio::File>()
                        .map(|file| {
                            file.ok()
                                .and_then(|file| file.path())
                                .map(|path| path.to_string_lossy().to_string())
                        })
                        .flatten()
                        .collect();

                    obj.set_files(file_vec);
                }

                dialog.close();
            }));

            dialog.show();
        }));

        // Clear button clicked signal
        imp.clear_button.connect_clicked(clone!(@weak self as obj => move |_| {
            obj.set_files(vec![]);
        }));
    }
}
