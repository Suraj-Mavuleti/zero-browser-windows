import sys
import gi
import os
import json
import urllib.parse
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
from gi.repository import Gtk, Gdk, WebKit2, GLib, Gio

CONFIG_DIR = os.path.expanduser("~/.config/zero-browser")
BOOKMARKS_FILE = os.path.join(CONFIG_DIR, "bookmarks.json")
FILTER_DIR = os.path.join(CONFIG_DIR, "filters")

NEW_TAB_HTML = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { margin: 0; padding: 0; background: radial-gradient(circle at center, #1a2130, #050608); color: #FFFFFF; font-family: 'Segoe UI', -apple-system, sans-serif; height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center; }
        .clock { font-size: 8rem; font-weight: 200; letter-spacing: -2px; text-shadow: 0 10px 30px rgba(0, 229, 255, 0.4); margin-bottom: 20px; color: #00E5FF; }
        .greeting { font-size: 2rem; font-weight: 400; color: #8B94A5; margin-bottom: 60px; }
        .search-box { width: 600px; background: rgba(16, 20, 30, 0.6); border: 1px solid rgba(0, 229, 255, 0.2); border-radius: 30px; padding: 15px 30px; font-size: 1.2rem; color: #FFFFFF; box-shadow: 0 10px 40px rgba(0,0,0,0.5); outline: none; transition: all 0.3s ease; }
        .search-box:focus { border: 1px solid #00E5FF; box-shadow: 0 0 20px rgba(0, 229, 255, 0.4); background: rgba(20, 25, 40, 0.8); }
        .search-box::placeholder { color: #4A5568; }
        .bookmarks-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-top: 60px; }
        .bookmark-card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 16px; text-align: center; cursor: pointer; transition: all 0.2s ease; text-decoration: none; color: #8B94A5; font-weight: bold; width: 120px; }
        .bookmark-card:hover { background: rgba(0, 229, 255, 0.1); border: 1px solid #00E5FF; color: #00E5FF; transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.3); }
    </style>
    <script>
        function updateTime() {
            const now = new Date();
            let h = now.getHours(), m = now.getMinutes();
            document.getElementById('clock').innerText = (h<10?'0'+h:h) + ':' + (m<10?'0'+m:m);
            document.getElementById('greeting').innerText = (h<12?'Good morning':h<18?'Good afternoon':'Good evening') + ', Studio.';
        }
        setInterval(updateTime, 1000);
        function handleSearch(e) {
            if (e.key === 'Enter') {
                const q = e.target.value;
                window.location.href = (q.includes('.') && !q.includes(' ')) ? 'https://' + q : 'https://google.com/search?q=' + encodeURIComponent(q);
            }
        }
    </script>
</head>
<body onload="updateTime()">
    <div class="clock" id="clock">00:00</div>
    <div class="greeting" id="greeting">Welcome.</div>
    <input type="text" class="search-box" placeholder="Search the web or enter a URL..." onkeypress="handleSearch(event)">
    <div class="bookmarks-grid">
        <a href="https://github.com" class="bookmark-card">GitHub</a>
        <a href="https://youtube.com" class="bookmark-card">YouTube</a>
        <a href="https://reddit.com" class="bookmark-card">Reddit</a>
        <a href="https://twitter.com" class="bookmark-card">X</a>
    </div>
</body>
</html>
"""

READER_MODE_JS = """
(function() {
    let el = document.querySelector('article') || document.querySelector('main') || document.querySelector('.content') || document.body;
    let content = el.innerHTML;
    let title = document.title;
    document.head.innerHTML = `
        <style>
            body { background-color: #0d1117; color: #c9d1d9; font-family: 'Georgia', serif; font-size: 21px; line-height: 1.8; max-width: 800px; margin: 0 auto; padding: 60px 20px; }
            h1 { font-family: -apple-system, sans-serif; font-size: 42px; margin-bottom: 40px; color: #00E5FF; text-align: center; }
            h2, h3 { color: #8B94A5; font-family: -apple-system, sans-serif; margin-top: 40px; }
            img { max-width: 100%; border-radius: 12px; margin: 20px 0; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
            a { color: #00E5FF; text-decoration: none; }
            a:hover { text-decoration: underline; }
            p { margin-bottom: 25px; }
            pre, code { background: #161b22; padding: 10px; border-radius: 8px; font-family: monospace; overflow-x: auto; }
        </style>
    `;
    document.body.innerHTML = `<h1>${title}</h1>` + content;
})();
"""

class ZeroBrowser(Gtk.Window):
    def __init__(self):
        super().__init__(title="Zero Browser - Ultimate Studio")
        self.set_default_size(1400, 900)
        
        os.makedirs(CONFIG_DIR, exist_ok=True)
        self.bookmarks = self.load_bookmarks()
        
        self.header = Gtk.HeaderBar()
        self.header.set_show_close_button(True)
        self.header.props.title = ""
        self.header.get_style_context().add_class("hidden-header")
        self.set_titlebar(self.header)
        
        self.context = WebKit2.WebContext.new_ephemeral()
        self.context.set_tls_errors_policy(WebKit2.TLSErrorsPolicy.FAIL)
        self.context.get_cookie_manager().set_accept_policy(WebKit2.CookieAcceptPolicy.NO_THIRD_PARTY)
        self.context.set_sandbox_enabled(True)
        self.context.connect("download-started", self.on_download_started)
        
        self.setup_adblocker()
        self.setup_css()
        self.setup_shortcuts()
        
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.add(main_box)
        
        # ================= SIDEBAR =================
        self.sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.sidebar.set_size_request(300, -1)
        self.sidebar.get_style_context().add_class("sidebar")
        main_box.pack_start(self.sidebar, False, False, 0)
        
        logo_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        logo = Gtk.Label(label="Z E R O")
        logo.get_style_context().add_class("sidebar-logo")
        logo_box.pack_start(logo, True, True, 0)
        self.sidebar.pack_start(logo_box, False, False, 10)
        
        url_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        url_box.set_margin_start(15)
        url_box.set_margin_end(15)
        self.url_entry = Gtk.Entry()
        self.url_entry.set_placeholder_text("🔍 Search...")
        self.url_entry.get_style_context().add_class("url-entry")
        self.url_entry.connect("activate", self.on_url_entered)
        url_box.pack_start(self.url_entry, True, True, 0)
        
        self.btn_reader = Gtk.Button(label="📖")
        self.btn_reader.get_style_context().add_class("nav-btn")
        self.btn_reader.connect("clicked", self.activate_reader_mode)
        url_box.pack_start(self.btn_reader, False, False, 0)
        
        self.sidebar.pack_start(url_box, False, False, 10)
        
        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        nav_box.set_margin_start(15)
        nav_box.set_margin_end(15)
        self.btn_back = Gtk.Button(label="◀")
        self.btn_forward = Gtk.Button(label="▶")
        self.btn_reload = Gtk.Button(label="↻")
        self.btn_new = Gtk.Button(label="➕ Tab")
        
        self.btn_back.connect("clicked", self.on_back)
        self.btn_forward.connect("clicked", self.on_forward)
        self.btn_reload.connect("clicked", self.on_reload)
        self.btn_new.connect("clicked", lambda x: self.new_tab("zero://newtab"))
        
        for btn in [self.btn_back, self.btn_forward, self.btn_reload, self.btn_new]:
            btn.get_style_context().add_class("nav-btn")
            nav_box.pack_start(btn, True, True, 0)
        self.sidebar.pack_start(nav_box, False, False, 5)
        
        lbl_spaces = Gtk.Label(label="OPEN TABS")
        lbl_spaces.get_style_context().add_class("section-label")
        lbl_spaces.set_halign(Gtk.Align.START)
        lbl_spaces.set_margin_start(20)
        lbl_spaces.set_margin_top(15)
        self.sidebar.pack_start(lbl_spaces, False, False, 5)
        
        scroll_sidebar = Gtk.ScrolledWindow()
        scroll_sidebar.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.tabs_list = Gtk.ListBox()
        self.tabs_list.get_style_context().add_class("tabs-list")
        self.tabs_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.tabs_list.connect("row-selected", self.on_tab_selected)
        scroll_sidebar.add(self.tabs_list)
        self.sidebar.pack_start(scroll_sidebar, True, True, 0)
        
        tools_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        tools_box.set_margin_start(15)
        tools_box.set_margin_end(15)
        tools_box.set_margin_bottom(15)
        
        self.btn_star = Gtk.Button(label="⭐ Bookmark")
        self.btn_star.get_style_context().add_class("nav-btn")
        self.btn_star.connect("clicked", self.bookmark_current)
        
        self.btn_dev = Gtk.Button(label="💻 DevTools")
        self.btn_dev.get_style_context().add_class("nav-btn")
        self.btn_dev.connect("clicked", self.toggle_inspector)
        
        tools_box.pack_start(self.btn_star, True, True, 0)
        tools_box.pack_start(self.btn_dev, True, True, 0)
        self.sidebar.pack_end(tools_box, False, False, 0)
        
        # ================= WEBVIEW AREA =================
        self.webview_container = Gtk.Box()
        self.webview_container.get_style_context().add_class("webview-container")
        main_box.pack_start(self.webview_container, True, True, 0)
        
        self.overlay = Gtk.Overlay()
        self.webview_container.pack_start(self.overlay, True, True, 0)
        
        self.webview_box = Gtk.Box()
        self.webview_box.get_style_context().add_class("webview-box")
        self.overlay.add(self.webview_box)
        
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(250)
        self.webview_box.pack_start(self.stack, True, True, 0)
        
        self.toast_revealer = Gtk.Revealer()
        self.toast_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_UP)
        self.toast_revealer.set_halign(Gtk.Align.CENTER)
        self.toast_revealer.set_valign(Gtk.Align.END)
        self.toast_revealer.set_margin_bottom(30)
        
        self.toast_lbl = Gtk.Label()
        self.toast_lbl.get_style_context().add_class("toast")
        self.toast_revealer.add(self.toast_lbl)
        self.overlay.add_overlay(self.toast_revealer)
        
        self.tab_map = {}
        self.new_tab("zero://newtab")
        
    def setup_adblocker(self):
        os.makedirs(FILTER_DIR, exist_ok=True)
        rules = [
            {"trigger": {"url-filter": ".*(google-analytics|doubleclick|facebook.com/tr|metrics|tracking).*"}, "action": {"type": "block"}},
            {"trigger": {"url-filter": ".*(ads|adsystem|adserver|adtech|adsafeprotected).*"}, "action": {"type": "block"}},
            {"trigger": {"url-filter": ".*(pixel.gif|beacon.js|hotjar).*"}, "action": {"type": "block"}}
        ]
        json_path = os.path.join(FILTER_DIR, "privacy_shield.json")
        with open(json_path, "w") as f: json.dump(rules, f)
        self.filter_store = WebKit2.UserContentFilterStore.new(FILTER_DIR)
        
        def on_compile_finished(store, result):
            try:
                filter_obj = store.save_finish(result)
                self.content_manager = WebKit2.UserContentManager.new()
                self.content_manager.add_filter(filter_obj)
            except Exception: pass
            
        try:
            with open(json_path, "rb") as f: data = GLib.Bytes.new(f.read())
            self.filter_store.save("privacy_shield", data, None, on_compile_finished)
        except Exception: pass

    def show_toast(self, message):
        self.toast_lbl.set_text(message)
        self.toast_revealer.set_reveal_child(True)
        GLib.timeout_add_seconds(3, lambda: self.toast_revealer.set_reveal_child(False) or False)
        
    def setup_css(self):
        css = b'''
            window { background-color: #030305; }
            .hidden-header { background: #030305; min-height: 0px; padding: 0px; border: none; box-shadow: none; }
            .sidebar { background-color: #080A10; border-right: 1px solid #141722; }
            .sidebar-logo { color: #FFFFFF; font-size: 26px; font-weight: 900; letter-spacing: 4px; text-shadow: 0 0 10px rgba(0,229,255,0.4); }
            .url-entry { background: #10141E; color: #00E5FF; border: 1px solid #1C2333; border-radius: 12px; padding: 12px 15px; font-size: 14px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.5); caret-color: #00E5FF; }
            .url-entry:focus { border: 1px solid #00E5FF; background: #141926; box-shadow: 0 0 12px rgba(0,229,255,0.3); }
            .nav-btn { background: #10141E; border: 1px solid #1C2333; color: #8B94A5; border-radius: 10px; padding: 8px; font-weight: bold; font-size: 14px; transition: all 0.2s ease; }
            .nav-btn:hover { background: #181E2D; color: #00E5FF; border: 1px solid #00E5FF; box-shadow: 0 0 8px rgba(0,229,255,0.2); }
            .section-label { color: #4A5568; font-size: 11px; font-weight: 900; letter-spacing: 1px; }
            .tabs-list { background: transparent; }
            .tab-row { background: transparent; padding: 12px 15px; margin: 4px 15px; border-radius: 10px; color: #8B94A5; font-weight: bold; font-size: 13px; border: 1px solid transparent; }
            .tab-row:hover { background: #10141E; color: #FFFFFF; border: 1px solid #1C2333; }
            .tab-row:selected { background: rgba(0, 229, 255, 0.1); color: #00E5FF; border-left: 3px solid #00E5FF; border-top: 1px solid rgba(0,229,255,0.3); border-bottom: 1px solid rgba(0,229,255,0.3); border-right: 1px solid rgba(0,229,255,0.3); }
            .tab-close-btn { background: transparent; border: none; color: #4A5568; padding: 0px 5px; }
            .tab-close-btn:hover { color: #FF3366; }
            .webview-container { background-color: #030305; padding: 12px 12px 12px 0px; }
            .webview-box { background: #10141E; border-radius: 16px; border: 1px solid #1C2333; box-shadow: 0 10px 30px rgba(0,0,0,0.8); overflow: hidden; }
            .toast { background: rgba(0, 229, 255, 0.9); color: #000000; font-weight: bold; padding: 10px 20px; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,229,255,0.5); }
        '''
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
    def setup_shortcuts(self):
        accel = Gtk.AccelGroup()
        self.add_accel_group(accel)
        key, mod = Gtk.accelerator_parse("<Primary>t")
        accel.connect(key, mod, Gtk.AccelFlags.VISIBLE, lambda *a: self.new_tab("zero://newtab"))
        key, mod = Gtk.accelerator_parse("<Primary>w")
        accel.connect(key, mod, Gtk.AccelFlags.VISIBLE, lambda *a: self.close_current_tab(None))
        key, mod = Gtk.accelerator_parse("<Primary>l")
        accel.connect(key, mod, Gtk.AccelFlags.VISIBLE, lambda *a: self.url_entry.grab_focus())
        key, mod = Gtk.accelerator_parse("<Primary>r")
        accel.connect(key, mod, Gtk.AccelFlags.VISIBLE, lambda *a: self.activate_reader_mode(None))

    def load_bookmarks(self):
        try:
            if os.path.exists(BOOKMARKS_FILE):
                with open(BOOKMARKS_FILE, "r") as f: return json.load(f)
        except Exception: pass
        return {}
        
    def save_bookmarks(self):
        os.makedirs(os.path.dirname(BOOKMARKS_FILE), exist_ok=True)
        with open(BOOKMARKS_FILE, "w") as f: json.dump(self.bookmarks, f)
            
    def bookmark_current(self, widget):
        wv = self.current_webview()
        if wv and wv.get_uri() and not wv.get_uri().startswith("zero://"):
            url = wv.get_uri()
            title = wv.get_title() or url
            self.bookmarks[url] = title
            self.save_bookmarks()
            self.show_toast("⭐ Bookmark Saved!")

    def on_download_started(self, context, download):
        self.show_toast(f"📥 Downloading: {download.get_request().get_uri().split('/')[-1]}")
        downloads_dir = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD)
        filename = download.get_request().get_uri().split('/')[-1] or "download"
        dest = os.path.join(downloads_dir, filename)
        download.set_destination("file://" + dest)
        download.connect("finished", lambda d: self.show_toast("✅ Download Complete!"))
        
    def new_tab(self, url):
        if hasattr(self, 'content_manager'):
            webview = WebKit2.WebView.new_with_context_and_user_content_manager(self.context, self.content_manager)
        else:
            webview = WebKit2.WebView.new_with_context(self.context)
            
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
        
        stack_id = str(id(webview))
        self.stack.add_named(scrolled, stack_id)
        
        row = Gtk.ListBoxRow()
        row.get_style_context().add_class("tab-row")
        
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        lbl = Gtk.Label(label="New Tab")
        lbl.set_halign(Gtk.Align.START)
        lbl.set_ellipsize(3)
        
        close_btn = Gtk.Button(label="✕")
        close_btn.get_style_context().add_class("tab-close-btn")
        close_btn.connect("clicked", lambda b: self.close_tab(webview, row))
        
        box.pack_start(lbl, True, True, 0)
        box.pack_end(close_btn, False, False, 0)
        row.add(box)
        row.show_all()
        
        row.stack_id = stack_id
        row.lbl = lbl
        self.tab_map[webview] = row
        
        self.tabs_list.add(row)
        self.tabs_list.select_row(row)
        
        if url == "zero://newtab":
            webview.load_html(NEW_TAB_HTML, "zero://newtab")
        else:
            webview.load_uri(url)
        return True
        
    def close_tab(self, webview, row):
        scrolled = webview.get_parent()
        self.stack.remove(scrolled)
        self.tabs_list.remove(row)
        del self.tab_map[webview]
        
        if len(self.tab_map) == 0:
            self.new_tab("zero://newtab")
            
    def current_webview(self):
        row = self.tabs_list.get_selected_row()
        if not row: return None
        scrolled = self.stack.get_child_by_name(row.stack_id)
        return scrolled.get_child() if scrolled else None
        
    def close_current_tab(self, widget):
        wv = self.current_webview()
        if wv:
            row = self.tab_map.get(wv)
            if row: self.close_tab(wv, row)
        return True
        
    def on_tab_selected(self, listbox, row):
        if row:
            self.stack.set_visible_child_name(row.stack_id)
            wv = self.current_webview()
            if wv and wv.get_uri(): 
                uri = wv.get_uri()
                if uri == "zero://newtab": self.url_entry.set_text("")
                else: self.url_entry.set_text(uri)
                
    def on_url_entered(self, widget):
        url = self.url_entry.get_text()
        if url in self.bookmarks: pass
        elif not url.startswith("http://") and not url.startswith("https://"):
            if "." in url and " " not in url: url = "https://" + url
            else: url = "https://google.com/search?q=" + urllib.parse.quote_plus(url)
        wv = self.current_webview()
        if wv: wv.load_uri(url)
        
    def on_load_changed(self, webview, load_event):
        if webview == self.current_webview() and load_event == WebKit2.LoadEvent.COMMITTED:
            uri = webview.get_uri()
            if uri != "zero://newtab":
                self.url_entry.set_text(uri)
            else:
                self.url_entry.set_text("")
            
    def on_title_changed(self, webview, param):
        row = self.tab_map.get(webview)
        if row:
            title = webview.get_title()
            if webview.get_uri() == "zero://newtab":
                row.lbl.set_text("New Tab")
            elif title:
                row.lbl.set_text(title[:20] + "...")
            
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
            
    def activate_reader_mode(self, widget):
        wv = self.current_webview()
        if wv and wv.get_uri() != "zero://newtab":
            self.show_toast("📖 Activating Reader Mode...")
            wv.run_javascript(READER_MODE_JS, None, None, None)

if __name__ == "__main__":
    win = ZeroBrowser()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
