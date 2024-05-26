use gtk::{glib, gdk, pango};
use adw::subclass::prelude::*;
use adw::prelude::*;
use glib::clone;

use crate::cheat_object::CheatObject;

//------------------------------------------------------------------------------
// MODULE: CheatsWindow
//------------------------------------------------------------------------------
mod imp {
    use super::*;

    //-----------------------------------
    // Private structure
    //-----------------------------------
    #[derive(Default, gtk::CompositeTemplate)]
    #[template(resource = "/com/github/ZandronumLauncher/ui/cheats_window.ui")]
    pub struct CheatsWindow {
        #[template_child]
        pub switches_grid: TemplateChild<gtk::Grid>,
        #[template_child]
        pub cheats_grid: TemplateChild<gtk::Grid>,
    }

    //-----------------------------------
    // Subclass
    //-----------------------------------
    #[glib::object_subclass]
    impl ObjectSubclass for CheatsWindow {
        const NAME: &'static str = "CheatsWindow";
        type Type = super::CheatsWindow;
        type ParentType = adw::Window;

        fn class_init(klass: &mut Self::Class) {
            CheatObject::ensure_type();

            klass.bind_template();
        }

        fn instance_init(obj: &glib::subclass::InitializingObject<Self>) {
            obj.init_template();
        }
    }

    impl ObjectImpl for CheatsWindow {
        //-----------------------------------
        // Constructor
        //-----------------------------------
        fn constructed(&self) {
            self.parent_constructed();

            let obj = self.obj();

            obj.setup_widgets();
            obj.setup_controllers();
        }
    }

    impl WidgetImpl for CheatsWindow {}
    impl WindowImpl for CheatsWindow {}
    impl AdwWindowImpl for CheatsWindow {} 
    impl PreferencesWindowImpl for CheatsWindow {}
}

//------------------------------------------------------------------------------
// IMPLEMENTATION: CheatsWindow
//------------------------------------------------------------------------------
glib::wrapper! {
    pub struct CheatsWindow(ObjectSubclass<imp::CheatsWindow>)
        @extends adw::Window, gtk::Window, gtk::Widget,
        @implements gtk::Accessible, gtk::Buildable, gtk::ConstraintTarget, gtk::Native, gtk::Root, gtk::ShortcutManager;
}

impl CheatsWindow {
    //-----------------------------------
    // New function
    //-----------------------------------
    pub fn new() -> Self {
        glib::Object::builder().build()
    }

    //-----------------------------------
    // Label helper functions
    //-----------------------------------
    fn key_label(&self, key: &str) -> gtk::Label {
        let label = gtk::Label::new(Some(key));
        label.set_vexpand(true);
        label.set_xalign(0.0);
        label.set_yalign(0.5);
        label.set_can_focus(false);
        label.set_selectable(true);

        label
    }

    fn value_label(&self, value: &str) -> gtk::Label {
        let label = gtk::Label::new(Some(value));
        label.set_vexpand(true);
        label.set_xalign(0.0);
        label.set_yalign(0.5);
        label.set_can_focus(false);
        label.set_wrap_mode(pango::WrapMode::Word);
        label.set_wrap(true);
        label.set_width_chars(40);
        label.set_max_width_chars(40);

        label
    }

    //-----------------------------------
    // Setup widgets
    //-----------------------------------
    fn setup_widgets(&self) {
        let imp = self.imp();

        // Populate command line switches
        [
            ("-fast", "Increases the speed and attack rate of monsters. Requires the -warp parameter."),
            ("-nomonsters", "Disable spawning of monsters. Requires the -warp parameter."),
            ("-nomusic", "Disable background music"),
            ("-nosfx", "Disable sound effects"),
            ("-nosound", "Disable music and sound effects"),
            ("-respawn", "Monsters return a few seconds after being killed. Requires the -warp parameter."),
            ("-skill <s>", "Select difficulty level <s> (1 to 5). This parameter will warp to the first level of the game (if no other -warp parameter is specified)."),
            ("-warp <m>\n-warp <e> <m>", "Start the game on level <m> (1 to 32). For Ultimate Doom and Freedoom Phase 1, both episode <e> (1 to 4) and map <m> (1 to 9) must be specified, separated by a space."),
            ("-width x\n-height y", "Specify desired screen resolution.")
        ]
        .iter()
        .enumerate()
        .for_each(|(i, (key, value))| {
            imp.switches_grid.attach(&self.key_label(key), 0, i as i32, 1, 1);
            imp.switches_grid.attach(&self.value_label(value), 1, i as i32, 1, 1);
        });

        // Populate cheat codes
        [
            ("IDBEHOLDA", "Automap"),
            ("IDBEHOLDI", "Temporary invisibility"),
            ("IDBEHOLDL", "Light amplification goggles"),
            ("IDBEHOLDR", "Radiation suit"),
            ("IDBEHOLDS", "Berserk pack"),
            ("IDBEHOLDV", "Temporary invulnerability"),
            ("IDCHOPPERS", "Chainsaw"),
            ("IDCLEV##", "Warp to episode #, map #"),
            ("IDCLIP", "No clipping (walk through objects)"),
            ("IDDQD", "God mode (invincibility)"),
            ("IDDT", "Display entire map and enemies (toggle)"),
            ("IDFA", "All weapons and 200% armor"),
            ("IDKFA", "All keys and weapons"),
            ("IDMYPOS", "Display location")
        ]
        .iter()
        .enumerate()
        .for_each(|(i, (key, value))| {
            imp.cheats_grid.attach(&self.key_label(key), 0, i as i32, 1, 1);
            imp.cheats_grid.attach(&self.value_label(value), 1, i as i32, 1, 1);
        });
    }

    //-----------------------------------
    // Setup controllers
    //-----------------------------------
    fn setup_controllers(&self) {
        // Key controller (close window on ESC)
        let controller = gtk::EventControllerKey::new();

        controller.connect_key_pressed(clone!(@weak self as window => @default-return glib::Propagation::Proceed, move |_, key, _, state| {
            if key == gdk::Key::Escape && state.is_empty() {
                window.close();

                glib::Propagation::Stop
            } else {
                glib::Propagation::Proceed
            }

        }));

        self.add_controller(controller);
    }
}

impl Default for CheatsWindow {
    fn default() -> Self {
        Self::new()
    }
}
