import pygame
import os
import time
import random

# === Setup ===
pygame.init()
pygame.mixer.init()
pygame.font.init()

# Window
WIDTH, HEIGHT = 320, 240
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Music Player")

# Default font
font = pygame.font.SysFont('None', 22)

# Album select screen font
custom_font_path = os.path.join("assets", "Data70.ttf")
album_font = pygame.font.Font(custom_font_path, 32)

# Now playing screen font
fresh_palm_font_path = os.path.join("assets", "FreshPalm.ttf")
fresh_palm_font = pygame.font.Font(fresh_palm_font_path, 26)
fresh_palm_smaller = pygame.font.Font(fresh_palm_font_path, 18)
time_font_small = pygame.font.SysFont('Arial', 12)

# Background images
BACKGROUND_IMAGES = [
    "ArcadeBG.png",
    "BlackBG.png",
    "CustomBG.png",
    "DarkBG.png",
    "GroovyBG.png",
    "SpaceBG.png",
    "StripeBG.png",
    "VaporBG.png",
    "VinylBG.png",
]
background_idx = 7  # Start with vaporwave bg
BACKGROUND_NAMES = [img[:-6] for img in BACKGROUND_IMAGES]


def load_background(index):
    path = os.path.join("assets", BACKGROUND_IMAGES[index])
    return pygame.image.load(path).convert()


background_image = load_background(background_idx)
wheel_image = pygame.image.load(os.path.join("assets", "Wheel.png")).convert_alpha()

# Themes
COLOR_THEMES = [
    ("White", (255, 255, 255)),
    ("Teal", (184, 255, 255)),
    ("Pink", (255, 214, 255)),
    ("Yellow", (255, 235, 133)),
    ("Orange", (255, 188, 94)),
    ("Green", (163, 255, 77)),
]

selected_color_idx = 0
cassette_style_idx = 0  # -1 means random, start on first non-random style
TEXT_COLOR = COLOR_THEMES[selected_color_idx][1]
WHITE = (255, 255, 255)  # For fixed white text
REEL_COLOR = (33, 26, 22)


def apply_color_theme(index):
    global TEXT_COLOR
    TEXT_COLOR = COLOR_THEMES[index][1]


apply_color_theme(selected_color_idx)

# Folder & timing
MUSIC_FOLDER = "music"
seek_speed_options = [10, 20, 45, 5]
seek_speed_idx = 0
SEEK_SPEED = seek_speed_options[seek_speed_idx]
SEEK_INTERVAL = 0.2

# Music state
albums = sorted([
    folder for folder in os.listdir(MUSIC_FOLDER)
    if os.path.isdir(os.path.join(MUSIC_FOLDER, folder)) and
       any(f.lower().endswith(".mp3") for f in os.listdir(os.path.join(MUSIC_FOLDER, folder)))
])
selected_album_idx = len(albums) // 2
songs = []
current_song_idx = 0
is_playing = False
is_in_album = False
is_in_settings = False
last_seek_time = 0
is_seeking = False

# Settings menu state
settings_items = [
    "Change Background",
    "Change Text Color",
    "Change Seek Speed",
    "Change Cassette Style",
    "Show Artist Name",  # never, on pause, always TODO
    "Connect to Bluetooth",
]
selected_settings_idx = 0
album_cassette_idx = -1

cassette_images = [f"BlankCassette{i}.png" for i in range(10)]


# Stats
def get_music_stats():
    total_songs = 0
    total_size = 0
    for album in albums:
        folder = os.path.join(MUSIC_FOLDER, album)
        for f in os.listdir(folder):
            if f.lower().endswith(".mp3"):
                total_songs += 1
                total_size += os.path.getsize(os.path.join(folder, f))
    total_albums = len(albums)
    size_mb = total_size / (1024 * 1024)
    return total_albums, total_songs, round(size_mb, 2)


# Time tracking
current_pos = 0.0
last_play_time = 0
song_length = 0.0

clock = pygame.time.Clock()
wheel_angle = 0


def load_cassette_image():
    cassette_filename = cassette_images[album_cassette_idx]
    path = os.path.join("assets", cassette_filename)
    return pygame.image.load(path).convert_alpha()


