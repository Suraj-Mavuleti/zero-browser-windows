import sys
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
from gi.repository import Gtk, Gdk, WebKit2, GLib

class ZeroBrowser(Gtk.Window):
    def __init__(self):
        super().__init__(title="Zero Browser - Fortified Glass Edition")
        self.set_default_size(1300, 900)
        
        self.setup_css()
        
        # 🛡️ Global Privacy Context (Ephemeral / Memory Only)
        self.context = WebKit2.WebContext.new_ephemeral()
        self.context.set_tls_errors_policy(WebKit2.TLSErrorsPolicy.FAIL)
        self.context.get_cookie_manager().set_accept_policy(WebKit2.CookieAcceptPolicy.NO_THIRD_PARTY)
        self.context.set_sandbox_enabled(True)
        
        # 🎨 Native HeaderBar (Glassmorphism look)
        self.header = Gtk.HeaderBar()
        self.header.set_show_close_button(True)
        self.header.props.title = "ZERO BROWSER"
        self.header.props.subtitle = "Max Security Active"
        self.set_titlebar(self.header)
        
        # Left Nav Buttons
        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.btn_back = Gtk.Button(label="◀")
        self.btn_forward = Gtk.Button(label="▶")
        self.btn_reload = Gtk.Button(label="↻")
        self.btn_back.connect("clicked", self.on_back)
        self.btn_forward.connect("clicked", self.on_forward)
        self.btn_reload.connect("clicked", self.on_reload)
        nav_box.pack_start(self.btn_back, False, False, 0)
        nav_box.pack_start(self.btn_forward, False, False, 0)
        nav_box.pack_start(self.btn_reload, False, False, 0)
        self.header.pack_start(nav_box)
        
        # Center URL Bar
        self.url_entry = Gtk.Entry()
        self.url_entry.set_width_chars(45)
        self.url_entry.set_placeholder_text("Search Google or enter URL...")
        self.url_entry.connect("activate", self.on_url_entered)
        self.header.set_custom_title(self.url_entry)
        
        # Right Tools Box
        tools_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.btn_new_tab = Gtk.Button(label="➕ Tab")
        self.btn_close_tab = Gtk.Button(label="❌ Tab")
        self.btn_zoom_in = Gtk.Button(label="🔎+")
        self.btn_zoom_out = Gtk.Button(label="🔎-")
        self.btn_dev = Gtk.Button(label="💻 Dev")
        self.btn_panic = Gtk.Button(label="🛑 Panic Wipe")
        
        self.btn_new_tab.connect("clicked", lambda x: self.new_tab("https://google.com"))
        self.btn_close_tab.connect("clicked", self.close_current_tab)
        self.btn_zoom_in.connect("clicked", self.zoom_in)
        self.btn_zoom_out.connect("clicked", self.zoom_out)
        self.btn_dev.connect("clicked", self.toggle_inspector)
        self.btn_panic.connect("clicked", self.panic_wipe)
        
        tools_box.pack_start(self.btn_new_tab, False, False, 0)
        tools_box.pack_start(self.btn_close_tab, False, False, 0)
        tools_box.pack_start(self.btn_zoom_in, False, False, 0)
        tools_box.pack_start(self.btn_zoom_out, False, False, 0)
        tools_box.pack_start(self.btn_dev, False, False, 0)
        tools_box.pack_start(self.btn_panic, False, False, 0)
        self.header.pack_end(tools_box)
        
        # Tabs System
        self.notebook = Gtk.Notebook()
        self.notebook.set_scrollable(True)
        self.notebook.connect("switch-page", self.on_tab_changed)
        self.add(self.notebook)
        
        self.new_tab("https://google.com")
        
    def setup_css(self):
        css = b'''
            window {
                background: radial-gradient(circle at 50% 0%, #1a2130, #050608);
            }
            headerbar {
                background: rgba(10, 13, 20, 0.95);
                border-bottom: 1px solid rgba(0, 229, 255, 0.3);
                box-shadow: 0 4px 15px rgba(0,0,0,0.8);
                padding: 10px;
            }
            headerbar label.title {
                color: #FFFFFF;
                font-weight: 900;
                letter-spacing: 2px;
            }
            headerbar label.subtitle {
                color: #00FF66;
                font-weight: bold;
            }
            entry {
                background: rgba(0, 0, 0, 0.5);
                color: #00E5FF;
                border: 1px solid rgba(0, 229, 255, 0.2);
                border-radius: 18px;
                padding: 8px 20px;
                box-shadow: inset 0 2px 5px rgba(0,0,0,0.5);
                caret-color: #00E5FF;
            }
            entry:focus {
                border: 1px solid #00E5FF;
                box-shadow: 0 0 12px rgba(0, 229, 255, 0.4);
            }
            button {
                background: rgba(255,255,255,0.03);
                border-radius: 8px;
                border: 1px solid rgba(255,255,255,0.05);
                color: #C5C6C7;
                font-weight: bold;
                padding: 6px 12px;
            }
            button:hover {
                background: rgba(0, 229, 255, 0.15);
                border: 1px solid #00E5FF;
                color: #00E5FF;
                box-shadow: 0 0 8px rgba(0, 229, 255, 0.3);
            }
            notebook header {
                background: rgba(8, 10, 15, 0.95);
                border-bottom: 1px solid #1E2532;
            }
            notebook tab {
                background: rgba(255,255,255,0.02);
                border: none;
                border-radius: 8px 8px 0 0;
                color: #8B94A5;
                padding: 8px 20px;
            }
            notebook tab:checked {
                background: rgba(15, 19, 28, 0.9);
                color: #00E5FF;
                border-top: 2px solid #00E5FF;
            }
        '''
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), style_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
    def new_tab(self, url):
        webview = WebKit2.WebView.new_with_context(self.context)
        
        # Compiler-level tracking immunity
        settings = webview.get_settings()
        settings.set_enable_webgl(False)
        settings.set_enable_media_stream(False)
        settings.set_enable_html5_local_storage(False)
        settings.set_enable_html5_database(False)
        settings.set_enable_dns_prefetching(False)
        settings.set_enable_webaudio(False)
        settings.set_enable_plugins(False)
        settings.set_enable_java(False)
        settings.set_enable_smooth_scrolling(True)
        settings.set_enable_developer_extras(True)
        
        webview.connect("load-changed", self.on_load_changed)
        webview.connect("notify::title", self.on_title_changed)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.add(webview)
        scrolled.show_all()
        
        label = Gtk.Label(label="Loading...")
        self.notebook.append_page(scrolled, label)
        self.notebook.set_current_page(self.notebook.get_n_pages() - 1)
        webview.load_uri(url)
        
    def current_webview(self):
        idx = self.notebook.get_current_page()
        if idx == -1: return None
        return self.notebook.get_nth_page(idx).get_child()
        
    def close_current_tab(self, widget):
        idx = self.notebook.get_current_page()
        if idx != -1: self.notebook.remove_page(idx)
        if self.notebook.get_n_pages() == 0: self.new_tab("https://google.com")
            
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
        idx = self.notebook.page_num(webview.get_parent())
        if idx != -1 and webview.get_title():
            self.notebook.set_tab_label_text(webview.get_parent(), webview.get_title()[:25] + "...")
                
    def on_tab_changed(self, notebook, page, page_num):
        wv = self.current_webview()
        if wv and wv.get_uri(): self.url_entry.set_text(wv.get_uri())
            
    def on_back(self, widget):
        wv = self.current_webview()
        if wv and wv.can_go_back(): wv.go_back()
            
    def on_forward(self, widget):
        wv = self.current_webview()
        if wv and wv.can_go_forward(): wv.go_forward()
            
    def on_reload(self, widget):
        wv = self.current_webview()
        if wv: wv.reload()
        
    def zoom_in(self, widget):
        wv = self.current_webview()
        if wv: wv.set_zoom_level(wv.get_zoom_level() + 0.1)
        
    def zoom_out(self, widget):
        wv = self.current_webview()
        if wv: wv.set_zoom_level(wv.get_zoom_level() - 0.1)
        
    def toggle_inspector(self, widget):
        wv = self.current_webview()
        if wv:
            ins = wv.get_inspector()
            if ins.is_attached(): ins.close()
            else: ins.show()
                
    def panic_wipe(self, widget):
        self.context.clear_cache()
        for i in range(self.notebook.get_n_pages()-1, -1, -1):
            self.notebook.remove_page(i)
        self.url_entry.set_text("")
        self.new_tab("https://duckduckgo.com")
        self.header.props.subtitle = "WIPE SUCCESSFUL - MEMORY CLEARED"

if __name__ == "__main__":
    win = ZeroBrowser()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
