import os
import time
import requests
from pypresence import Presence
import configparser

# Clear the console at the start of the script
os.system('cls' if os.name == 'nt' else 'clear')

# Read configuration from conf file
config = configparser.ConfigParser()
config.read('config.conf')

# Ensure the required configuration is present
try:
    DISCORD_CLIENT_ID = config['Discord']['ClientID']
    if not DISCORD_CLIENT_ID:
        raise ValueError("Discord Client ID is missing in config.conf")

    JELLYFIN_SERVER_URL = config['Jellyfin']['ServerURL']
    JELLYFIN_API_TOKEN = config['Jellyfin']['ApiToken']
    TARGET_USER = config['Jellyfin']['TargetUser']
    DEFAULT_IMAGE = config['Discord']['DefaultImage']  # Customizable default image key

except KeyError as e:
    print(f"Missing configuration key: {e}")
    raise
except ValueError as e:
    print(e)
    raise

# Initialize Discord Rich Presence
rpc = Presence(DISCORD_CLIENT_ID)
rpc.connect()

def fetch_sessions():
    """Fetches active sessions from the Jellyfin server."""
    headers = {"X-Emby-Token": JELLYFIN_API_TOKEN}
    response = requests.get(f"{JELLYFIN_SERVER_URL}/Sessions", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch sessions: {response.status_code}")
        return []

def truncate_string(s, max_length):
    """Truncates a string to fit within a maximum length, appending ellipsis if needed."""
    if len(s) > max_length:
        return s[:max_length-3] + "..."
    return s

def update_presence():
    """Updates the Discord Rich Presence based on what the target user is watching or listening to."""
    previous_details = None
    previous_state = None

    while True:
        sessions = fetch_sessions()
        target_session = next((session for session in sessions if session['UserName'] == TARGET_USER), None)

        if target_session:
            now_playing = target_session.get('NowPlayingItem')
            play_state = target_session.get('PlayState', {})

            if now_playing and not play_state.get('IsPaused', False):  # Ensure the item is not paused
                title = now_playing.get('Name', 'Unknown Title')
                artist = now_playing.get('Artists', [None])[0] if now_playing.get('Artists') else 'Unknown Artist'
                album = now_playing.get('Album', 'Unknown Album')
                cover_image_tags = now_playing.get('BackdropImageTags', [])
                cover_image = cover_image_tags[0] if cover_image_tags else DEFAULT_IMAGE

                # Format the details for Rich Presence
                details = f"{title} by {artist}"
                state = f"On {album}"

                # Truncate details if necessary
                details = truncate_string(details, 128)
                state = truncate_string(state, 128)
                large_text = truncate_string(f"{title} on {album}", 128)

                # Only update the print and Rich Presence if the item or state has changed
                if details != previous_details or state != previous_state:
                    print(f"{title} by {artist} on {album}")
                    previous_details = details
                    previous_state = state

                    rpc.update(
                        details=details,            # The main details message
                        state=state,               # The state message (album name)
                        large_image=cover_image,   # Image key for the cover image
                        large_text=large_text      # Tooltip text for the image
                    )
            elif play_state.get('IsPaused', False):  # Check if the item is paused
                if previous_details is not None:  # Only clear once
                    print(f"{TARGET_USER} has paused the item.")
                    previous_details = None
                    previous_state = None
                rpc.clear()
            else:
                if previous_details is not None:  # Only clear once when there's no active item
                    print(f"{TARGET_USER} is not listening to anything.")
                    previous_details = None
                    previous_state = None
                rpc.clear()
        else:
            if previous_details is not None:  # Only clear once when the user is not active
                print(f"{TARGET_USER} is not active.")
                previous_details = None
                previous_state = None
            rpc.clear()

        time.sleep(5)  # Check every 5 seconds

if __name__ == "__main__":
    try:
        update_presence()
    except KeyboardInterrupt:
        rpc.clear()
        rpc.close()
        print("\nRich presence cleared and connection closed.")
