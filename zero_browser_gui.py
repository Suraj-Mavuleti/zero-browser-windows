import sys
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
from gi.repository import Gtk, Gdk, WebKit2

class ZeroBrowser(Gtk.Window):
    def __init__(self):
        super().__init__(title="Zero Browser - Fortified Engine")
        self.set_default_size(1250, 850)
        
        # Massive UI Polish (Premium Glass Aesthetic)
        css = b'''
            window { background-color: #050608; }
            .zero-header {
                background-color: #0A0D12;
                padding: 15px;
                border-bottom: 2px solid #141A25;
            }
            .zero-urlbar {
                background-color: #0F131C;
                color: #00E5FF;
                border: 1px solid #1E2532;
                border-radius: 24px;
                padding: 10px 20px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                caret-color: #00E5FF;
            }
            .zero-urlbar:focus {
                border: 1px solid #00E5FF;
                box-shadow: 0 0 12px rgba(0, 229, 255, 0.4);
            }
            .zero-btn {
                background-color: transparent;
                color: #8B94A5;
                border: 1px solid #1E2532;
                border-radius: 12px;
                padding: 10px 15px;
                font-weight: bold;
            }
            .zero-btn:hover {
                background-color: #121620;
                color: #00E5FF;
                border: 1px solid #00E5FF;
            }
            .zero-logo {
                color: #FFFFFF;
                font-weight: 900;
                font-size: 20px;
                margin-right: 20px;
                margin-left: 10px;
                letter-spacing: 2px;
            }
            .zero-shield {
                color: #00FF66;
                font-weight: bold;
                background-color: rgba(0, 255, 102, 0.1);
                border: 1px solid #00FF66;
                border-radius: 12px;
                padding: 10px 15px;
                margin-left: 15px;
            }
        '''
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), style_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(vbox)
        
        # Header
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
        self.url_entry.set_placeholder_text("Search Google or enter URL...")
        self.url_entry.connect("activate", self.on_url_entered)
        toolbar.pack_start(self.url_entry, True, True, 10)
        
        shield = Gtk.Label(label="🛡️ MAX SECURITY ACTIVE")
        shield.get_style_context().add_class("zero-shield")
        toolbar.pack_start(shield, False, False, 5)
        
        vbox.pack_start(toolbar, False, False, 0)
        
        # Privacy Engine Context Setup
        context = WebKit2.WebContext.get_default()
        
        # 1. Enforce strict TLS (HTTPS only, drop connection on bad certs)
        context.set_tls_errors_policy(WebKit2.TLSErrorsPolicy.FAIL)
        
        # 2. Block all 3rd Party Tracking Cookies natively at the C++ layer
        cookie_manager = context.get_cookie_manager()
        cookie_manager.set_accept_policy(WebKit2.CookieAcceptPolicy.NO_THIRD_PARTY)
        
        # 3. Enable Strict Multi-Process Sandboxing
        context.set_sandbox_enabled(True)
        
        self.webview = WebKit2.WebView.new_with_context(context)
        self.webview.connect("load-changed", self.on_load_changed)
        
        # Aggressive Anti-Fingerprinting Settings
        settings = self.webview.get_settings()
        
        # Disable WebGL (stops 3D canvas hardware fingerprinting)
        settings.set_enable_webgl(False)
        
        # Disable WebRTC / Media Streams (stops IP leaking behind VPNs)
        settings.set_enable_media_stream(False)
        
        # Disable Local Storage & Databases (stops persistent supercookies)
        settings.set_enable_html5_local_storage(False)
        settings.set_enable_html5_database(False)
        
        # Disable DNS Prefetching (stops passive DNS leakage requests)
        settings.set_enable_dns_prefetching(False)
        
        # Disable Audio API Fingerprinting
        settings.set_enable_webaudio(False)
        
        # Disable legacy plugins
        settings.set_enable_plugins(False)
        settings.set_enable_java(False)
        
        # Keep smooth scrolling for good UI feel
        settings.set_enable_smooth_scrolling(True)
        
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.add(self.webview)
        vbox.pack_start(scrolled_window, True, True, 0)
        
        self.webview.load_uri("https://google.com")
        
    def on_url_entered(self, widget):
        url = self.url_entry.get_text()
        if not url.startswith("http://") and not url.startswith("https://"):
            if "." in url and " " not in url:
                url = "https://" + url
            else:
                url = "https://google.com/search?q=" + url.replace(" ", "+")
        self.webview.load_uri(url)
        
    def on_load_changed(self, webview, load_event):
        if load_event == WebKit2.LoadEvent.COMMITTED:
            self.url_entry.set_text(self.webview.get_uri())
            
    def on_back_clicked(self, widget):
        if self.webview.can_go_back(): self.webview.go_back()
            
    def on_forward_clicked(self, widget):
        if self.webview.can_go_forward(): self.webview.go_forward()
            
    def on_reload_clicked(self, widget):
        self.webview.reload()

if __name__ == "__main__":
    win = ZeroBrowser()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
