import os, base64, json, zlib, requests, copy

requests.packages.urllib3.disable_warnings()

CLIENT_PLATFORM = "ew0KCSJwbGF0Zm9ybVR5cGUiOiAiUEMiLA0KCSJwbGF0Zm9ybU9TIjogIldpbmRvd3MiLA0KCSJwbGF0Zm9ybU9TVmVyc2lvbiI6ICIxMC4wLjE5MDQyLjEuMjU2LjY0Yml0IiwNCgkicGxhdGZvcm1DaGlwc2V0IjogIlVua25vd24iDQp9"
CLIENT_VERSION  = "release-11.02-25-3708969"
PREFS_BASE      = "https://player-preferences-euc1.pp.sgp.pvp.net/playerPref/v3"
GET_URL         = f"{PREFS_BASE}/getPreference/Ares.PlayerSettings"
SAVE_URL        = f"{PREFS_BASE}/savePreference"


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def get_tokens():
    lockfile = os.path.join(os.getenv("LOCALAPPDATA"),
                            "Riot Games", "Riot Client", "Config", "lockfile")

    with open(lockfile, "r") as f:
        name, pid, port, password, protocol = f.read().split(":")

    auth = base64.b64encode(f"riot:{password}".encode()).decode()
    url = f"{protocol}://127.0.0.1:{port}/entitlements/v1/token"

    r = requests.get(url, headers={"Authorization": f"Basic {auth}"}, verify=False)
    data = r.json()
    return data["accessToken"], data["token"], data["subject"]


def build_headers(auth_token, ent_token):
    return {
        "Authorization": f"Bearer {auth_token}",
        "X-Riot-Entitlements-JWT": ent_token,
        "X-Riot-ClientPlatform": CLIENT_PLATFORM,
        "X-Riot-ClientVersion": CLIENT_VERSION,
        "Content-Type": "application/json",
    }


# ---------------------------------------------------------------------------
# Encode / Decode
# ---------------------------------------------------------------------------

def decode_settings_data(raw_b64):
    decoded = base64.b64decode(raw_b64)
    decompressed = zlib.decompress(decoded, -15)
    return json.loads(decompressed)


def encode_settings_data(settings_dict):
    raw_json = json.dumps(settings_dict, separators=(",", ":"))
    compressed = zlib.compress(raw_json.encode(), 9)
    stripped = compressed[2:-4]
    return base64.b64encode(stripped).decode()


# ---------------------------------------------------------------------------
# Fetch / Save
# ---------------------------------------------------------------------------

def fetch_settings(headers):
    r = requests.get(GET_URL, headers=headers, verify=False)
    r.raise_for_status()
    return r.json()


def save_settings(headers, raw_response, settings_dict):
    new_data = encode_settings_data(settings_dict)
    payload = {
        "type": raw_response["type"],
        "data": new_data,
        "modified": raw_response["modified"],
    }
    r = requests.put(SAVE_URL, headers=headers, json=payload, verify=False)
    r.raise_for_status()
    return r.status_code, r.text


# ---------------------------------------------------------------------------
# Crosshair helpers
# ---------------------------------------------------------------------------

def make_color(r, g, b, a=255):
    return {"r": r, "g": g, "b": b, "a": a}


def make_lines(thickness, length, offset, opacity, show,
               vert_length=None, allow_vert=False,
               movement_err=False, shooting_err=False, min_err=False,
               firing_scale=1, movement_scale=1):
    return {
        "lineThickness": thickness,
        "lineLength": length,
        "lineLengthVertical": vert_length if vert_length is not None else length,
        "bAllowVertScaling": allow_vert,
        "lineOffset": offset,
        "bShowMovementError": movement_err,
        "bShowShootingError": shooting_err,
        "bShowMinError": min_err,
        "opacity": opacity,
        "bShowLines": show,
        "firingErrorScale": firing_scale,
        "movementErrorScale": movement_scale,
    }

EMPTY_LINES = make_lines(0, 0, 0, 0, False)


def make_section(color, custom_color=None, use_custom=False,
                 outline=True, outline_thick=1, outline_opacity=0.5,
                 dot_size=0, dot_opacity=0, show_dot=False,
                 fade_firing=False, spectated=False, hide=False, fix_min=False,
                 inner=None, outer=None):
    return {
        "color": color,
        "colorCustom": custom_color or color,
        "bUseCustomColor": use_custom,
        "bHasOutline": outline,
        "outlineThickness": outline_thick,
        "outlineColor": make_color(0, 0, 0),
        "outlineOpacity": outline_opacity,
        "centerDotSize": dot_size,
        "centerDotOpacity": dot_opacity,
        "bDisplayCenterDot": show_dot,
        "bFadeCrosshairWithFiringError": fade_firing,
        "bShowSpectatedPlayerCrosshair": spectated,
        "bHideCrosshair": hide,
        "bFixMinErrorAcrossWeapons": fix_min,
        "innerLines": inner or copy.deepcopy(EMPTY_LINES),
        "outerLines": outer or copy.deepcopy(EMPTY_LINES),
    }