def rotate_image(image, angle):
    rotated = pygame.transform.rotozoom(image, -angle, 1.0)
    rect = rotated.get_rect(center=image.get_rect().center)
    return rotated, rect


# === Music Functions ===
def load_album(album_idx):
    global songs, current_song_idx, album_cassette_idx
    album_path = os.path.join(MUSIC_FOLDER, albums[album_idx])
    songs = sorted([f for f in os.listdir(album_path) if f.lower().endswith(".mp3")])
    current_song_idx = 0

    album_name = albums[album_idx]
    if "awesome mix" in album_name.lower():
        album_cassette_idx = 4
    elif cassette_style_idx >= 0:
        album_cassette_idx = cassette_style_idx % len(cassette_images)
    else:
        album_cassette_idx = random.randint(0, len(cassette_images) - 1)


def get_song_length():
    album_path = os.path.join(MUSIC_FOLDER, albums[selected_album_idx])
    song_path = os.path.join(album_path, songs[current_song_idx])
    return pygame.mixer.Sound(song_path).get_length()


def play_song(start_pos=0):
    global is_playing, current_pos, last_play_time, song_length
    album_path = os.path.join(MUSIC_FOLDER, albums[selected_album_idx])
    song_path = os.path.join(album_path, songs[current_song_idx])
    pygame.mixer.music.load(song_path)
    pygame.mixer.music.play(start=start_pos)
    current_pos = start_pos
    last_play_time = pygame.time.get_ticks()
    song_length = get_song_length()
    is_playing = True


def pause_song():
    global is_playing, current_pos
    pygame.mixer.music.pause()
    update_current_pos()
    is_playing = False


def resume_song():
    global is_playing, last_play_time
    pygame.mixer.music.unpause()
    last_play_time = pygame.time.get_ticks()
    is_playing = True


def update_current_pos():
    global current_pos, last_play_time
    if is_playing:
        now = pygame.time.get_ticks()
        delta = (now - last_play_time) / 1000.0
        current_pos += delta
        last_play_time = now
        if current_pos >= song_length:
            next_song()


def seek(direction):
    global current_pos, current_song_idx
    update_current_pos()
    new_pos = current_pos + (direction * SEEK_SPEED)

    if new_pos < 0:
        if current_song_idx > 0:
            current_song_idx -= 1
            play_song(0)
            prev_length = song_length
            overflow = -new_pos
            new_seek_pos = max(0, prev_length - overflow)
            play_song(start_pos=new_seek_pos)
        else:
            play_song(start_pos=0)
    elif new_pos >= song_length:
        if current_song_idx < len(songs) - 1:
            overflow = new_pos - song_length
            current_song_idx += 1
            play_song(start_pos=overflow)
        else:
            play_song(start_pos=song_length - 0.01)
    else:
        play_song(start_pos=new_pos)


def next_song(start_pos=0.0):
    global current_song_idx
    current_song_idx = (current_song_idx + 1) % len(songs)
    play_song(start_pos=start_pos)


