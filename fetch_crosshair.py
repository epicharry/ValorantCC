import os, base64, json, requests

requests.packages.urllib3.disable_warnings()

CLIENT_PLATFORM = "ew0KCSJwbGF0Zm9ybVR5cGUiOiAiUEMiLA0KCSJwbGF0Zm9ybU9TIjogIldpbmRvd3MiLA0KCSJwbGF0Zm9ybU9TVmVyc2lvbiI6ICIxMC4wLjE5MDQyLjEuMjU2LjY0Yml0IiwNCgkicGxhdGZvcm1DaGlwc2V0IjogIlVua25vd24iDQp9"
CLIENT_VERSION  = "release-11.02-25-3708969"
PREFS_URL       = "https://player-preferences-euc1.pp.sgp.pvp.net/playerPref/v3/getPreference/Ares.PlayerSettings"

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

def fetch_crosshair_settings(auth_token, ent_token):
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "X-Riot-Entitlements-JWT": ent_token,
        "X-Riot-ClientPlatform": CLIENT_PLATFORM,
        "X-Riot-ClientVersion": CLIENT_VERSION,
        "Content-Type": "application/json"
    }

    r = requests.get(PREFS_URL, headers=headers, verify=False)
    return r.status_code, r.text

if __name__ == "__main__":
    print("Reading lockfile...")
    auth_token, ent_token, subject = get_tokens()
    print(f"Authenticated as: {subject}")

    print(f"Fetching settings from: {PREFS_URL}")
    status, raw = fetch_crosshair_settings(auth_token, ent_token)
    print(f"Status: {status}")

    output_file = "crosshair_raw_response.json"
    with open(output_file, "w") as f:
        f.write(raw)

    print(f"Raw response saved to: {output_file}")
