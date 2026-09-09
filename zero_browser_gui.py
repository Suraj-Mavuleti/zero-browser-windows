import sys
import gi
import os
import random
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, Gdk, GLib
from gi.repository import WebKit2

class ZeroHackerBrowser(Gtk.Window):
    def __init__(self):
        super().__init__(title="Zero Browser - Developer Edition")
        self.set_default_size(1600, 1000)
        
        self.header = Gtk.HeaderBar()
        self.header.set_show_close_button(True)
        self.header.props.title = ""
        self.header.get_style_context().add_class("hidden-header")
        self.set_titlebar(self.header)
        
        self.setup_css()
        
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.add(main_box)
        
        # ================= LEFT SIDEBAR (Hacker Tools) =================
        self.sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.sidebar.set_size_request(280, -1)
        self.sidebar.get_style_context().add_class("sidebar")
        main_box.pack_start(self.sidebar, False, False, 0)
        
        logo = Gtk.Label(label="Z E R O // D E V")
        logo.get_style_context().add_class("logo-glitch")
        logo.set_margin_top(25)
        logo.set_margin_bottom(20)
        self.sidebar.pack_start(logo, False, False, 0)
        
        # Developer Tools Panel
        l_tools = Gtk.Label(label="ATTACK VECTOR TOOLS")
        l_tools.get_style_context().add_class("section-label")
        l_tools.set_halign(Gtk.Align.START)
        l_tools.set_margin_start(20)
        l_tools.set_margin_bottom(10)
        self.sidebar.pack_start(l_tools, False, False, 0)
        
        tools = [
            ("📡 Network Interceptor", "ACTIVE"),
            ("🍪 Cookie Forger", "READY"),
            ("🎭 User-Agent Spoof", "LINUX/X11"),
            ("🛡️ Proxy Chain", "TOR ROUTED"),
            ("🔌 Websocket Sniffer", "LISTENING")
        ]
        
        for name, status in tools:
            btn = Gtk.Button()
            btn.get_style_context().add_class("tool-btn")
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            box.pack_start(Gtk.Label(label=name), True, True, 0)
            s_lbl = Gtk.Label(label=status)
            s_lbl.get_style_context().add_class("tool-status")
            box.pack_end(s_lbl, False, False, 0)
            btn.add(box)
            self.sidebar.pack_start(btn, False, False, 5)
            
        # Terminal Mock in Sidebar
        self.sidebar.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 15)
        
        term_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        term_box.get_style_context().add_class("terminal-container")
        term_box.set_margin_start(15)
        term_box.set_margin_end(15)
        term_box.set_margin_bottom(20)
        
        term_lbl = Gtk.Label(label="root@zero:~# nmap -sS -p- target\\nStarting Nmap 7.93...\\nDiscovered open port 80/tcp\\nDiscovered open port 443/tcp")
        term_lbl.get_style_context().add_class("terminal-text")
        term_lbl.set_halign(Gtk.Align.START)
        term_lbl.set_valign(Gtk.Align.START)
        term_lbl.set_line_wrap(True)
        term_box.pack_start(term_lbl, True, True, 10)
        
        self.sidebar.pack_end(term_box, True, True, 0)

        # ================= MAIN WORKSPACE =================
        self.workspace = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.workspace.get_style_context().add_class("workspace")
        main_box.pack_start(self.workspace, True, True, 0)
        
        # URL Bar / Navigation
        nav_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        nav_bar.get_style_context().add_class("nav-bar")
        self.workspace.pack_start(nav_bar, False, False, 0)
        
        self.url_entry = Gtk.Entry()
        self.url_entry.set_placeholder_text("Target URI...")
        self.url_entry.get_style_context().add_class("url-bar")
        self.url_entry.connect("activate", self.on_url_entered)
        nav_bar.pack_start(self.url_entry, True, True, 0)
        
        btn_exec = Gtk.Button(label="[ EXECUTE ]")
        btn_exec.get_style_context().add_class("exec-btn")
        btn_exec.connect("clicked", lambda w: self.on_url_entered(self.url_entry))
        nav_bar.pack_start(btn_exec, False, False, 0)
        
        # Web View
        ctx = WebKit2.WebContext.new_ephemeral()
        self.webview = WebKit2.WebView.new_with_context(ctx)
        self.webview.connect("notify::uri", self.on_uri_changed)
        
        # Force Developer Tools to be allowed
        settings = self.webview.get_settings()
        settings.set_enable_developer_extras(True)
        self.webview.set_settings(settings)
        
        self.workspace.pack_start(self.webview, True, True, 0)
        
        # ================= BOTTOM PANEL (Network Monitor) =================
        net_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        net_panel.get_style_context().add_class("net-panel")
        net_panel.set_size_request(-1, 200)
        self.workspace.pack_end(net_panel, False, False, 0)
        
        l_net = Gtk.Label(label="NETWORK TRAFFIC MONITOR")
        l_net.get_style_context().add_class("section-label")
        l_net.set_halign(Gtk.Align.START)
        l_net.set_margin_start(10)
        l_net.set_margin_top(5)
        l_net.set_margin_bottom(5)
        net_panel.pack_start(l_net, False, False, 0)
        
        scroll = Gtk.ScrolledWindow()
        self.net_list = Gtk.ListBox()
        self.net_list.get_style_context().add_class("transparent-list")
        scroll.add(self.net_list)
        net_panel.pack_start(scroll, True, True, 0)
        
        # Initial Load
        self.webview.load_uri("https://hackerone.com")
        
        # Start random traffic generator
        GLib.timeout_add(1500, self.inject_mock_traffic)

    def on_url_entered(self, entry):
        url = entry.get_text()
        if not url.startswith("http"): url = "https://" + url
        self.webview.load_uri(url)

    def on_uri_changed(self, webview, param):
        self.url_entry.set_text(webview.get_uri() or "")
        
    def inject_mock_traffic(self):
        methods = ["GET", "POST", "OPTIONS", "PUT"]
        status = ["200 OK", "404 NOT FOUND", "403 FORBIDDEN", "500 SERVER ERROR"]
        endpoints = ["/api/v1/users", "/auth/login", "/wp-admin", "/config.json", "/.git/HEAD"]
        
        m = random.choice(methods)
        s = random.choice(status)
        e = random.choice(endpoints)
        
        row = Gtk.ListBoxRow()
        row.get_style_context().add_class("net-row")
        
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        lbl_m = Gtk.Label(label=m)
        lbl_m.set_size_request(60, -1)
        lbl_m.get_style_context().add_class(f"net-{m.lower()}")
        
        lbl_e = Gtk.Label(label=e)
        lbl_e.set_margin_start(10)
        
        lbl_s = Gtk.Label(label=s)
        if "200" in s: lbl_s.get_style_context().add_class("net-200")
        else: lbl_s.get_style_context().add_class("net-error")
        
        box.pack_start(lbl_m, False, False, 0)
        box.pack_start(lbl_e, True, True, 0)
        box.pack_end(lbl_s, False, False, 10)
        
        row.add(box)
        self.net_list.prepend(row)
        self.net_list.show_all()
        
        # Keep list small
        if len(self.net_list.get_children()) > 20:
            self.net_list.remove(self.net_list.get_children()[-1])
            
        return True # Continue timer

    def setup_css(self):
        css = b'''
            window { background-color: #050A0F; }
            .hidden-header { background: #050A0F; min-height: 0px; padding: 0px; border: none; box-shadow: none; }
            .sidebar { background-color: #020406; border-right: 1px solid #00FF41; }
            .logo-glitch { color: #00FF41; font-size: 22px; font-weight: 900; letter-spacing: 4px; text-shadow: 2px 0 #FF003C, -2px 0 #00E6F6; font-family: monospace; }
            .section-label { color: #008F11; font-size: 12px; font-weight: 900; letter-spacing: 2px; font-family: monospace; }
            .tool-btn { background: #0A141A; border: 1px solid #003B00; border-radius: 0; margin: 0 15px; padding: 10px; color: #00FF41; font-family: monospace; transition: all 0.2s; }
            .tool-btn:hover { background: #00FF41; color: #000000; }
            .tool-status { font-size: 10px; font-weight: bold; }
            .terminal-container { background: #000000; border: 1px solid #00FF41; box-shadow: inset 0 0 49px #00E6F6; }
            .terminal-text { color: #00FF41; font-family: monospace; font-size: 12px; }
            .workspace { background-color: #0A141A; }
            .nav-bar { background: #020406; padding: 15px; border-bottom: 1px solid #00FF41; }
            .url-bar { background: #000000; color: #00FF41; border: 1px solid #00FF41; border-radius: 0; padding: 10px; font-family: monospace; font-size: 16px; box-shadow: 0 0 10px rgba(0,255,65,0.2); }
            .exec-btn { background: #00FF41; color: #000000; border: none; font-weight: bold; font-family: monospace; padding: 10px 20px; border-radius: 0; }
            .exec-btn:hover { background: #FFFFFF; }
            .net-panel { background: #020406; border-top: 1px solid #00FF41; }
            .transparent-list { background: transparent; }
            .net-row { background: transparent; color: #00FF41; font-family: monospace; padding: 4px; border-bottom: 1px solid #003B00; }
            .net-get { color: #00E6F6; }
            .net-post { color: #FF003C; }
            .net-options { color: #F6FF00; }
            .net-put { color: #FF8A00; }
            .net-200 { color: #00FF41; }
            .net-error { color: #FF003C; font-weight: bold; }
        '''
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

if __name__ == "__main__":
    win = ZeroHackerBrowser()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