EMPTY_SECTION = make_section(make_color(255, 255, 255), outline=False, outline_opacity=0)

EMPTY_SNIPER = {
    "centerDotColor": make_color(255, 255, 255),
    "centerDotColorCustom": make_color(255, 255, 255),
    "bUseCustomCenterDotColor": False,
    "centerDotSize": 1,
    "centerDotOpacity": 1,
    "bDisplayCenterDot": True,
}


def make_profile(name, primary, ads=None, sniper=None, use_primary_for_ads=True, advanced=True):
    return {
        "primary": primary,
        "aDS": ads or copy.deepcopy(EMPTY_SECTION),
        "focusMode": copy.deepcopy(EMPTY_SECTION),
        "sniper": sniper or copy.deepcopy(EMPTY_SNIPER),
        "bUsePrimaryCrosshairForADS": use_primary_for_ads,
        "bUsePrimaryCrosshairForFocusMode": False,
        "bUseCustomCrosshairOnAllPrimary": False,
        "bUseAdvancedOptions": advanced,
        "bScaleToResolution": False,
        "profileName": name,
    }


# ---------------------------------------------------------------------------
# Preset crosshairs
# ---------------------------------------------------------------------------

PRESETS = {}

# 1) TenZ - small crosshair with cyan color
PRESETS["TenZ"] = make_profile(
    "TenZ",
    make_section(
        make_color(0, 255, 255),
        outline=True, outline_thick=1, outline_opacity=1,
        dot_size=0, show_dot=False,
        inner=make_lines(2, 3, 2, 1, True),
        outer=make_lines(0, 0, 0, 0, False),
    ),
)

# 2) Aspas - green dot + short lines
PRESETS["Aspas"] = make_profile(
    "Aspas",
    make_section(
        make_color(0, 255, 0),
        outline=True, outline_thick=1, outline_opacity=1,
        dot_size=2, dot_opacity=1, show_dot=True,
        inner=make_lines(2, 4, 3, 1, True),
        outer=make_lines(0, 0, 0, 0, False),
    ),
)

# 3) Dot Only (White) - pure dot, no lines
PRESETS["Dot Only (White)"] = make_profile(
    "Dot Only (White)",
    make_section(
        make_color(255, 255, 255),
        outline=True, outline_thick=1, outline_opacity=1,
        dot_size=2, dot_opacity=1, show_dot=True,
        inner=make_lines(0, 0, 0, 0, False),
        outer=make_lines(0, 0, 0, 0, False),
    ),
)

# 4) Classic Cross (Yellow) - traditional +
PRESETS["Classic Cross (Yellow)"] = make_profile(
    "Classic Cross (Yellow)",
    make_section(
        make_color(255, 255, 0),
        outline=True, outline_thick=1, outline_opacity=0.5,
        dot_size=0, show_dot=False,
        inner=make_lines(2, 6, 3, 1, True),
        outer=make_lines(2, 2, 10, 0.35, True, movement_err=True, shooting_err=True),
    ),
)

# 5) Small Cross (Cyan) - tight competitive crosshair
PRESETS["Small Cross (Cyan)"] = make_profile(
    "Small Cross (Cyan)",
    make_section(
        make_color(0, 255, 255),
        outline=True, outline_thick=1, outline_opacity=1,
        dot_size=1, dot_opacity=1, show_dot=True,
        inner=make_lines(2, 2, 2, 1, True),
        outer=make_lines(0, 0, 0, 0, False),
    ),
)

# 6) Crosshair with movement error (Red)
PRESETS["Dynamic (Red)"] = make_profile(
    "Dynamic (Red)",
    make_section(
        make_color(255, 70, 70),
        use_custom=True,
        custom_color=make_color(255, 70, 70),
        outline=True, outline_thick=1, outline_opacity=1,
        dot_size=2, dot_opacity=1, show_dot=True,
        fade_firing=True,
        inner=make_lines(2, 4, 3, 1, True, movement_err=True, shooting_err=True, min_err=True),
        outer=make_lines(2, 2, 8, 0.5, True, movement_err=True, shooting_err=True),
    ),
)


