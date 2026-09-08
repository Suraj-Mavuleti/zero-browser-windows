import sys
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
from gi.repository import Gtk, Gdk, WebKit2

class ZeroBrowser(Gtk.Window):
    def __init__(self):
        super().__init__(title="Zero Browser - Ultimate WebKit Engine")
        self.set_default_size(1200, 800)
        
        # Apply Zero OS Custom GTK CSS Theme
        css = b'''
            window {
                background-color: #0B0C10;
            }
            .zero-header {
                background-color: #0B0C10;
                padding: 10px;
                border-bottom: 1px solid #1F2833;
            }
            .zero-urlbar {
                background-color: #161920;
                color: #66FCF1;
                border: 1px solid #1F2833;
                border-radius: 20px;
                padding: 8px 15px;
                font-family: monospace;
                font-size: 14px;
                caret-color: #66FCF1;
            }
            .zero-urlbar:focus {
                border: 1px solid #66FCF1;
                box-shadow: 0 0 5px rgba(102, 252, 241, 0.5);
            }
            .zero-btn {
                background-color: #1F2833;
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                padding: 8px 15px;
                font-weight: bold;
            }
            .zero-btn:hover {
                background-color: #2b3846;
                color: #66FCF1;
            }
            .zero-logo {
                color: #66FCF1;
                font-weight: bold;
                font-size: 18px;
                margin-right: 15px;
            }
        '''
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
        # Main Layout
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(vbox)
        
        # Header/Toolbar
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        toolbar.get_style_context().add_class("zero-header")
        
        logo = Gtk.Label(label="Z E R O")
        logo.get_style_context().add_class("zero-logo")
        toolbar.pack_start(logo, False, False, 5)
        
        self.btn_back = Gtk.Button(label="◀")
        self.btn_back.get_style_context().add_class("zero-btn")
        self.btn_back.connect("clicked", self.on_back_clicked)
        toolbar.pack_start(self.btn_back, False, False, 0)
        
        self.btn_forward = Gtk.Button(label="▶")
        self.btn_forward.get_style_context().add_class("zero-btn")
        self.btn_forward.connect("clicked", self.on_forward_clicked)
        toolbar.pack_start(self.btn_forward, False, False, 0)
        
        self.btn_reload = Gtk.Button(label="↻")
        self.btn_reload.get_style_context().add_class("zero-btn")
        self.btn_reload.connect("clicked", self.on_reload_clicked)
        toolbar.pack_start(self.btn_reload, False, False, 0)
        
        self.url_entry = Gtk.Entry()
        self.url_entry.get_style_context().add_class("zero-urlbar")
        self.url_entry.set_placeholder_text("Enter Search or URL...")
        self.url_entry.connect("activate", self.on_url_entered)
        toolbar.pack_start(self.url_entry, True, True, 10)
        
        self.btn_go = Gtk.Button(label="GO")
        self.btn_go.get_style_context().add_class("zero-btn")
        self.btn_go.connect("clicked", self.on_url_entered)
        toolbar.pack_start(self.btn_go, False, False, 0)
        
        vbox.pack_start(toolbar, False, False, 0)
        
        # WebKit Engine
        self.webview = WebKit2.WebView()
        self.webview.connect("load-changed", self.on_load_changed)
        
        # Enable hardware acceleration & smooth scrolling
        settings = self.webview.get_settings()
        settings.set_enable_smooth_scrolling(True)
        settings.set_enable_webgl(True)
        settings.set_enable_developer_extras(True)
        
        # Setup ScrolledWindow for the webview
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.add(self.webview)
        vbox.pack_start(scrolled_window, True, True, 0)
        
        # Initial Load
        self.webview.load_uri("https://duckduckgo.com")
        
    def on_url_entered(self, widget):
        url = self.url_entry.get_text()
        if not url.startswith("http://") and not url.startswith("https://"):
            if "." in url and " " not in url:
                url = "https://" + url
            else:
                url = "https://duckduckgo.com/?q=" + url.replace(" ", "+")
        self.webview.load_uri(url)
        
    def on_load_changed(self, webview, load_event):
        if load_event == WebKit2.LoadEvent.COMMITTED:
            self.url_entry.set_text(self.webview.get_uri())
            
    def on_back_clicked(self, widget):
        if self.webview.can_go_back():
            self.webview.go_back()
            
    def on_forward_clicked(self, widget):
        if self.webview.can_go_forward():
            self.webview.go_forward()
            
    def on_reload_clicked(self, widget):
        self.webview.reload()

if __name__ == "__main__":
    win = ZeroBrowser()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
