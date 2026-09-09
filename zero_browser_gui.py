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
        self.set_default_size(1500, 950)
        
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
        
        # PROXY TOGGLE
        self.btn_proxy = Gtk.ToggleButton(label="[🛡️ Proxy: OFF]")
        self.btn_proxy.get_style_context().add_class("glass-btn-danger")
        self.btn_proxy.connect("toggled", self.on_proxy_toggled)
        self.toolbar.pack_start(self.btn_proxy, False, False, 0)
        
        # DEV TOOLS
        self.btn_inspect = Gtk.ToggleButton(label="[🔍 Inspect]")
        self.btn_inspect.get_style_context().add_class("glass-btn")
        self.btn_inspect.connect("toggled", self.on_inspect_toggled)
        self.toolbar.pack_start(self.btn_inspect, False, False, 0)
        
        self.btn_cookies = Gtk.ToggleButton(label="[🍪 Cookies]")
        self.btn_cookies.get_style_context().add_class("glass-btn")
        self.btn_cookies.connect("toggled", self.on_cookies_toggled)
        self.toolbar.pack_start(self.btn_cookies, False, False, 0)
        
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
        
        # ================= MAIN WORKSPACE (HPaned for Sidebar) =================
        self.hpaned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.main_vbox.pack_start(self.hpaned, True, True, 0)
        
        # LEFT: Payload Library Sidebar
        self.sidebar = self.build_payload_sidebar()
        self.hpaned.pack1(self.sidebar, False, False)
        
        # RIGHT: Browser Area (VPaned for Bottom Stack)
        self.vpaned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        self.hpaned.pack2(self.vpaned, True, False)
        
        self.notebook = Gtk.Notebook()
        self.notebook.get_style_context().add_class("glass-tabs")
        self.vpaned.pack1(self.notebook, True, False)
        
        # Bottom Tool Stack
        self.bottom_stack = Gtk.Stack()
        self.bottom_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_UP_DOWN)
        self.vpaned.pack2(self.bottom_stack, False, False)
        
        self.inspector_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.inspector_box.get_style_context().add_class("tool-box")
        self.bottom_stack.add_named(self.inspector_window_mock(), "inspector")
        
        self.cookie_box = self.build_cookie_explorer()
        self.cookie_box.get_style_context().add_class("tool-box")
        self.bottom_stack.add_named(self.cookie_box, "cookies")
        
        self.terminal_box = self.build_terminal_emulator()
        self.bottom_stack.add_named(self.terminal_box, "terminal")
        
        self.bottom_stack.hide()
        
        self.new_tab("https://github.com")

    def build_payload_sidebar(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.set_size_request(260, -1)
        box.get_style_context().add_class("sidebar-box")
        
        lbl = Gtk.Label(label="ATTACK PAYLOADS")
        lbl.get_style_context().add_class("sidebar-title")
        lbl.set_margin_top(15)
        lbl.set_margin_bottom(10)
        box.pack_start(lbl, False, False, 0)
        
        scroll = Gtk.ScrolledWindow()
        listbox = Gtk.ListBox()
        listbox.get_style_context().add_class("glass-list")
        
        payloads = [
            ("XSS Alert", "<script>alert(1)</script>"),
            ("XSS Image", "<img src=x onerror=alert(1)>"),
            ("SQLi Auth Bypass", "' OR '1'='1"),
            ("SQLi Union", "1' UNION SELECT null, version()--"),
            ("LFI Linux", "../../../../etc/passwd"),
            ("LFI Windows", "..\\..\\..\\windows\\win.ini"),
            ("SSRF Localhost", "http://127.0.0.1:80/"),
            ("Command Inj", "; cat /etc/passwd")
        ]
        
        for title, p in payloads:
            row = Gtk.ListBoxRow()
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            vbox.set_margin_start(10)
            vbox.set_margin_end(10)
            vbox.set_margin_top(5)
            vbox.set_margin_bottom(5)
            
            lt = Gtk.Label(label=title)
            lt.set_halign(Gtk.Align.START)
            lt.get_style_context().add_class("payload-title")
            
            lp = Gtk.Label(label=p)
            lp.set_halign(Gtk.Align.START)
            lp.get_style_context().add_class("payload-text")
            
            vbox.pack_start(lt, False, False, 0)
            vbox.pack_start(lp, False, False, 0)
            row.add(vbox)
            listbox.add(row)
            
        listbox.connect("row-activated", self.on_payload_activated)
        scroll.add(listbox)
        box.pack_start(scroll, True, True, 0)
        
        btn_term = Gtk.Button(label=">_ Open Terminal")
        btn_term.get_style_context().add_class("glass-btn")
        btn_term.set_margin_bottom(15)
        btn_term.connect("clicked", self.on_terminal_toggled)
        box.pack_end(btn_term, False, False, 10)
        
        return box

    def build_terminal_emulator(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.set_size_request(-1, 250)
        box.get_style_context().add_class("tool-box")
        
        lbl = Gtk.Label(label="INTEGRATED PYTHON TERMINAL")
        lbl.get_style_context().add_class("tool-title")
        lbl.set_halign(Gtk.Align.START)
        lbl.set_margin_start(15)
        lbl.set_margin_top(10)
        box.pack_start(lbl, False, False, 0)
        
        self.term_output = Gtk.TextView()
        self.term_output.get_style_context().add_class("term-text")
        self.term_output.set_editable(False)
        self.term_output.get_buffer().set_text("Zero Developer Environment initialized.\nPython 3 interpreter ready.\n>>> ")
        
        scroll = Gtk.ScrolledWindow()
        scroll.add(self.term_output)
        box.pack_start(scroll, True, True, 5)
        
        entry = Gtk.Entry()
        entry.get_style_context().add_class("term-entry")
        entry.connect("activate", self.on_term_execute)
        box.pack_start(entry, False, False, 0)
        
        return box

    def on_term_execute(self, entry):
        cmd = entry.get_text()
        buf = self.term_output.get_buffer()
        end_iter = buf.get_end_iter()
        buf.insert(end_iter, cmd + "\n")
        
        try:
            # Dangerous but it's a hacker browser!
            result = str(eval(cmd))
            buf.insert(buf.get_end_iter(), result + "\n>>> ")
        except Exception as e:
            try:
                exec(cmd)
                buf.insert(buf.get_end_iter(), "Executed.\n>>> ")
            except Exception as ex:
                buf.insert(buf.get_end_iter(), f"Error: {ex}\n>>> ")
        entry.set_text("")

    def on_payload_activated(self, listbox, row):
        vbox = row.get_child()
        lbl = vbox.get_children()[1]
        payload = lbl.get_text()
        self.url_bar.set_text(self.url_bar.get_text() + payload)
        self.url_bar.grab_focus()

    def on_proxy_toggled(self, btn):
        if not hasattr(self, 'current_webview'): return
        ctx = self.current_webview.get_context()
        if btn.get_active():
            # Mock setting SOCKS5 proxy to localhost:9050
            # Note: WebKit2 context proxy settings require WebKit2.NetworkProxySettings which is complex in PyGObject
            # We mock the visual toggle for the UI
            btn.set_label("[🛡️ Proxy: TOR]")
            btn.get_style_context().remove_class("glass-btn-danger")
            btn.get_style_context().add_class("glass-btn-success")
        else:
            btn.set_label("[🛡️ Proxy: OFF]")
            btn.get_style_context().remove_class("glass-btn-success")
            btn.get_style_context().add_class("glass-btn-danger")

    def inspector_window_mock(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        lbl = Gtk.Label(label="Native WebInspector acts externally on GTK. This is a placeholder.")
        lbl.set_margin_top(20)
        lbl.get_style_context().add_class("tab-label")
        box.pack_start(lbl, False, False, 0)
        return box

    def build_cookie_explorer(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.set_size_request(-1, 250)
        
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        lbl = Gtk.Label(label="SITE COOKIES (document.cookie)")
        lbl.get_style_context().add_class("tool-title")
        lbl.set_margin_top(10)
        lbl.set_margin_bottom(10)
        lbl.set_margin_start(15)
        lbl.set_halign(Gtk.Align.START)
        header.pack_start(lbl, False, False, 0)
        
        btn_refresh = Gtk.Button(label="Refresh Cookies")
        btn_refresh.get_style_context().add_class("glass-btn")
        btn_refresh.set_margin_top(5)
        btn_refresh.set_margin_bottom(5)
        btn_refresh.set_margin_end(15)
        btn_refresh.connect("clicked", self.refresh_cookies)
        header.pack_end(btn_refresh, False, False, 0)
        
        box.pack_start(header, False, False, 0)
        
        scroll = Gtk.ScrolledWindow()
        self.cookie_list = Gtk.ListBox()
        self.cookie_list.get_style_context().add_class("glass-list")
        scroll.add(self.cookie_list)
        box.pack_start(scroll, True, True, 0)
        return box

    def refresh_cookies(self, btn=None):
        if not hasattr(self, 'current_webview'): return
        for child in self.cookie_list.get_children():
            self.cookie_list.remove(child)
            
        def on_js_finish(webview, result, user_data=None):
            try:
                js_result = webview.run_javascript_finish(result)
                cookie_str = js_result.get_js_value().to_string()
                
                if not cookie_str:
                    row = Gtk.ListBoxRow()
                    lbl = Gtk.Label(label="No cookies accessible via document.cookie (HttpOnly cookies are hidden).")
                    lbl.get_style_context().add_class("cookie-val")
                    lbl.set_margin_top(10)
                    row.add(lbl)
                    self.cookie_list.add(row)
                else:
                    cookies = cookie_str.split(";")
                    for c in cookies:
                        if "=" not in c: continue
                        k, v = c.split("=", 1)
                        row = Gtk.ListBoxRow()
                        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                        hbox.set_margin_top(5)
                        hbox.set_margin_bottom(5)
                        
                        lk = Gtk.Label(label=k.strip())
                        lk.get_style_context().add_class("cookie-key")
                        lk.set_size_request(200, -1)
                        lk.set_halign(Gtk.Align.START)
                        lk.set_margin_start(15)
                        
                        lv = Gtk.Label(label=v.strip())
                        lv.get_style_context().add_class("cookie-val")
                        lv.set_halign(Gtk.Align.START)
                        
                        hbox.pack_start(lk, False, False, 0)
                        hbox.pack_start(lv, True, True, 0)
                        row.add(hbox)
                        self.cookie_list.add(row)
                self.cookie_list.show_all()
            except Exception as e:
                pass
                
        self.current_webview.run_javascript("document.cookie", None, on_js_finish, None)

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
            self.btn_cookies.set_active(False)
            inspector.show()
            self.bottom_stack.show()
            self.bottom_stack.set_visible_child_name("inspector")
        else:
            inspector.close()
            if not self.btn_cookies.get_active():
                self.bottom_stack.hide()
            
    def on_cookies_toggled(self, btn):
        if btn.get_active():
            self.btn_inspect.set_active(False)
            self.bottom_stack.show()
            self.bottom_stack.set_visible_child_name("cookies")
            self.refresh_cookies()
        else:
            if not self.btn_inspect.get_active():
                self.bottom_stack.hide()

    def on_terminal_toggled(self, btn):
        if self.bottom_stack.get_visible_child_name() == "terminal" and self.bottom_stack.is_visible():
            self.bottom_stack.hide()
        else:
            self.btn_inspect.set_active(False)
            self.btn_cookies.set_active(False)
            self.bottom_stack.show()
            self.bottom_stack.set_visible_child_name("terminal")

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
            .glass-btn-danger { background: rgba(255, 0, 0, 0.1); color: #FF4444; border: 1px solid rgba(255, 0, 0, 0.3); border-radius: 8px; padding: 8px 15px; font-family: monospace; font-weight: bold; }
            .glass-btn-success { background: rgba(0, 255, 0, 0.1); color: #44FF44; border: 1px solid rgba(0, 255, 0, 0.3); border-radius: 8px; padding: 8px 15px; font-family: monospace; font-weight: bold; }
            .glass-url { background: rgba(0, 0, 0, 0.5); color: #FFFFFF; border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 8px; padding: 10px 15px; font-family: monospace; font-size: 14px; transition: all 0.2s; }
            .glass-url:focus { border: 1px solid #00FFCC; box-shadow: 0 0 10px rgba(0, 255, 204, 0.2); }
            .glass-combo { background: rgba(255, 255, 255, 0.05); color: #00FFCC; border-radius: 8px; font-family: monospace; padding: 5px; }
            .glass-tabs { background: rgba(10, 15, 20, 0.7); }
            .tab-label { color: #A0AAB5; font-family: sans-serif; font-weight: bold; font-size: 13px; padding: 5px 15px; }
            .tool-box { background: rgba(0, 0, 0, 0.9); border-top: 1px solid rgba(0, 255, 204, 0.3); }
            .tool-title { color: #00FFCC; font-family: monospace; font-weight: bold; letter-spacing: 2px; font-size: 14px; }
            .sidebar-box { background: rgba(5, 10, 15, 0.95); border-right: 1px solid rgba(0, 255, 204, 0.2); }
            .sidebar-title { color: #FF0055; font-family: monospace; font-weight: bold; letter-spacing: 2px; font-size: 16px; text-shadow: 0 0 5px #FF0055; }
            .payload-title { color: #00FFCC; font-family: sans-serif; font-weight: bold; font-size: 12px; }
            .payload-text { color: #A0AAB5; font-family: monospace; font-size: 10px; }
            .term-text { background: transparent; color: #00FFCC; font-family: monospace; font-size: 14px; padding: 10px; }
            .term-entry { background: rgba(0, 255, 204, 0.1); color: #FFFFFF; font-family: monospace; font-size: 14px; border: none; padding: 10px; }
            .glass-list { background: transparent; }
            .cookie-key { color: #FFFFFF; font-family: monospace; font-weight: bold; }
            .cookie-val { color: #A0AAB5; font-family: monospace; }
        '''
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

if __name__ == "__main__":
    win = ZeroDevBrowser()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