# ---------------------------------------------------------------------------
# Crosshair profile data manipulation
# ---------------------------------------------------------------------------

def get_crosshair_data(settings):
    for s in settings.get("stringSettings", []):
        if s["settingEnum"] == "EAresStringSettingName::SavedCrosshairProfileData":
            return json.loads(s["value"])
    return None


def set_crosshair_data(settings, crosshair_data):
    for s in settings.get("stringSettings", []):
        if s["settingEnum"] == "EAresStringSettingName::SavedCrosshairProfileData":
            s["value"] = json.dumps(crosshair_data, separators=(",", ":"))
            return
    settings.setdefault("stringSettings", []).append({
        "settingEnum": "EAresStringSettingName::SavedCrosshairProfileData",
        "value": json.dumps(crosshair_data, separators=(",", ":")),
    })


def add_profile(crosshair_data, profile, set_active=False):
    crosshair_data["profiles"].append(profile)
    idx = len(crosshair_data["profiles"]) - 1
    if set_active:
        crosshair_data["currentProfile"] = idx
    return idx


# ---------------------------------------------------------------------------
# Interactive menu
# ---------------------------------------------------------------------------

def print_profiles(crosshair_data):
    active = crosshair_data["currentProfile"]
    for i, p in enumerate(crosshair_data["profiles"]):
        marker = " <-- active" if i == active else ""
        print(f"  [{i}] {p.get('profileName', 'Unnamed')}{marker}")


def main():
    print("Reading lockfile...")
    auth_token, ent_token, subject = get_tokens()
    headers = build_headers(auth_token, ent_token)
    print(f"Authenticated as: {subject}\n")

    print("Fetching current settings...")
    raw_response = fetch_settings(headers)
    settings = decode_settings_data(raw_response["data"])
    crosshair_data = get_crosshair_data(settings)

    if not crosshair_data:
        print("No crosshair data found in settings.")
        return

    while True:
        print("\n========================================")
        print("  Valorant Crosshair Manager")
        print("========================================")
        print("  1) List current profiles")
        print("  2) Add a preset crosshair")
        print("  3) Set active profile")
        print("  4) Save & push to server")
        print("  5) Export decoded settings to file")
        print("  0) Exit")
        print("========================================")

        choice = input("Choice: ").strip()

        if choice == "1":
            print(f"\nProfiles ({len(crosshair_data['profiles'])} total):")
            print_profiles(crosshair_data)

        elif choice == "2":
            print("\nAvailable presets:")
            preset_names = list(PRESETS.keys())
            for i, name in enumerate(preset_names):
                print(f"  [{i}] {name}")
            sel = input("Select preset number (or 'all' to add all): ").strip()
            if sel.lower() == "all":
                for name in preset_names:
                    idx = add_profile(crosshair_data, copy.deepcopy(PRESETS[name]))
                    print(f"  Added '{name}' at index {idx}")
            else:
                try:
                    idx_sel = int(sel)
                    name = preset_names[idx_sel]
                    idx = add_profile(crosshair_data, copy.deepcopy(PRESETS[name]))
                    print(f"  Added '{name}' at index {idx}")
                except (ValueError, IndexError):
                    print("  Invalid selection.")

        elif choice == "3":
            print(f"\nCurrent active: {crosshair_data['currentProfile']}")
            print_profiles(crosshair_data)
            sel = input("Set active profile index: ").strip()
            try:
                idx_sel = int(sel)
                if 0 <= idx_sel < len(crosshair_data["profiles"]):
                    crosshair_data["currentProfile"] = idx_sel
                    name = crosshair_data["profiles"][idx_sel].get("profileName", "Unnamed")
                    print(f"  Active profile set to [{idx_sel}] {name}")
                else:
                    print("  Index out of range.")
            except ValueError:
                print("  Invalid number.")

        elif choice == "4":
            print("\nPushing settings to server...")
            set_crosshair_data(settings, crosshair_data)
            status, resp = save_settings(headers, raw_response, settings)
            print(f"  Response: {status}")
            print(f"  Body: {resp[:500]}")
            raw_response = fetch_settings(headers)
            settings = decode_settings_data(raw_response["data"])
            crosshair_data = get_crosshair_data(settings)
            print("  Settings saved and re-fetched successfully.")

        elif choice == "5":
            out = "decoded_settings.json"
            with open(out, "w") as f:
                json.dump(settings, f, indent=2)
            print(f"  Exported to {out}")

        elif choice == "0":
            print("Bye.")
            break

        else:
            print("  Invalid choice.")


if __name__ == "__main__":
    main()
