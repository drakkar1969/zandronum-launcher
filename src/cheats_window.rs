use gtk::{glib, gio};
use adw::subclass::prelude::*;
use adw::prelude::*;

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
        pub switches_model: TemplateChild<gio::ListStore>,
        #[template_child]
        pub cheats_model: TemplateChild<gio::ListStore>,
    }

    //-----------------------------------
    // Subclass
    //-----------------------------------
    #[glib::object_subclass]
    impl ObjectSubclass for CheatsWindow {
        const NAME: &'static str = "CheatsWindow";
        type Type = super::CheatsWindow;
        type ParentType = adw::PreferencesWindow;

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
    // Setup widgets
    //-----------------------------------
    fn setup_widgets(&self) {
        let imp = self.imp();

        // Populate command line switches
        let switches = [
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
            .map(|(key, value)| {
                CheatObject::new(key, value)
            })
            .collect::<Vec<CheatObject>>();

        imp.switches_model.splice(0, 0, &switches);

        // Populate cheat codes
        let cheats = [
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
            .map(|(key, value)| {
                CheatObject::new(key, value)
            })
            .collect::<Vec<CheatObject>>();

        imp.cheats_model.splice(0, 0, &cheats);
    }
}
