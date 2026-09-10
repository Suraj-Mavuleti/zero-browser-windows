import sys
import gi
import os
import json
from datetime import datetime
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
from gi.repository import Gtk, Gdk, GLib, Pango
from gi.repository import WebKit2

class ZeroDevBrowser(Gtk.Window):
    def __init__(self):
        super().__init__(title="Zero Browser - Premium Developer Studio")
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
        
        # State
        self.history_store = Gtk.ListStore(str, str) # Time, URL
        self.downloads_store = Gtk.ListStore(str, str, str) # Filename, Status, Progress
        self.custom_headers = []
        
        self.main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_vbox.get_style_context().add_class("glass-container")
        self.add(self.main_vbox)
        
        # ================= TOOLBAR 1 =================
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
        
        # PROXY & SECURITY
        self.btn_proxy = Gtk.ToggleButton(label="🛡️ Proxy")
        self.btn_proxy.get_style_context().add_class("glass-btn-danger")
        self.btn_proxy.connect("toggled", self.on_proxy_toggled)
        self.toolbar.pack_start(self.btn_proxy, False, False, 0)
        
        self.btn_webrtc = Gtk.ToggleButton(label="WebRTC: Leak")
        self.btn_webrtc.get_style_context().add_class("glass-btn-danger")
        self.btn_webrtc.connect("toggled", self.on_webrtc_toggled)
        self.toolbar.pack_start(self.btn_webrtc, False, False, 0)
        
        self.btn_cors = Gtk.ToggleButton(label="CORS: Strict")
        self.btn_cors.get_style_context().add_class("glass-btn-danger")
        self.btn_cors.connect("toggled", self.on_cors_toggled)
        self.toolbar.pack_start(self.btn_cors, False, False, 0)
        
        self.ua_combo = Gtk.ComboBoxText()
        self.ua_combo.get_style_context().add_class("glass-combo")
        for ua in ["Default UA", "Chrome/Windows", "Safari/macOS", "iPhone/iOS", "Googlebot"]:
            self.ua_combo.append_text(ua)
        self.ua_combo.set_active(0)
        self.ua_combo.connect("changed", self.on_ua_changed)
        self.toolbar.pack_start(self.ua_combo, False, False, 0)
        
        # ================= TOOLBAR 2 (DEV TOOLS) =================
        self.toolbar2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.toolbar2.get_style_context().add_class("glass-toolbar")
        self.main_vbox.pack_start(self.toolbar2, False, False, 0)
        
        self.dev_buttons = {}
        for text, key, cb in [
            ("🔍 Inspect", "inspector", self.on_inspect_toggled),
            ("🍪 Cookies", "cookies", self.on_cookies_toggled),
            ("💾 Storage", "storage", self.on_storage_toggled),
            ("📑 Headers", "headers", self.on_headers_toggled),
            ("🎨 CSS", "css", self.on_css_toggled),
            ("📄 Source", "source", self.on_source_toggled),
            ("🌐 Network", "network", self.on_network_toggled),
            ("⚡ JS", "js_console", self.on_js_toggled)
        ]:
            b = Gtk.ToggleButton(label=text)
            b.get_style_context().add_class("glass-btn")
            b.connect("toggled", cb)
            self.toolbar2.pack_start(b, False, False, 0)
            self.dev_buttons[key] = b
            
        self.btn_tech = Gtk.Button(label="🤖 Stack")
        self.btn_tech.get_style_context().add_class("glass-btn")
        self.btn_tech.connect("clicked", self.on_tech_detect)
        self.toolbar2.pack_start(self.btn_tech, False, False, 0)
        
        # ================= MAIN WORKSPACE =================
        self.hpaned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.main_vbox.pack_start(self.hpaned, True, True, 0)
        
        self.sidebar = self.build_unified_sidebar()
        self.hpaned.pack1(self.sidebar, False, False)
        
        self.vpaned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        self.hpaned.pack2(self.vpaned, True, False)
        
        self.notebook = Gtk.Notebook()
        self.notebook.get_style_context().add_class("glass-tabs")
        self.vpaned.pack1(self.notebook, True, False)
        
        self.bottom_stack = Gtk.Stack()
        self.bottom_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_UP_DOWN)
        self.vpaned.pack2(self.bottom_stack, False, False)
        
        # Build all panels
        self.inspector_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        lbl = Gtk.Label(label="Native WebInspector acts externally on GTK.")
        lbl.get_style_context().add_class("tab-label")
        self.inspector_box.pack_start(lbl, False, False, 20)
        self.bottom_stack.add_named(self.inspector_box, "inspector")
        
        self.cookie_box = self.build_cookie_explorer()
        self.bottom_stack.add_named(self.cookie_box, "cookies")
        self.storage_box = self.build_storage_explorer()
        self.bottom_stack.add_named(self.storage_box, "storage")
        self.terminal_box = self.build_terminal_emulator()
        self.bottom_stack.add_named(self.terminal_box, "terminal")
        self.headers_box = self.build_headers_panel()
        self.bottom_stack.add_named(self.headers_box, "headers")
        self.css_box = self.build_css_panel()
        self.bottom_stack.add_named(self.css_box, "css")
        self.source_box = self.build_source_viewer()
        self.bottom_stack.add_named(self.source_box, "source")
        self.network_box = self.build_network_panel()
        self.bottom_stack.add_named(self.network_box, "network")
        self.js_console_box = self.build_js_console()
        self.bottom_stack.add_named(self.js_console_box, "js_console")
        
        self.bottom_stack.hide()
        
        # Global WebKit Context for Downloads
        self.web_ctx = WebKit2.WebContext.new_ephemeral()
        self.web_ctx.connect("download-started", self.on_download_started)
        
        self.new_tab("https://github.com")

    # ================= UNIFIED SIDEBAR (Payloads, History, Downloads) =================
    def build_unified_sidebar(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.set_size_request(280, -1)
        box.get_style_context().add_class("sidebar-box")
        
        notebook = Gtk.Notebook()
        notebook.get_style_context().add_class("glass-tabs-sidebar")
        
        # 1. Payloads
        payload_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        scroll = Gtk.ScrolledWindow()
        listbox = Gtk.ListBox()
        listbox.get_style_context().add_class("glass-list")
        payloads = [
            ("XSS Alert", "<script>alert(1)</script>"),
            ("XSS Image", "<img src=x onerror=alert(1)>"),
            ("SQLi Auth Bypass", "' OR '1'='1"),
            ("SQLi Union", "1' UNION SELECT null, version()--"),
            ("LFI Linux", "../../../../etc/passwd"),
            ("SSRF Localhost", "http://127.0.0.1:80/"),
            ("DOM Tree", "javascript:alert(document.documentElement.innerHTML)")
        ]
        for title, p in payloads:
            row = Gtk.ListBoxRow(); v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            lt = Gtk.Label(label=title); lt.set_halign(Gtk.Align.START); lt.get_style_context().add_class("payload-title")
            lp = Gtk.Label(label=p); lp.set_halign(Gtk.Align.START); lp.get_style_context().add_class("payload-text")
            v.pack_start(lt, False, False, 2); v.pack_start(lp, False, False, 2); row.add(v); listbox.add(row)
        listbox.connect("row-activated", self.on_payload_activated)
        scroll.add(listbox); payload_box.pack_start(scroll, True, True, 0)
        btn_term = Gtk.Button(label=">_ Python Terminal")
        btn_term.get_style_context().add_class("glass-btn")
        btn_term.connect("clicked", self.on_terminal_toggled)
        payload_box.pack_end(btn_term, False, False, 10)
        
        lbl_p = Gtk.Label(label="Exploits"); lbl_p.get_style_context().add_class("tab-label-side")
        notebook.append_page(payload_box, lbl_p)
        
        # 2. History
        hist_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        hist_tree = Gtk.TreeView(model=self.history_store)
        hist_tree.get_style_context().add_class("glass-tree")
        renderer = Gtk.CellRendererText()
        col1 = Gtk.TreeViewColumn("Time", renderer, text=0); hist_tree.append_column(col1)
        col2 = Gtk.TreeViewColumn("URL", renderer, text=1); hist_tree.append_column(col2)
        hist_scroll = Gtk.ScrolledWindow(); hist_scroll.add(hist_tree)
        hist_box.pack_start(hist_scroll, True, True, 0)
        lbl_h = Gtk.Label(label="History"); lbl_h.get_style_context().add_class("tab-label-side")
        notebook.append_page(hist_box, lbl_h)
        hist_tree.connect("row-activated", self.on_history_activated)
        
        # 3. Downloads
        dl_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        dl_tree = Gtk.TreeView(model=self.downloads_store)
        dl_tree.get_style_context().add_class("glass-tree")
        rend2 = Gtk.CellRendererText()
        dl_tree.append_column(Gtk.TreeViewColumn("File", rend2, text=0))
        dl_tree.append_column(Gtk.TreeViewColumn("Status", rend2, text=1))
        dl_tree.append_column(Gtk.TreeViewColumn("Prog", rend2, text=2))
        dl_scroll = Gtk.ScrolledWindow(); dl_scroll.add(dl_tree)
        dl_box.pack_start(dl_scroll, True, True, 0)
        lbl_d = Gtk.Label(label="Downloads"); lbl_d.get_style_context().add_class("tab-label-side")
        notebook.append_page(dl_box, lbl_d)
        
        box.pack_start(notebook, True, True, 0)
        return box

    def on_history_activated(self, treeview, path, column):
        url = self.history_store[path][1]
        self.url_bar.set_text(url)
        self.on_url_activate(self.url_bar)

    def on_download_started(self, context, download):
        req = download.get_request()
        filename = req.get_uri().split("/")[-1]
        if not filename: filename = "downloaded_file"
        
        dest_path = os.path.join(os.path.expanduser("~"), "Downloads", filename)
        download.set_destination("file://" + dest_path)
        
        iter_ref = self.downloads_store.append([filename, "Downloading...", "0%"])
        
        def on_received_data(dl, length, i=iter_ref):
            prog = int(dl.get_estimated_progress() * 100)
            self.downloads_store[i][2] = f"{prog}%"
            
        def on_finished(dl, i=iter_ref):
            self.downloads_store[i][1] = "Finished"
            self.downloads_store[i][2] = "100%"
            
        def on_failed(dl, error, i=iter_ref):
            self.downloads_store[i][1] = "Failed"
            
        download.connect("received-data", on_received_data)
        download.connect("finished", on_finished)
        download.connect("failed", on_failed)

    # ================= BOTTOM PANELS =================
    def build_terminal_emulator(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.get_style_context().add_class("tool-box")
        lbl = Gtk.Label(label="PYTHON TERMINAL"); lbl.get_style_context().add_class("tool-title")
        box.pack_start(lbl, False, False, 10)
        self.term_output = Gtk.TextView(); self.term_output.get_style_context().add_class("term-text")
        scroll = Gtk.ScrolledWindow(); scroll.add(self.term_output)
        box.pack_start(scroll, True, True, 5)
        entry = Gtk.Entry(); entry.get_style_context().add_class("term-entry"); entry.connect("activate", self.on_term_execute)
        box.pack_start(entry, False, False, 0)
        return box

    def build_headers_panel(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); box.get_style_context().add_class("tool-box")
        lbl = Gtk.Label(label="HTTP HEADERS INJECTOR"); lbl.get_style_context().add_class("tool-title"); box.pack_start(lbl, False, False, 10)
        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.h_key = Gtk.Entry(); self.h_key.set_placeholder_text("Key"); self.h_key.get_style_context().add_class("term-entry")
        self.h_val = Gtk.Entry(); self.h_val.set_placeholder_text("Value"); self.h_val.get_style_context().add_class("term-entry")
        btn_add = Gtk.Button(label="+ Inject"); btn_add.get_style_context().add_class("glass-btn-success"); btn_add.connect("clicked", self.on_add_header)
        controls.pack_start(self.h_key, True, True, 0); controls.pack_start(self.h_val, True, True, 0); controls.pack_start(btn_add, False, False, 0)
        box.pack_start(controls, False, False, 10)
        self.header_list = Gtk.ListBox(); self.header_list.get_style_context().add_class("glass-list")
        scroll = Gtk.ScrolledWindow(); scroll.add(self.header_list); box.pack_start(scroll, True, True, 0)
        return box

    def build_css_panel(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); box.get_style_context().add_class("tool-box")
        lbl = Gtk.Label(label="LIVE CSS INJECTOR"); lbl.get_style_context().add_class("tool-title"); box.pack_start(lbl, False, False, 10)
        self.css_text = Gtk.TextView(); self.css_text.get_style_context().add_class("term-text")
        scroll = Gtk.ScrolledWindow(); scroll.add(self.css_text); box.pack_start(scroll, True, True, 5)
        btn_inject = Gtk.Button(label="[💉 INJECT CSS TO CURRENT TAB]"); btn_inject.get_style_context().add_class("glass-btn-success"); btn_inject.connect("clicked", self.on_inject_css)
        box.pack_start(btn_inject, False, False, 10)
        return box

    def build_source_viewer(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); box.get_style_context().add_class("tool-box")
        lbl = Gtk.Label(label="PAGE SOURCE VIEWER"); lbl.get_style_context().add_class("tool-title"); box.pack_start(lbl, False, False, 10)
        self.source_text = Gtk.TextView(); self.source_text.get_style_context().add_class("term-text")
        scroll = Gtk.ScrolledWindow(); scroll.add(self.source_text); box.pack_start(scroll, True, True, 5)
        btn_refresh = Gtk.Button(label="[⟳ Fetch Latest DOM Source]"); btn_refresh.get_style_context().add_class("glass-btn-success"); btn_refresh.connect("clicked", self.on_fetch_source)
        box.pack_start(btn_refresh, False, False, 10)
        return box

    def build_cookie_explorer(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); box.get_style_context().add_class("tool-box")
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        lbl = Gtk.Label(label="SITE COOKIES"); lbl.get_style_context().add_class("tool-title")
        btn = Gtk.Button(label="Refresh"); btn.get_style_context().add_class("glass-btn"); btn.connect("clicked", self.refresh_cookies)
        hdr.pack_start(lbl, False, False, 10); hdr.pack_end(btn, False, False, 10); box.pack_start(hdr, False, False, 10)
        self.cookie_list = Gtk.ListBox(); self.cookie_list.get_style_context().add_class("glass-list")
        scroll = Gtk.ScrolledWindow(); scroll.add(self.cookie_list); box.pack_start(scroll, True, True, 0)
        return box

    def build_storage_explorer(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); box.get_style_context().add_class("tool-box")
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        lbl = Gtk.Label(label="LOCAL STORAGE"); lbl.get_style_context().add_class("tool-title")
        btn = Gtk.Button(label="Refresh"); btn.get_style_context().add_class("glass-btn"); btn.connect("clicked", self.refresh_storage)
        hdr.pack_start(lbl, False, False, 10); hdr.pack_end(btn, False, False, 10); box.pack_start(hdr, False, False, 10)
        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.ls_key = Gtk.Entry(); self.ls_key.get_style_context().add_class("term-entry")
        self.ls_val = Gtk.Entry(); self.ls_val.get_style_context().add_class("term-entry")
        btn_add = Gtk.Button(label="+ Set Item"); btn_add.get_style_context().add_class("glass-btn-success"); btn_add.connect("clicked", self.on_add_storage)
        controls.pack_start(self.ls_key, True, True, 0); controls.pack_start(self.ls_val, True, True, 0); controls.pack_start(btn_add, False, False, 0)
        box.pack_start(controls, False, False, 10)
        self.storage_list = Gtk.ListBox(); self.storage_list.get_style_context().add_class("glass-list")
        scroll = Gtk.ScrolledWindow(); scroll.add(self.storage_list); box.pack_start(scroll, True, True, 0)
        return box

    def build_network_panel(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); box.get_style_context().add_class("tool-box")
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        lbl = Gtk.Label(label="NETWORK LOGGER"); lbl.get_style_context().add_class("tool-title")
        btn = Gtk.Button(label="Clear Logs"); btn.get_style_context().add_class("glass-btn-danger"); btn.connect("clicked", self.on_clear_network)
        hdr.pack_start(lbl, False, False, 10); hdr.pack_end(btn, False, False, 10); box.pack_start(hdr, False, False, 10)
        self.network_list = Gtk.ListBox(); self.network_list.get_style_context().add_class("glass-list")
        scroll = Gtk.ScrolledWindow(); scroll.add(self.network_list); box.pack_start(scroll, True, True, 0)
        return box

    def build_js_console(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); box.get_style_context().add_class("tool-box")
        lbl = Gtk.Label(label="JS CONSOLE"); lbl.get_style_context().add_class("tool-title"); box.pack_start(lbl, False, False, 10)
        self.js_output = Gtk.TextView(); self.js_output.get_style_context().add_class("term-text"); self.js_output.set_editable(False)
        self.js_output.get_buffer().set_text("> ")
        scroll = Gtk.ScrolledWindow(); scroll.add(self.js_output); box.pack_start(scroll, True, True, 5)
        entry = Gtk.Entry(); entry.get_style_context().add_class("term-entry"); entry.connect("activate", self.on_js_execute)
        box.pack_start(entry, False, False, 0)
        return box

    # --- ACTION HANDLERS ---
    def on_js_execute(self, entry):
        if not hasattr(self, 'current_webview'): return
        js_cmd = entry.get_text()
        buf = self.js_output.get_buffer(); buf.insert(buf.get_end_iter(), js_cmd + "\n"); entry.set_text("")
        def on_js_finish(w, r, u):
            try:
                val = w.run_javascript_finish(r).get_js_value()
                out = val.to_string() if val.is_string() else str(val.to_double()) if val.is_number() else str(val.to_boolean()) if val.is_boolean() else "null" if val.is_null() else "undefined" if val.is_undefined() else "[Object]"
                buf.insert(buf.get_end_iter(), "<- " + out + "\n> ")
            except Exception as e: buf.insert(buf.get_end_iter(), f"Error: {e}\n> ")
        self.current_webview.run_javascript(js_cmd, None, on_js_finish, None)

    def on_tech_detect(self, btn):
        if not hasattr(self, 'current_webview'): return
        js = "var t=[]; if(window.React) t.push('React'); if(window.Vue) t.push('Vue'); if(window.jQuery) t.push('jQuery'); return t.join(',');"
        def on_js_finish(w, r, u):
            try:
                res = w.run_javascript_finish(r).get_js_value().to_string()
                d = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Tech Stack:")
                d.format_secondary_text(res or "None"); d.run(); d.destroy()
            except: pass
        self.current_webview.run_javascript(js, None, on_js_finish, None)

    def on_webrtc_toggled(self, btn):
        if not hasattr(self, 'current_webview'): return
        settings = self.current_webview.get_settings()
        if btn.get_active():
            btn.set_label("WebRTC: Blocked"); btn.get_style_context().remove_class("glass-btn-danger"); btn.get_style_context().add_class("glass-btn-success")
            settings.set_enable_webrtc(False)
        else:
            btn.set_label("WebRTC: Leak"); btn.get_style_context().remove_class("glass-btn-success"); btn.get_style_context().add_class("glass-btn-danger")
            settings.set_enable_webrtc(True)
        self.current_webview.set_settings(settings)

    def on_cors_toggled(self, btn):
        if not hasattr(self, 'current_webview'): return
        settings = self.current_webview.get_settings()
        if btn.get_active():
            btn.set_label("CORS: Bypass"); btn.get_style_context().remove_class("glass-btn-danger"); btn.get_style_context().add_class("glass-btn-success")
            settings.set_enable_xss_auditor(False)
        else:
            btn.set_label("CORS: Strict"); btn.get_style_context().remove_class("glass-btn-success"); btn.get_style_context().add_class("glass-btn-danger")
            settings.set_enable_xss_auditor(True)
        self.current_webview.set_settings(settings)

    def on_clear_network(self, btn):
        for child in self.network_list.get_children(): self.network_list.remove(child)

    def on_resource_load(self, webview, resource, request):
        uri = request.get_uri()
        method = request.get_http_method() or "GET" if hasattr(request, 'get_http_method') else "GET"
        row = Gtk.ListBoxRow(); hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        lm = Gtk.Label(label=f"[{method}]"); lm.get_style_context().add_class("cookie-key")
        lu = Gtk.Label(label=uri); lu.get_style_context().add_class("cookie-val"); lu.set_halign(Gtk.Align.START)
        hbox.pack_start(lm, False, False, 0); hbox.pack_start(lu, True, True, 0); row.add(hbox)
        self.network_list.add(row); self.network_list.show_all()

    def refresh_cookies(self, btn=None):
        if not hasattr(self, 'current_webview'): return
        for child in self.cookie_list.get_children(): self.cookie_list.remove(child)
        def on_js_finish(w, r, u):
            try:
                for c in w.run_javascript_finish(r).get_js_value().to_string().split(";"):
                    if "=" not in c: continue
                    k, v = c.split("=", 1)
                    row = Gtk.ListBoxRow(); hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                    lk = Gtk.Label(label=k.strip()); lk.get_style_context().add_class("cookie-key"); lk.set_size_request(200, -1); lk.set_halign(Gtk.Align.START)
                    lv = Gtk.Label(label=v.strip()); lv.get_style_context().add_class("cookie-val"); lv.set_halign(Gtk.Align.START)
                    hbox.pack_start(lk, False, False, 0); hbox.pack_start(lv, True, True, 0); row.add(hbox)
                    self.cookie_list.add(row)
                self.cookie_list.show_all()
            except: pass
        self.current_webview.run_javascript("document.cookie", None, on_js_finish, None)

    def refresh_storage(self, btn=None):
        if not hasattr(self, 'current_webview'): return
        for child in self.storage_list.get_children(): self.storage_list.remove(child)
        def on_js_finish(w, r, u):
            try:
                for k, v in json.loads(w.run_javascript_finish(r).get_js_value().to_string()).items():
                    row = Gtk.ListBoxRow(); hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                    lk = Gtk.Label(label=k); lk.get_style_context().add_class("cookie-key"); lk.set_size_request(200, -1); lk.set_halign(Gtk.Align.START)
                    lv = Gtk.Label(label=str(v)); lv.get_style_context().add_class("cookie-val"); lv.set_halign(Gtk.Align.START)
                    hbox.pack_start(lk, False, False, 0); hbox.pack_start(lv, True, True, 0); row.add(hbox)
                    self.storage_list.add(row)
                self.storage_list.show_all()
            except: pass
        self.current_webview.run_javascript("JSON.stringify(localStorage);", None, on_js_finish, None)

    def on_add_storage(self, btn):
        k, v = self.ls_key.get_text().strip(), self.ls_val.get_text().strip()
        if k and v:
            self.current_webview.run_javascript(f"localStorage.setItem('{k}', '{v}');", None, None, None)
            self.ls_key.set_text(""); self.ls_val.set_text(""); self.refresh_storage()

    def on_fetch_source(self, btn):
        if not hasattr(self, 'current_webview'): return
        def on_js_finish(w, r, u):
            try: self.source_text.get_buffer().set_text(w.run_javascript_finish(r).get_js_value().to_string())
            except: pass
        self.current_webview.run_javascript("document.documentElement.outerHTML", None, on_js_finish, None)

    def on_inject_css(self, btn):
        buf = self.css_text.get_buffer()
        css = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True).replace("`", "\\`")
        self.current_webview.run_javascript(f"var s = document.createElement('style'); s.innerHTML = `{css}`; document.head.appendChild(s);", None, None, None)

    def on_add_header(self, btn):
        k, v = self.h_key.get_text().strip(), self.h_val.get_text().strip()
        if k and v:
            self.custom_headers.append((k, v))
            row = Gtk.ListBoxRow(); hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            lk = Gtk.Label(label=k); lk.get_style_context().add_class("cookie-key"); lk.set_size_request(200, -1); lk.set_halign(Gtk.Align.START)
            lv = Gtk.Label(label=v); lv.get_style_context().add_class("cookie-val"); lv.set_halign(Gtk.Align.START)
            hbox.pack_start(lk, False, False, 0); hbox.pack_start(lv, True, True, 0); row.add(hbox)
            self.header_list.add(row); self.header_list.show_all()
            self.h_key.set_text(""); self.h_val.set_text("")

    def on_term_execute(self, entry):
        cmd = entry.get_text()
        buf = self.term_output.get_buffer(); buf.insert(buf.get_end_iter(), cmd + "\n")
        try: buf.insert(buf.get_end_iter(), str(eval(cmd)) + "\n>>> ")
        except Exception as e:
            try: exec(cmd); buf.insert(buf.get_end_iter(), "Executed.\n>>> ")
            except Exception as ex: buf.insert(buf.get_end_iter(), f"Error: {ex}\n>>> ")
        entry.set_text("")

    def on_payload_activated(self, listbox, row):
        vbox = row.get_child()
        self.url_bar.set_text(self.url_bar.get_text() + vbox.get_children()[1].get_text())
        self.url_bar.grab_focus()

    def new_tab(self, url):
        webview = WebKit2.WebView.new_with_context(self.web_ctx)
        webview.connect("resource-load-started", self.on_resource_load)
        
        settings = webview.get_settings()
        settings.set_enable_developer_extras(True)
        webview.set_settings(settings)
        
        webview.load_uri(url)
        scrolled = Gtk.ScrolledWindow(); scrolled.add(webview)
        
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        label = Gtk.Label(label="New Tab")
        label.get_style_context().add_class("tab-label-bold")
        btn_close = Gtk.Button(label="×")
        btn_close.get_style_context().add_class("close-btn")
        btn_close.connect("clicked", lambda b: self.notebook.remove_page(self.notebook.page_num(scrolled)))
        hbox.pack_start(label, True, True, 0)
        hbox.pack_end(btn_close, False, False, 0)
        hbox.show_all()
        
        self.notebook.append_page(scrolled, hbox)
        self.notebook.show_all()
        
        def on_uri(w, p):
            uri = w.get_uri() or ""
            self.url_bar.set_text(uri)
            # Log to history
            time_str = datetime.now().strftime("%H:%M:%S")
            self.history_store.append([time_str, uri])
            
        webview.connect("notify::uri", on_uri)
        webview.connect("notify::title", lambda w, p: label.set_text(w.get_title() or "Untitled"))
        self.current_webview = webview

    def on_url_activate(self, entry):
        url = entry.get_text()
        if not url.startswith("http"): url = "https://" + url
        if hasattr(self, 'current_webview'): self.current_webview.load_uri(url)

    def on_proxy_toggled(self, btn):
        if btn.get_active():
            btn.set_label("🛡️ Proxy: TOR"); btn.get_style_context().remove_class("glass-btn-danger"); btn.get_style_context().add_class("glass-btn-success")
        else:
            btn.set_label("🛡️ Proxy"); btn.get_style_context().remove_class("glass-btn-success"); btn.get_style_context().add_class("glass-btn-danger")

    def _hide_all_stacks(self):
        for key, b in self.dev_buttons.items(): b.set_active(False)
        self.bottom_stack.hide()

    def _toggle_panel(self, btn, name):
        if btn.get_active():
            self._hide_all_stacks(); btn.set_active(True); self.bottom_stack.show(); self.bottom_stack.set_visible_child_name(name)
        else: self.bottom_stack.hide()

    def on_inspect_toggled(self, btn):
        if not hasattr(self, 'current_webview'): return
        inspector = self.current_webview.get_inspector()
        if btn.get_active():
            self._hide_all_stacks(); btn.set_active(True); inspector.show(); self.bottom_stack.show(); self.bottom_stack.set_visible_child_name("inspector")
        else: inspector.close(); self.bottom_stack.hide()
            
    def on_cookies_toggled(self, btn): self._toggle_panel(btn, "cookies"); self.refresh_cookies() if btn.get_active() else None
    def on_storage_toggled(self, btn): self._toggle_panel(btn, "storage"); self.refresh_storage() if btn.get_active() else None
    def on_headers_toggled(self, btn): self._toggle_panel(btn, "headers")
    def on_css_toggled(self, btn): self._toggle_panel(btn, "css")
    def on_source_toggled(self, btn): self._toggle_panel(btn, "source")
    def on_network_toggled(self, btn): self._toggle_panel(btn, "network")
    def on_js_toggled(self, btn): self._toggle_panel(btn, "js_console")
    
    def on_terminal_toggled(self, btn):
        if self.bottom_stack.get_visible_child_name() == "terminal" and self.bottom_stack.is_visible(): self.bottom_stack.hide()
        else: self._hide_all_stacks(); self.bottom_stack.show(); self.bottom_stack.set_visible_child_name("terminal")

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
        if uas[idx]: settings.set_user_agent(uas[idx])
        else: settings.set_user_agent(WebKit2.Settings().get_user_agent())
        self.current_webview.set_settings(settings)
        self.current_webview.reload()

    def setup_css(self):
        css = b'''
            window { background-color: transparent; }
            .hidden-header { background: rgba(10, 12, 18, 0.95); min-height: 0px; padding: 0px; border: none; box-shadow: none; }
            .glass-container { 
                background: linear-gradient(135deg, rgba(15, 20, 25, 0.95), rgba(5, 8, 12, 0.98)); 
                border: 1px solid rgba(255, 255, 255, 0.15); 
                border-radius: 16px; 
                box-shadow: 0 25px 60px rgba(0,0,0,0.9); 
            }
            .glass-toolbar { 
                background: rgba(0, 0, 0, 0.5); 
                padding: 10px 15px; 
                border-bottom: 1px solid rgba(255, 255, 255, 0.08); 
            }
            .glass-btn { 
                background: linear-gradient(to bottom, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.02));
                color: #00FFCC; 
                border: 1px solid rgba(0, 255, 204, 0.3); 
                border-radius: 20px; 
                padding: 6px 14px; 
                font-family: monospace; 
                font-weight: bold; 
                transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); 
            }
            .glass-btn:hover { 
                background: linear-gradient(to bottom, rgba(0, 255, 204, 0.2), rgba(0, 255, 204, 0.05));
                border: 1px solid rgba(0, 255, 204, 0.8); 
                box-shadow: 0 0 15px rgba(0, 255, 204, 0.4); 
            }
            .glass-btn:checked { 
                background: rgba(0, 255, 204, 0.4); 
                border: 1px solid #00FFCC; 
                box-shadow: 0 0 20px rgba(0, 255, 204, 0.6); 
                color: #FFFFFF; 
            }
            .glass-btn-danger { 
                background: linear-gradient(to bottom, rgba(255, 0, 0, 0.15), rgba(255, 0, 0, 0.05));
                color: #FF4444; 
                border: 1px solid rgba(255, 0, 0, 0.4); 
                border-radius: 20px; 
                padding: 6px 14px; 
                font-family: monospace; 
                font-weight: bold; 
            }
            .glass-btn-danger:hover {
                background: rgba(255, 0, 0, 0.25);
                box-shadow: 0 0 15px rgba(255, 0, 0, 0.4);
            }
            .glass-btn-danger:checked { background: rgba(255, 0, 0, 0.4); color: white; border-color: red;}
            .glass-btn-success { 
                background: linear-gradient(to bottom, rgba(0, 255, 0, 0.15), rgba(0, 255, 0, 0.05));
                color: #44FF44; 
                border: 1px solid rgba(0, 255, 0, 0.4); 
                border-radius: 20px; 
                padding: 6px 14px; 
                font-family: monospace; 
                font-weight: bold; 
            }
            .glass-btn-success:checked { background: rgba(0, 255, 0, 0.4); color: white; border-color: lime;}
            .glass-url { 
                background: rgba(0, 0, 0, 0.6); 
                color: #FFFFFF; 
                border: 1px solid rgba(255, 255, 255, 0.2); 
                border-radius: 20px; 
                padding: 8px 18px; 
                font-family: monospace; 
                font-size: 14px; 
                box-shadow: inset 0 2px 5px rgba(0,0,0,0.5);
            }
            .glass-url:focus { border: 1px solid #00FFCC; box-shadow: 0 0 12px rgba(0, 255, 204, 0.3), inset 0 2px 5px rgba(0,0,0,0.5); }
            .glass-combo { background: rgba(255, 255, 255, 0.08); color: #00FFCC; border-radius: 20px; font-family: monospace; padding: 4px; border: 1px solid rgba(0,255,204,0.3);}
            
            /* Tabs Styling */
            notebook header { background: rgba(5, 8, 12, 0.8); border-bottom: 1px solid rgba(0,255,204,0.2); }
            notebook header tab { background: rgba(255,255,255,0.02); border: 1px solid transparent; border-radius: 12px 12px 0 0; padding: 5px; margin: 2px 4px; }
            notebook header tab:checked { background: rgba(0,255,204,0.1); border: 1px solid rgba(0,255,204,0.4); border-bottom: none; box-shadow: 0 -2px 10px rgba(0,255,204,0.15); }
            .tab-label-bold { color: #E0E0E0; font-family: sans-serif; font-weight: bold; font-size: 13px; margin-right: 10px; }
            .close-btn { background: transparent; color: #FF4444; border: none; border-radius: 50%; padding: 2px 6px; font-weight: bold; }
            .close-btn:hover { background: rgba(255,0,0,0.2); }
            
            /* Sidebar & Panels */
            .tool-box { background: rgba(0, 0, 0, 0.95); border-top: 1px solid rgba(0, 255, 204, 0.4); box-shadow: inset 0 5px 15px rgba(0,0,0,0.8);}
            .tool-title { color: #00FFCC; font-family: monospace; font-weight: bold; letter-spacing: 2px; font-size: 14px; text-shadow: 0 0 5px rgba(0,255,204,0.5); }
            .sidebar-box { background: rgba(5, 8, 12, 0.98); border-right: 1px solid rgba(0, 255, 204, 0.3); }
            .sidebar-title { color: #FF0055; font-family: monospace; font-weight: bold; letter-spacing: 2px; font-size: 16px; text-shadow: 0 0 8px #FF0055; }
            .payload-title { color: #00FFCC; font-family: sans-serif; font-weight: bold; font-size: 13px; margin-bottom: 2px;}
            .payload-text { color: #8090A0; font-family: monospace; font-size: 11px; }
            .term-text { background: transparent; color: #00FFCC; font-family: monospace; font-size: 14px; padding: 12px; }
            .term-entry { background: rgba(0, 255, 204, 0.05); color: #FFFFFF; font-family: monospace; font-size: 14px; border: 1px solid rgba(0,255,204,0.2); border-radius: 8px; padding: 10px; margin: 5px; }
            .term-entry:focus { border: 1px solid #00FFCC; box-shadow: 0 0 8px rgba(0,255,204,0.4); }
            
            /* Tree & Lists */
            .glass-list { background: transparent; }
            .cookie-key { color: #FFFFFF; font-family: monospace; font-weight: bold; font-size: 13px;}
            .cookie-val { color: #8090A0; font-family: monospace; font-size: 13px;}
            .glass-tree { background: transparent; color: #00FFCC; font-family: monospace; }
            treeview header button { background: rgba(255,255,255,0.05); color: #FFF; border: none; padding: 5px;}
            
            /* Side tabs */
            .glass-tabs-sidebar header { background: transparent; border-right: 1px solid rgba(0,255,204,0.2); }
            .glass-tabs-sidebar tab { padding: 10px; border-radius: 0 8px 8px 0; border: none; }
            .glass-tabs-sidebar tab:checked { background: rgba(0,255,204,0.15); border-left: 3px solid #00FFCC; }
            .tab-label-side { color: #00FFCC; font-weight: bold; font-family: sans-serif; }
        '''
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

if __name__ == "__main__":
    win = ZeroDevBrowser()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