# === Drawing ===
def draw_interface():
    global wheel_angle

    # screen.blit(background_image, (0, 0))
    if is_in_album:
        # DRAW A BLACK BG
        screen.fill((0, 0, 0))

        # Update current position for dynamic reel sizing
        update_current_pos()
        total_tracks = len(songs)
        album_progress = (
                                     current_song_idx + current_pos / song_length) / total_tracks if total_tracks > 0 and song_length > 0 else 0
        left_radius = int(78 - (45 * album_progress))
        right_radius = int(35 + (40 * album_progress))
        pygame.draw.circle(screen, (33, 26, 22), (85, 110), left_radius)
        pygame.draw.circle(screen, (33, 26, 22), (WIDTH - 84, 110), right_radius)

        current_album = albums[selected_album_idx]
        cassette_image = load_cassette_image()
        screen.blit(cassette_image, (0, 0))
        # screen.blit(blank_cassette, (0, 0))

        # if is_playing:
        #    wheel_angle = (wheel_angle + 2) % 360

        spin_speed = 2 if not is_seeking else 6
        if is_playing or is_seeking:
            wheel_angle = (wheel_angle + spin_speed) % 360

        rotated_wheel, _ = rotate_image(wheel_image, wheel_angle)
        wheel_pos_left = rotated_wheel.get_rect(center=(85, 110))
        wheel_pos_right = rotated_wheel.get_rect(center=(WIDTH - 84, 110))

        screen.blit(rotated_wheel, wheel_pos_left)
        screen.blit(rotated_wheel, wheel_pos_right)
    else:
        screen.blit(background_image, (0, 0))
    y = 10

    # Settings screen
    if is_in_settings:
        screen.blit(font.render("SETTINGS MENU", True, WHITE), (10, y))
        y += 25
        for i, item in enumerate(settings_items):
            if item == "Change Text Color":
                item_display = f"{item}: {COLOR_THEMES[selected_color_idx][0]}"
            elif item == "Change Background":
                # item_display = f"{item}: {BACKGROUND_IMAGES[background_idx]}"
                item_display = f"{item}: {BACKGROUND_NAMES[background_idx]}"
            elif item == "Change Seek Speed":
                item_display = f"{item}: {SEEK_SPEED}s"
            elif item == "Change Cassette Style":
                if cassette_style_idx == -1:
                    style_name = "Random"
                else:
                    style_name = str(cassette_style_idx + 1)
                item_display = f"{item}: {style_name}"
            elif item == "Show Artist Name":
                item_display = f"Show Artist Name: Never"
            else:
                item_display = item
            prefix = "> " if i == selected_settings_idx else "  "
            screen.blit(font.render(prefix + item_display, True, WHITE), (10, y))
            y += 20

        albums_count, songs_count, total_size = get_music_stats()
        stats_text = f"{albums_count} albums | {songs_count} songs | {total_size} MiB"
        text_surface = font.render(stats_text, True, WHITE)
        text_rect = text_surface.get_rect()
        text_rect.topleft = (10, HEIGHT - text_rect.height - 10)
        screen.blit(text_surface, text_rect)
        pygame.display.flip()
        return

    # Main album select screen
    if not is_in_album:
        max_visible = 7
        half_visible = max_visible // 2
        total_albums = len(albums)
        line_height = 32
        center_y = HEIGHT // 2 - (line_height // 2)

        distance_opacity = {
            0: 255,
            1: 128,
            2: 64,
            3: 25
        }

        for i in range(-half_visible, half_visible + 1):
            idx = selected_album_idx + i
            if 0 <= idx < total_albums:
                album = albums[idx]
                text = "  " + album if idx == selected_album_idx else "  " + album

                distance = abs(i)
                alpha = distance_opacity.get(distance, 0)

                text_surface = album_font.render(text, True, TEXT_COLOR)
                text_surface.set_alpha(alpha)

                y_pos = center_y + (i * line_height)
                left_padding = 0 + (10 * max(0, (half_visible - distance)))
                screen.blit(text_surface, (left_padding, y_pos))

    else:
        # Playing screen
        album = albums[selected_album_idx]
        song = songs[current_song_idx]
        update_current_pos()

        # Time left in seconds
        time_left = max(0, song_length - current_pos)

        # Convert to mm:ss
        left_minutes = int(time_left) // 60
        left_seconds = int(time_left) % 60
        time_left_str = f"{left_minutes}:{left_seconds:02d}"

        # ALBUM NAME
        text_surface = fresh_palm_font.render(f"{album}", True, (64, 59, 56))
        text_rect = text_surface.get_rect(centerx=WIDTH // 2)
        text_rect.top = 38
        screen.blit(text_surface, text_rect)

        # TRACK NUMBER
        text_surface = time_font_small.render(f"{current_song_idx + 1}/{len(songs)}", True, (64, 59, 56))
        text_rect = text_surface.get_rect(centerx=(WIDTH // 2) - 90)
        text_rect.top = 153
        screen.blit(text_surface, text_rect)

        # TRACK NAME
        clean_name = song[5:] if len(song) > 5 else song
        if clean_name.lower().endswith(".mp3"):
            clean_name = clean_name[:-4]

        # Split by dash
        parts = clean_name.split(" - ")
        if len(parts) >= 2:
            title = parts[0].strip()
            artist = parts[-1].strip()
            # Handle cases like: "02 - Song - Artist" or "02 - Song - Remix - Artist"
            title = " - ".join(parts[0:-1]).strip()
        else:
            title = clean_name.strip()
            artist = ""

        # Display title
        title_surface = fresh_palm_smaller.render(f"{title}", True, (64, 59, 56))
        title_rect = title_surface.get_rect(centerx=WIDTH // 2)
        title_rect.top = 150
        screen.blit(title_surface, title_rect)
        # text_surface = fresh_palm_smaller.render(f"{clean_name}", True, (64, 59, 56))
        # text_rect = text_surface.get_rect(centerx=WIDTH // 2)
        # text_rect.top = 150
        # screen.blit(text_surface, text_rect)

        if artist:
            artist_surface = time_font_small.render(artist, True, (64, 59, 56))
            artist_rect = artist_surface.get_rect(centerx=WIDTH // 2)
            artist_rect.top = 168
            screen.blit(artist_surface, artist_rect)

        # TIME LEFT
        text_surface = time_font_small.render(f"{time_left_str}", True, (64, 59, 56))
        text_rect = text_surface.get_rect(centerx=(WIDTH // 2) + 90)
        text_rect.top = 153
        screen.blit(text_surface, text_rect)

        # TODO - WHEELS GLITCH A BIT EVERY FULL ROTATION

        # TODO - SPIN WHEELS FASTER WHEN SEEKING/SKIPPING

        # TODO - TAKE THE ARTIST NAME OUT OF TRACK NAME

    pygame.display.flip()


# === Main Loop ===
running = True
while running:
    draw_interface()
    clock.tick(30)
    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYUP:
            if is_in_album and event.key in (pygame.K_2, pygame.K_3):
                is_seeking = False

        if event.type == pygame.KEYDOWN:
            if is_in_album and event.key in (pygame.K_2, pygame.K_3):
                is_seeking = True

            if is_in_settings:
                if event.key == pygame.K_2:
                    selected_settings_idx = (selected_settings_idx - 1) % len(settings_items)
                elif event.key == pygame.K_3:
                    selected_settings_idx = (selected_settings_idx + 1) % len(settings_items)
                elif event.key == pygame.K_1:
                    if selected_settings_idx == 1:
                        selected_color_idx = (selected_color_idx + 1) % len(COLOR_THEMES)
                        apply_color_theme(selected_color_idx)
                    elif selected_settings_idx == 0:
                        background_idx = (background_idx + 1) % len(BACKGROUND_IMAGES)
                        background_image = load_background(background_idx)
                    elif selected_settings_idx == 2:
                        seek_speed_idx = (seek_speed_idx + 1) % len(seek_speed_options)
                        SEEK_SPEED = seek_speed_options[seek_speed_idx]
                    elif selected_settings_idx == 3:
                        cassette_style_idx += 1
                        if cassette_style_idx > 9:
                            cassette_style_idx = -1
                elif event.key == pygame.K_4:
                    is_in_settings = False
            elif not is_in_album:
                if event.key == pygame.K_3:
                    selected_album_idx = (selected_album_idx + 1) % len(albums)
                elif event.key == pygame.K_2:
                    selected_album_idx = (selected_album_idx - 1) % len(albums)
                elif event.key == pygame.K_1:
                    is_in_album = True
                    load_album(selected_album_idx)
                    play_song()
                elif event.key == pygame.K_4:
                    is_in_settings = True
            else:
                if event.key == pygame.K_1:
                    if is_playing:
                        pause_song()
                    else:
                        resume_song()
                elif event.key == pygame.K_4:
                    pygame.mixer.music.stop()
                    is_in_album = False
                    is_playing = False

    if is_in_album:
        now = time.time()
        if keys[pygame.K_2] and now - last_seek_time > SEEK_INTERVAL:
            seek(-1)
            last_seek_time = now
        elif keys[pygame.K_3] and now - last_seek_time > SEEK_INTERVAL:
            seek(1)
            last_seek_time = now

pygame.quit()
