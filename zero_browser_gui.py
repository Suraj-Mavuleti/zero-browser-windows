import sys
import gi
import os
import json
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, Gdk, GLib
from gi.repository import WebKit2

CONFIG_DIR = os.path.expanduser("~/.config/zero-browser")
BKMK_FILE = os.path.join(CONFIG_DIR, "bookmarks.json")

class ZeroBrowser(Gtk.Window):
    def __init__(self):
        super().__init__(title="Zero Browser - Ultimate Studio")
        self.set_default_size(1300, 850)
        
        self.header = Gtk.HeaderBar()
        self.header.set_show_close_button(True)
        self.header.props.title = ""
        self.header.get_style_context().add_class("hidden-header")
        self.set_titlebar(self.header)
        
        self.current_theme = 0
        self.setup_css()
        
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.add(main_box)
        
        self.sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.sidebar.set_size_request(260, -1)
        self.sidebar.get_style_context().add_class("sidebar")
        main_box.pack_start(self.sidebar, False, False, 0)
        
        logo = Gtk.Label(label="Z E R O")
        logo.get_style_context().add_class("sidebar-logo")
        logo.set_margin_top(20)
        logo.set_margin_bottom(20)
        self.sidebar.pack_start(logo, False, False, 0)
        
        btn_new_tab = Gtk.Button(label="+ New Tab")
        btn_new_tab.get_style_context().add_class("action-btn")
        btn_new_tab.connect("clicked", self.add_tab)
        self.sidebar.pack_start(btn_new_tab, False, False, 10)
        
        btn_theme = Gtk.Button(label="🎨 Toggle Theme")
        btn_theme.get_style_context().add_class("nav-btn")
        btn_theme.set_margin_start(15)
        btn_theme.set_margin_end(15)
        btn_theme.connect("clicked", self.toggle_theme)
        self.sidebar.pack_start(btn_theme, False, False, 10)
        
        lbl_tabs = Gtk.Label(label="OPEN TABS")
        lbl_tabs.get_style_context().add_class("section-label")
        lbl_tabs.set_halign(Gtk.Align.START)
        lbl_tabs.set_margin_start(20)
        lbl_tabs.set_margin_top(15)
        self.sidebar.pack_start(lbl_tabs, False, False, 10)
        
        self.tab_list = Gtk.ListBox()
        self.tab_list.get_style_context().add_class("transparent-list")
        self.tab_list.connect("row-selected", self.on_tab_switched)
        self.sidebar.pack_start(self.tab_list, True, True, 0)
        
        self.workspace = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.workspace.get_style_context().add_class("workspace")
        main_box.pack_start(self.workspace, True, True, 0)
        
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        toolbar.get_style_context().add_class("toolbar")
        
        btn_back = Gtk.Button(label="◀")
        btn_back.get_style_context().add_class("nav-btn")
        btn_fwd = Gtk.Button(label="▶")
        btn_fwd.get_style_context().add_class("nav-btn")
        
        self.url_entry = Gtk.Entry()
        self.url_entry.set_placeholder_text("Search Google or enter address...")
        self.url_entry.get_style_context().add_class("url-bar")
        self.url_entry.connect("activate", self.on_url_entered)
        
        btn_shield = Gtk.Button(label="🛡️")
        btn_shield.get_style_context().add_class("nav-btn")
        btn_shield.set_tooltip_text("Privacy Shield Active")
        
        toolbar.pack_start(btn_back, False, False, 0)
        toolbar.pack_start(btn_fwd, False, False, 0)
        toolbar.pack_start(self.url_entry, True, True, 0)
        toolbar.pack_start(btn_shield, False, False, 0)
        self.workspace.pack_start(toolbar, False, False, 0)
        
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.workspace.pack_start(self.stack, True, True, 0)
        
        self.tabs = {}
        self.add_tab()

    def add_tab(self, widget=None):
        ctx = WebKit2.WebContext.new_ephemeral()
        ctx.set_sandbox_enabled(True)
        webview = WebKit2.WebView.new_with_context(ctx)
        
        settings = webview.get_settings()
        settings.set_enable_developer_extras(False)
        settings.set_enable_webgl(False)
        settings.set_enable_webrtc(False)
        webview.set_settings(settings)
        
        tab_id = str(id(webview))
        self.tabs[tab_id] = webview
        self.stack.add_named(webview, tab_id)
        
        row = Gtk.ListBoxRow()
        row.get_style_context().add_class("tab-row")
        row.tab_id = tab_id
        
        lbl = Gtk.Label(label="New Tab")
        lbl.set_halign(Gtk.Align.START)
        lbl.set_margin_start(15)
        lbl.set_margin_top(12)
        lbl.set_margin_bottom(12)
        lbl.get_style_context().add_class("tab-lbl")
        
        row.add(lbl)
        self.tab_list.add(row)
        self.tab_list.show_all()
        
        webview.connect("notify::title", lambda w, p: lbl.set_text(w.get_title() or "New Tab"))
        webview.connect("notify::uri", self.on_uri_changed)
        
        self.stack.set_visible_child(webview)
        self.tab_list.select_row(row)
        webview.load_uri("https://google.com")

    def on_tab_switched(self, listbox, row):
        if row:
            webview = self.tabs[row.tab_id]
            self.stack.set_visible_child(webview)
            self.url_entry.set_text(webview.get_uri() or "")

    def on_url_entered(self, entry):
        url = entry.get_text()
        if not url.startswith("http"):
            if "." in url and " " not in url:
                url = "https://" + url
            else:
                url = "https://www.google.com/search?q=" + url.replace(" ", "+")
        webview = self.stack.get_visible_child()
        if webview:
            webview.load_uri(url)

    def on_uri_changed(self, webview, param):
        if self.stack.get_visible_child() == webview:
            self.url_entry.set_text(webview.get_uri() or "")

    def toggle_theme(self, widget):
        self.current_theme = (self.current_theme + 1) % 3
        self.setup_css()

    def setup_css(self):
        themes = [
            # 0: Dark Glassmorphism (Default)
            b'''
            window { background-color: #030305; }
            .hidden-header { background: #030305; min-height: 0px; padding: 0px; border: none; box-shadow: none; }
            .sidebar { background-color: rgba(10, 12, 18, 0.98); border-right: 1px solid rgba(255, 255, 255, 0.05); }
            .sidebar-logo { color: #FFFFFF; text-shadow: 0 0 15px rgba(0, 153, 255, 0.6); }
            .action-btn { background: linear-gradient(45deg, #0099FF, #0055FF); color: #FFFFFF; }
            .section-label { color: #4A5568; }
            .tab-row:hover { background: rgba(255,255,255,0.05); }
            .tab-row:selected { background: rgba(0, 153, 255, 0.1); border-left: 3px solid #0099FF; }
            .tab-lbl { color: #c9d1d9; }
            .toolbar { background: #080A0F; border-bottom: 1px solid rgba(255, 255, 255, 0.05); }
            .url-bar { background: #10141E; color: #FFFFFF; border: 1px solid #1C2333; }
            .nav-btn { background: rgba(255,255,255,0.05); color: #FFFFFF; }
            .workspace { background: #000000; }
            ''',
            # 1: Neon Cyberpunk
            b'''
            window { background-color: #0d0221; }
            .hidden-header { background: #0d0221; min-height: 0px; padding: 0px; border: none; box-shadow: none; }
            .sidebar { background-color: rgba(20, 2, 40, 0.98); border-right: 1px solid rgba(255, 0, 255, 0.3); }
            .sidebar-logo { color: #00ffff; text-shadow: 0 0 20px #00ffff; }
            .action-btn { background: linear-gradient(45deg, #ff00ff, #00ffff); color: #000000; box-shadow: 0 0 20px rgba(255,0,255,0.5); }
            .section-label { color: #00ffff; }
            .tab-row:hover { background: rgba(0,255,255,0.1); }
            .tab-row:selected { background: rgba(255, 0, 255, 0.2); border-left: 3px solid #ff00ff; }
            .tab-lbl { color: #ffffff; text-shadow: 0 0 5px #00ffff; }
            .toolbar { background: #110022; border-bottom: 1px solid rgba(0, 255, 255, 0.3); }
            .url-bar { background: #220044; color: #00ffff; border: 1px solid #ff00ff; box-shadow: 0 0 10px rgba(255,0,255,0.2); }
            .nav-btn { background: rgba(0,255,255,0.1); color: #00ffff; border: 1px solid #00ffff; }
            .workspace { background: #000000; }
            ''',
            # 2: Light Mac Studio
            b'''
            window { background-color: #f5f5f7; }
            .hidden-header { background: #f5f5f7; min-height: 0px; padding: 0px; border: none; box-shadow: none; }
            .sidebar { background-color: rgba(255, 255, 255, 0.95); border-right: 1px solid rgba(0, 0, 0, 0.1); }
            .sidebar-logo { color: #1d1d1f; text-shadow: none; }
            .action-btn { background: linear-gradient(45deg, #0066cc, #004499); color: #FFFFFF; }
            .section-label { color: #86868b; }
            .tab-row:hover { background: rgba(0,0,0,0.05); }
            .tab-row:selected { background: rgba(0, 102, 204, 0.1); border-left: 3px solid #0066cc; }
            .tab-lbl { color: #1d1d1f; }
            .toolbar { background: #ffffff; border-bottom: 1px solid rgba(0, 0, 0, 0.1); }
            .url-bar { background: #f5f5f7; color: #1d1d1f; border: 1px solid #d2d2d7; }
            .nav-btn { background: rgba(0,0,0,0.05); color: #1d1d1f; }
            .workspace { background: #ffffff; }
            '''
        ]
        
        base_css = b'''
            .sidebar-logo { font-size: 24px; font-weight: 900; letter-spacing: 5px; }
            .action-btn { border-radius: 12px; font-weight: bold; padding: 12px; margin: 0 15px; border: none; transition: all 0.3s; }
            .action-btn:hover { transform: scale(1.02); }
            .section-label { font-size: 11px; font-weight: 900; letter-spacing: 2px; }
            .transparent-list { background: transparent; }
            .tab-row { background: transparent; border-radius: 8px; margin: 2px 10px; border: 1px solid transparent; transition: all 0.2s; }
            .tab-lbl { font-weight: bold; font-size: 14px; }
            .toolbar { padding: 10px 20px; }
            .url-bar { border-radius: 10px; padding: 10px; font-size: 14px; }
            .nav-btn { border-radius: 10px; padding: 10px; font-weight: bold; transition: all 0.2s; }
        '''
        
        provider = Gtk.CssProvider()
        provider.load_from_data(base_css + themes[self.current_theme])
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

if __name__ == "__main__":
    win = ZeroBrowser()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
