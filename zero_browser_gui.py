import sys
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
from gi.repository import Gtk, Gdk, WebKit2, GLib

class ZeroBrowser(Gtk.Window):
    def __init__(self):
        super().__init__(title="Zero Browser - Premium Studio")
        self.set_default_size(1400, 900)
        
        # Frameless native look (hide default titlebar)
        self.header = Gtk.HeaderBar()
        self.header.set_show_close_button(True)
        self.header.props.title = ""
        self.header.get_style_context().add_class("hidden-header")
        self.set_titlebar(self.header)
        
        # Security Context
        self.context = WebKit2.WebContext.new_ephemeral()
        self.context.set_tls_errors_policy(WebKit2.TLSErrorsPolicy.FAIL)
        self.context.get_cookie_manager().set_accept_policy(WebKit2.CookieAcceptPolicy.NO_THIRD_PARTY)
        self.context.set_sandbox_enabled(True)
        
        self.setup_css()
        
        # Main Container
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.add(main_box)
        
        # ================= SIDEBAR =================
        self.sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.sidebar.set_size_request(300, -1)
        self.sidebar.get_style_context().add_class("sidebar")
        main_box.pack_start(self.sidebar, False, False, 0)
        
        # Logo Area
        logo_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        logo = Gtk.Label(label="Z E R O")
        logo.get_style_context().add_class("sidebar-logo")
        logo_box.pack_start(logo, True, True, 0)
        self.sidebar.pack_start(logo_box, False, False, 10)
        
        # URL & Search Bar
        url_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        url_box.set_margin_start(15)
        url_box.set_margin_end(15)
        self.url_entry = Gtk.Entry()
        self.url_entry.set_placeholder_text("🔍 Search or type URL...")
        self.url_entry.get_style_context().add_class("url-entry")
        self.url_entry.connect("activate", self.on_url_entered)
        url_box.pack_start(self.url_entry, True, True, 0)
        self.sidebar.pack_start(url_box, False, False, 10)
        
        # Navigation Actions
        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        nav_box.set_margin_start(15)
        nav_box.set_margin_end(15)
        self.btn_back = Gtk.Button(label="◀")
        self.btn_forward = Gtk.Button(label="▶")
        self.btn_reload = Gtk.Button(label="↻")
        self.btn_new = Gtk.Button(label="➕")
        
        self.btn_back.connect("clicked", self.on_back)
        self.btn_forward.connect("clicked", self.on_forward)
        self.btn_reload.connect("clicked", self.on_reload)
        self.btn_new.connect("clicked", lambda x: self.new_tab("https://google.com"))
        
        for btn in [self.btn_back, self.btn_forward, self.btn_reload, self.btn_new]:
            btn.get_style_context().add_class("nav-btn")
            nav_box.pack_start(btn, True, True, 0)
        self.sidebar.pack_start(nav_box, False, False, 5)
        
        # Spaces / Tabs Label
        lbl_spaces = Gtk.Label(label="OPEN TABS")
        lbl_spaces.get_style_context().add_class("section-label")
        lbl_spaces.set_halign(Gtk.Align.START)
        lbl_spaces.set_margin_start(20)
        lbl_spaces.set_margin_top(15)
        self.sidebar.pack_start(lbl_spaces, False, False, 5)
        
        # Vertical Tabs List
        scroll_sidebar = Gtk.ScrolledWindow()
        scroll_sidebar.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.tabs_list = Gtk.ListBox()
        self.tabs_list.get_style_context().add_class("tabs-list")
        self.tabs_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.tabs_list.connect("row-selected", self.on_tab_selected)
        scroll_sidebar.add(self.tabs_list)
        self.sidebar.pack_start(scroll_sidebar, True, True, 0)
        
        # Bottom Tools
        tools_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        tools_box.set_margin_start(15)
        tools_box.set_margin_end(15)
        tools_box.set_margin_bottom(15)
        self.btn_dev = Gtk.Button(label="💻 DevTools")
        self.btn_dev.get_style_context().add_class("nav-btn")
        self.btn_dev.connect("clicked", self.toggle_inspector)
        tools_box.pack_start(self.btn_dev, True, True, 0)
        self.sidebar.pack_end(tools_box, False, False, 0)
        
        # ================= WEBVIEW AREA =================
        self.webview_container = Gtk.Box()
        self.webview_container.get_style_context().add_class("webview-container")
        main_box.pack_start(self.webview_container, True, True, 0)
        
        # The floating 'App' window inside the browser
        self.webview_box = Gtk.Box()
        self.webview_box.get_style_context().add_class("webview-box")
        self.webview_container.pack_start(self.webview_box, True, True, 0)
        
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(250)
        self.webview_box.pack_start(self.stack, True, True, 0)
        
        # State tracking
        self.tab_map = {} # webview -> row
        
        self.new_tab("https://google.com")
        
    def setup_css(self):
        css = b'''
            window { background-color: #030305; }
            .hidden-header {
                background: #030305;
                min-height: 0px;
                padding: 0px;
                border: none;
                box-shadow: none;
            }
            .sidebar {
                background-color: #080A10;
                border-right: 1px solid #141722;
            }
            .sidebar-logo {
                color: #FFFFFF;
                font-size: 26px;
                font-weight: 900;
                letter-spacing: 4px;
                text-shadow: 0 0 10px rgba(0,229,255,0.4);
            }
            .url-entry {
                background: #10141E;
                color: #00E5FF;
                border: 1px solid #1C2333;
                border-radius: 12px;
                padding: 12px 15px;
                font-size: 13px;
                box-shadow: inset 0 2px 4px rgba(0,0,0,0.5);
                caret-color: #00E5FF;
            }
            .url-entry:focus {
                border: 1px solid #00E5FF;
                background: #141926;
                box-shadow: 0 0 12px rgba(0,229,255,0.3);
            }
            .nav-btn {
                background: #10141E;
                border: 1px solid #1C2333;
                color: #8B94A5;
                border-radius: 10px;
                padding: 8px;
                font-weight: bold;
                font-size: 14px;
                transition: all 0.2s ease;
            }
            .nav-btn:hover {
                background: #181E2D;
                color: #00E5FF;
                border: 1px solid #00E5FF;
                box-shadow: 0 0 8px rgba(0,229,255,0.2);
            }
            .section-label {
                color: #4A5568;
                font-size: 11px;
                font-weight: 900;
                letter-spacing: 1px;
            }
            .tabs-list {
                background: transparent;
            }
            .tab-row {
                background: transparent;
                padding: 12px 15px;
                margin: 4px 15px;
                border-radius: 10px;
                color: #8B94A5;
                font-weight: bold;
                font-size: 13px;
            }
            .tab-row:hover {
                background: #10141E;
                color: #FFFFFF;
            }
            .tab-row:selected {
                background: rgba(0, 229, 255, 0.1);
                color: #00E5FF;
                border-left: 3px solid #00E5FF;
            }
            .tab-close-btn {
                background: transparent;
                border: none;
                color: #4A5568;
                padding: 0px 5px;
            }
            .tab-close-btn:hover {
                color: #FF3366;
            }
            .webview-container {
                background-color: #030305;
                padding: 12px 12px 12px 0px;
            }
            .webview-box {
                background: #10141E;
                border-radius: 16px;
                border: 1px solid #1C2333;
                box-shadow: 0 10px 30px rgba(0,0,0,0.8);
                overflow: hidden;
            }
        '''
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
    def new_tab(self, url):
        webview = WebKit2.WebView.new_with_context(self.context)
        
        # Privacy settings
        settings = webview.get_settings()
        for setting in ["webgl", "media_stream", "html5_local_storage", "html5_database", "dns_prefetching", "webaudio", "plugins", "java"]:
            getattr(settings, f"set_enable_{setting}")(False)
        settings.set_enable_smooth_scrolling(True)
        settings.set_enable_developer_extras(True)
        
        webview.connect("load-changed", self.on_load_changed)
        webview.connect("notify::title", self.on_title_changed)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.add(webview)
        scrolled.show_all()
        
        # Generate unique ID for Stack
        stack_id = str(id(webview))
        self.stack.add_named(scrolled, stack_id)
        
        # Create Custom Row
        row = Gtk.ListBoxRow()
        row.get_style_context().add_class("tab-row")
        
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        lbl = Gtk.Label(label="Loading...")
        lbl.set_halign(Gtk.Align.START)
        lbl.set_ellipsize(3) # END
        
        close_btn = Gtk.Button(label="✕")
        close_btn.get_style_context().add_class("tab-close-btn")
        close_btn.connect("clicked", lambda b: self.close_tab(webview, row))
        
        box.pack_start(lbl, True, True, 0)
        box.pack_end(close_btn, False, False, 0)
        row.add(box)
        row.show_all()
        
        # Bind row to stack ID
        row.stack_id = stack_id
        row.lbl = lbl
        self.tab_map[webview] = row
        
        self.tabs_list.add(row)
        self.tabs_list.select_row(row)
        
        webview.load_uri(url)
        
    def close_tab(self, webview, row):
        # Remove from stack
        scrolled = webview.get_parent()
        self.stack.remove(scrolled)
        # Remove from list
        self.tabs_list.remove(row)
        del self.tab_map[webview]
        
        # Auto-create if empty
        if len(self.tab_map) == 0:
            self.new_tab("https://google.com")
            
    def current_webview(self):
        row = self.tabs_list.get_selected_row()
        if not row: return None
        scrolled = self.stack.get_child_by_name(row.stack_id)
        return scrolled.get_child() if scrolled else None
        
    def on_tab_selected(self, listbox, row):
        if row:
            self.stack.set_visible_child_name(row.stack_id)
            wv = self.current_webview()
            if wv and wv.get_uri():
                self.url_entry.set_text(wv.get_uri())
                
    def on_url_entered(self, widget):
        url = self.url_entry.get_text()
        if not url.startswith("http://") and not url.startswith("https://"):
            if "." in url and " " not in url: url = "https://" + url
            else: url = "https://google.com/search?q=" + url.replace(" ", "+")
        wv = self.current_webview()
        if wv: wv.load_uri(url)
        
    def on_load_changed(self, webview, load_event):
        if webview == self.current_webview() and load_event == WebKit2.LoadEvent.COMMITTED:
            self.url_entry.set_text(webview.get_uri())
            
    def on_title_changed(self, webview, param):
        row = self.tab_map.get(webview)
        if row and webview.get_title():
            row.lbl.set_text(webview.get_title()[:20] + "...")
            
    def on_back(self, widget):
        wv = self.current_webview()
        if wv and wv.can_go_back(): wv.go_back()
            
    def on_forward(self, widget):
        wv = self.current_webview()
        if wv and wv.can_go_forward(): wv.go_forward()
            
    def on_reload(self, widget):
        wv = self.current_webview()
        if wv: wv.reload()
        
    def toggle_inspector(self, widget):
        wv = self.current_webview()
        if wv:
            ins = wv.get_inspector()
            if ins.is_attached(): ins.close()
            else: ins.show()

if __name__ == "__main__":
    win = ZeroBrowser()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
