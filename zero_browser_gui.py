import os
import sys
import subprocess
from pathlib import Path

def launch_gecko_browser():
    profile_dir = Path.home() / ".gemini/antigravity/scratch/zero_browser_profile"
    profile_dir.mkdir(parents=True, exist_ok=True)
    
    prefs = """
    user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);
    user_pref("browser.tabs.drawInTitlebar", true);
    user_pref("browser.startup.homepage", "about:blank");
    user_pref("browser.theme.content-theme", 0);
    user_pref("browser.theme.toolbar-theme", 0);
    user_pref("browser.uidensity", 1);
    """
    with open(profile_dir / "user.js", "w") as f:
        f.write(prefs)
        
    chrome_dir = profile_dir / "chrome"
    chrome_dir.mkdir(exist_ok=True)
    
    css = """
    /* GOD TIER ZERO OS GECKO THEME */
    :root {
        --toolbar-bgcolor: #0B0C10 !important;
        --toolbar-field-background-color: #161920 !important;
        --toolbar-field-color: #66FCF1 !important;
        --toolbar-field-focus-background-color: #0B0C10 !important;
        --toolbar-field-focus-color: #66FCF1 !important;
        --tab-selected-bgcolor: #1F2833 !important;
        --tab-selected-textcolor: #66FCF1 !important;
        --lwt-toolbar-field-border-color: transparent !important;
    }

    #nav-bar, #PersonalToolbar, #TabsToolbar {
        background-color: #0B0C10 !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* Style the URL Bar */
    #urlbar-background {
        background: #161920 !important;
        border: 1px solid #1F2833 !important;
        border-radius: 20px !important;
    }
    #urlbar[focused="true"] > #urlbar-background {
        border: 1px solid #66FCF1 !important;
        box-shadow: 0px 0px 10px rgba(102, 252, 241, 0.2) !important;
    }
    #urlbar-input {
        color: #66FCF1 !important;
        font-family: 'Segoe UI', monospace !important;
        font-size: 15px !important;
        text-align: center !important;
    }

    /* Floating Tab Design */
    .tabbrowser-tab {
        background-color: #0B0C10 !important;
        border-radius: 8px !important;
        margin: 4px !important;
    }
    .tabbrowser-tab[selected="true"] {
        background-color: #1F2833 !important;
        border: 1px solid #66FCF1 !important;
        box-shadow: 0px 0px 10px rgba(102, 252, 241, 0.4) !important;
    }
    .tabbrowser-tab::after, .tabbrowser-tab::before {
        display: none !important;
    }

    /* Clean UI Hacks */
    #tracking-protection-icon-container, #identity-box { display: none !important; }
    #PanelUI-button { display: none !important; }
    #alltabs-button { display: none !important; }
    
    .toolbarbutton-icon { fill: #66FCF1 !important; }
    window, dialog, page { background-color: #0B0C10 !important; }
    """
    with open(chrome_dir / "userChrome.css", "w") as f:
        f.write(css)

    # Launch Firedragon
    subprocess.Popen(["firedragon", "--profile", str(profile_dir), "--new-instance"])

if __name__ == "__main__":
    launch_gecko_browser()
