import pygame
import os
import time

# === Setup ===
pygame.init()
pygame.mixer.init()
pygame.font.init()

# Window
WIDTH, HEIGHT = 320, 240
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Music Player")
font = pygame.font.SysFont('None', 22)

# Album select screen font
custom_font_path = os.path.join("assets", "Data70.ttf")
album_font = pygame.font.Font(custom_font_path, 32)

# Background images
BACKGROUND_IMAGES = [
    "ArcadeBG.png",
    "DarkBG.png",
    "SpaceBG.png",
    "StripeBG.png",
    "VaporBG.png",
    "BlackBG.png",
]
background_idx = 2  # Starting with SpaceBG.png

BACKGROUND_NAMES = [
    img[:-6] if img.lower().endswith("BG.png") else img[:-4]  # Remove 'BG.png' or '.png'
    for img in BACKGROUND_IMAGES
]

def load_background(index):
    path = os.path.join("assets", BACKGROUND_IMAGES[index])
    return pygame.image.load(path).convert()

background_image = load_background(background_idx)

# Themes
COLOR_THEMES = [
    ("WHITE", (255, 255, 255)),
    ("TEAL", (137, 255, 255)),
    ("PINK", (255, 185, 255)),
    ("YELLOW", (255, 222, 56)),
    ("ORANGE", (242, 163, 44)),
    ("GREEN", (140, 235, 77)),
]

selected_color_idx = 0
TEXT_COLOR = COLOR_THEMES[selected_color_idx][1]
WHITE = (255, 255, 255)  # For fixed white text

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

# Settings menu state
settings_items = [
    "Change Background",
    "Change Text Color",
    "Change Seek Speed",
    "Connect to Bluetooth",
]
selected_settings_idx = 0

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

# === Music Functions ===
def load_album(album_idx):
    global songs, current_song_idx
    album_path = os.path.join(MUSIC_FOLDER, albums[album_idx])
    songs = sorted([f for f in os.listdir(album_path) if f.lower().endswith(".mp3")])
    current_song_idx = 0

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
                item_display = f"{item}: {BACKGROUND_IMAGES[background_idx]}"
            elif item == "Change Seek Speed":
                item_display = f"{item}: {SEEK_SPEED}s"
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
        album = albums[selected_album_idx]
        song = songs[current_song_idx]
        update_current_pos()

        minutes = int(current_pos) // 60
        seconds = int(current_pos) % 60
        time_str = f"{minutes}:{seconds:02d}"

        total_minutes = int(song_length) // 60
        total_seconds = int(song_length) % 60
        total_time_str = f"{total_minutes}:{total_seconds:02d}"

        screen.blit(font.render("Now Playing:", True, TEXT_COLOR), (10, y)); y += 20
        screen.blit(font.render(f"Album: {album}", True, TEXT_COLOR), (10, y)); y += 20
        screen.blit(font.render(f"Track: {current_song_idx + 1} / {len(songs)}", True, TEXT_COLOR), (10, y)); y += 20

        clean_name = song[5:] if len(song) > 5 else song
        if clean_name.lower().endswith(".mp3"):
            clean_name = clean_name[:-4]
        screen.blit(font.render(f"Song: {clean_name}", True, TEXT_COLOR), (10, y)); y += 20
        screen.blit(font.render(f"Time: {time_str} / {total_time_str}", True, TEXT_COLOR), (10, y)); y += 20

        bar_x = 10
        bar_y = y + 5
        bar_width = WIDTH - 20
        bar_height = 6

        song_progress = min(current_pos / song_length, 1.0) if song_length > 0 else 0
        pygame.draw.rect(screen, TEXT_COLOR, (bar_x, bar_y, bar_width, bar_height), 1)
        pygame.draw.rect(screen, TEXT_COLOR, (bar_x, bar_y, bar_width * song_progress, bar_height))
        y = bar_y + bar_height + 10

        total_tracks = len(songs)
        album_progress = (current_song_idx + current_pos / song_length) / total_tracks if total_tracks > 0 and song_length > 0 else 0
        bar_y = y
        pygame.draw.rect(screen, TEXT_COLOR, (bar_x, bar_y, bar_width, bar_height), 1)
        pygame.draw.rect(screen, TEXT_COLOR, (bar_x, bar_y, bar_width * album_progress, bar_height))

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

        if event.type == pygame.KEYDOWN:
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
