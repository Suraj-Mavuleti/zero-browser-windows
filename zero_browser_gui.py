import sys
import gi
import os
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, Gdk, GLib
from gi.repository import WebKit2

class ZeroDevBrowser(Gtk.Window):
    def __init__(self):
        super().__init__(title="Zero Browser - Developer Studio")
        self.set_default_size(1400, 900)
        
        # Transparent visual for true glassmorphism
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)
            self.set_app_paintable(True)

        self.header = Gtk.HeaderBar()
        self.header.set_show_close_button(True)
        self.header.props.title = ""
        self.header.get_style_context().add_class("hidden-header")
        self.set_titlebar(self.header)
        
        self.setup_css()
        
        self.main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_vbox.get_style_context().add_class("glass-container")
        self.add(self.main_vbox)
        
        # ================= TOOLBAR =================
        self.toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.toolbar.get_style_context().add_class("glass-toolbar")
        self.main_vbox.pack_start(self.toolbar, False, False, 0)
        
        btn_back = Gtk.Button(label="◀")
        btn_fwd = Gtk.Button(label="▶")
        btn_refresh = Gtk.Button(label="↻")
        for b in [btn_back, btn_fwd, btn_refresh]:
            b.get_style_context().add_class("glass-btn")
            self.toolbar.pack_start(b, False, False, 0)
            
        self.url_bar = Gtk.Entry()
        self.url_bar.get_style_context().add_class("glass-url")
        self.url_bar.set_placeholder_text("Enter URL or IP...")
        self.url_bar.connect("activate", self.on_url_activate)
        self.toolbar.pack_start(self.url_bar, True, True, 0)
        
        # ================= DEVELOPER TOOLS =================
        self.btn_inspect = Gtk.ToggleButton(label="[🔍 Inspect]")
        self.btn_inspect.get_style_context().add_class("glass-btn")
        self.btn_inspect.connect("toggled", self.on_inspect_toggled)
        self.toolbar.pack_start(self.btn_inspect, False, False, 0)
        
        self.ua_combo = Gtk.ComboBoxText()
        self.ua_combo.get_style_context().add_class("glass-combo")
        self.ua_combo.append_text("Default UA")
        self.ua_combo.append_text("Chrome/Windows")
        self.ua_combo.append_text("Safari/macOS")
        self.ua_combo.append_text("iPhone/iOS")
        self.ua_combo.append_text("Googlebot")
        self.ua_combo.set_active(0)
        self.ua_combo.connect("changed", self.on_ua_changed)
        self.toolbar.pack_start(self.ua_combo, False, False, 0)
        
        # ================= WORKSPACE =================
        self.paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        self.main_vbox.pack_start(self.paned, True, True, 0)
        
        self.notebook = Gtk.Notebook()
        self.notebook.get_style_context().add_class("glass-tabs")
        self.paned.pack1(self.notebook, True, False)
        
        # Inspector Container mock for layout
        self.inspector_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.inspector_box.get_style_context().add_class("inspector-box")
        self.paned.pack2(self.inspector_box, False, False)
        self.inspector_box.hide()
        
        self.new_tab("https://github.com")

    def new_tab(self, url):
        ctx = WebKit2.WebContext.new_ephemeral()
        webview = WebKit2.WebView.new_with_context(ctx)
        settings = webview.get_settings()
        settings.set_enable_developer_extras(True)
        webview.set_settings(settings)
        webview.load_uri(url)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.add(webview)
        
        label = Gtk.Label(label="New Tab")
        label.get_style_context().add_class("tab-label")
        self.notebook.append_page(scrolled, label)
        self.notebook.show_all()
        
        webview.connect("notify::uri", self.on_uri_changed)
        webview.connect("notify::title", lambda w, p: label.set_text(w.get_title() or "Untitled"))
        
        self.current_webview = webview
        
    def on_url_activate(self, entry):
        url = entry.get_text()
        if not url.startswith("http"): url = "https://" + url
        if hasattr(self, 'current_webview'):
            self.current_webview.load_uri(url)

    def on_uri_changed(self, webview, param):
        self.url_bar.set_text(webview.get_uri() or "")
        
    def on_inspect_toggled(self, btn):
        if not hasattr(self, 'current_webview'): return
        inspector = self.current_webview.get_inspector()
        if btn.get_active():
            inspector.show()
        else:
            inspector.close()

    def on_ua_changed(self, combo):
        if not hasattr(self, 'current_webview'): return
        uas = {
            0: None,
            1: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            2: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
            3: "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
            4: "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
        }
        idx = combo.get_active()
        settings = self.current_webview.get_settings()
        if uas[idx]:
            settings.set_user_agent(uas[idx])
        else:
            settings.set_user_agent(WebKit2.Settings().get_user_agent())
        self.current_webview.set_settings(settings)
        self.current_webview.reload()

    def setup_css(self):
        css = b'''
            window { background-color: transparent; }
            .hidden-header { background: rgba(10, 15, 20, 0.90); min-height: 0px; padding: 0px; border: none; box-shadow: none; }
            .glass-container { background: rgba(15, 20, 25, 0.88); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; box-shadow: 0 20px 50px rgba(0,0,0,0.8); }
            .glass-toolbar { background: rgba(0, 0, 0, 0.6); padding: 12px; border-bottom: 1px solid rgba(255, 255, 255, 0.05); }
            .glass-btn { background: rgba(255, 255, 255, 0.05); color: #00FFCC; border: 1px solid rgba(0, 255, 204, 0.3); border-radius: 8px; padding: 8px 15px; font-family: monospace; font-weight: bold; transition: all 0.2s; }
            .glass-btn:hover { background: rgba(0, 255, 204, 0.15); border: 1px solid rgba(0, 255, 204, 0.6); box-shadow: 0 0 10px rgba(0, 255, 204, 0.3); }
            .glass-btn:checked { background: rgba(0, 255, 204, 0.3); border: 1px solid #00FFCC; box-shadow: 0 0 15px rgba(0, 255, 204, 0.5); color: #FFFFFF; }
            .glass-url { background: rgba(0, 0, 0, 0.5); color: #FFFFFF; border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 8px; padding: 10px 15px; font-family: monospace; font-size: 14px; transition: all 0.2s; }
            .glass-url:focus { border: 1px solid #00FFCC; box-shadow: 0 0 10px rgba(0, 255, 204, 0.2); }
            .glass-combo { background: rgba(255, 255, 255, 0.05); color: #00FFCC; border-radius: 8px; font-family: monospace; padding: 5px; }
            .glass-tabs { background: rgba(10, 15, 20, 0.7); }
            .tab-label { color: #A0AAB5; font-family: sans-serif; font-weight: bold; font-size: 13px; padding: 5px 15px; }
            .inspector-box { background: #111111; border-top: 1px solid rgba(255, 255, 255, 0.1); }
        '''
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

if __name__ == "__main__":
    win = ZeroDevBrowser()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
