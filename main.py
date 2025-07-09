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
font = pygame.font.SysFont('Arial', 16)

# Themes
COLOR_THEMES = [
    ("WHITE", (255, 255, 255), (0, 0, 0)),
    ("BLACK", (0, 0, 0), (255, 255, 255)),
    ("TAN", (227, 210, 177), (82, 66, 46)),
    ("RED", (255, 255, 255), (180, 70, 37)),
    ("ORANGE", (213, 129, 28), (255, 255, 255)),
    ("YELLOW", (225, 175, 30), (0, 0, 0)),
    ("GREEN", (145, 179, 47), (0, 0, 0)),
    ("BLUE", (82, 141, 202), (255, 255, 255)),
    ("INDIGO", (160, 82, 202), (255, 255, 255)),
]

selected_color_idx = 0
PRIMARY = COLOR_THEMES[selected_color_idx][1]
SECONDARY = COLOR_THEMES[selected_color_idx][2]


def apply_color_theme(index):
    global PRIMARY, SECONDARY
    PRIMARY = COLOR_THEMES[index][1]
    SECONDARY = COLOR_THEMES[index][2]


apply_color_theme(selected_color_idx)

# Folder & timing
MUSIC_FOLDER = "music"
seek_speed_options = [10, 20, 45, 5]
seek_speed_idx = 0
SEEK_SPEED = seek_speed_options[seek_speed_idx]
SEEK_INTERVAL = 0.2

# Music state
# albums = sorted([f for f in os.listdir(MUSIC_FOLDER) if os.path.isdir(os.path.join(MUSIC_FOLDER, f))])
albums = sorted([
    folder for folder in os.listdir(MUSIC_FOLDER)
    if os.path.isdir(os.path.join(MUSIC_FOLDER, folder)) and
    any(f.lower().endswith(".mp3") for f in os.listdir(os.path.join(MUSIC_FOLDER, folder)))
])
selected_album_idx = 0
songs = []
current_song_idx = 0
is_playing = False
is_in_album = False
is_in_settings = False
last_seek_time = 0

# Settings menu state
settings_items = [
    "Change Theme",
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
    screen.fill(PRIMARY)
    y = 10

    if is_in_settings:
        screen.blit(font.render("SETTINGS MENU", True, SECONDARY), (10, y));
        y += 25

        for i, item in enumerate(settings_items):
            if item == "Change Theme":
                item_display = f"{item}: {COLOR_THEMES[selected_color_idx][0]}"
            elif item == "Change seek/skip time":
                item_display = f"{item}: {SEEK_SPEED}s"
            else:
                item_display = item

            prefix = "> " if i == selected_settings_idx else "  "
            screen.blit(font.render(prefix + item_display, True, SECONDARY), (10, y))
            y += 20

        # Music folder stats
        y += 5
        albums_count, songs_count, total_size = get_music_stats()
        stats_text = f"{albums_count} albums | {songs_count} songs | {total_size} MiB"
        text_surface = font.render(stats_text, True, SECONDARY)
        text_rect = text_surface.get_rect()
        text_rect.topleft = (10, HEIGHT - text_rect.height - 10)  # 5px padding from bottom
        screen.blit(text_surface, text_rect)
        pygame.display.flip()
        return

    if not is_in_album:
        for i, album in enumerate(albums):
            text = "> " + album if i == selected_album_idx else "  " + album
            label = font.render(text, True, SECONDARY)
            screen.blit(label, (10, y))
            y += 20
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

        screen.blit(font.render("Now Playing:", True, SECONDARY), (10, y));
        y += 20
        screen.blit(font.render(f"Album: {album}", True, SECONDARY), (10, y));
        y += 20
        screen.blit(font.render(f"Track: {current_song_idx + 1} / {len(songs)}", True, SECONDARY), (10, y));
        y += 20

        clean_name = song[5:] if len(song) > 5 else song
        if clean_name.lower().endswith(".mp3"):
            clean_name = clean_name[:-4]
        screen.blit(font.render(f"Song: {clean_name}", True, SECONDARY), (10, y));
        y += 20
        screen.blit(font.render(f"Time: {time_str} / {total_time_str}", True, SECONDARY), (10, y));
        y += 20

        bar_x = 10
        bar_y = y + 5
        bar_width = WIDTH - 20
        bar_height = 6

        song_progress = min(current_pos / song_length, 1.0) if song_length > 0 else 0
        pygame.draw.rect(screen, SECONDARY, (bar_x, bar_y, bar_width, bar_height), 1)
        pygame.draw.rect(screen, SECONDARY, (bar_x, bar_y, bar_width * song_progress, bar_height))

        y = bar_y + bar_height + 10

        total_tracks = len(songs)
        album_progress = (
                                     current_song_idx + current_pos / song_length) / total_tracks if total_tracks > 0 and song_length > 0 else 0
        bar_y = y
        pygame.draw.rect(screen, SECONDARY, (bar_x, bar_y, bar_width, bar_height), 1)
        pygame.draw.rect(screen, SECONDARY, (bar_x, bar_y, bar_width * album_progress, bar_height))

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
                    if selected_settings_idx == 0:
                        selected_color_idx = (selected_color_idx + 1) % len(COLOR_THEMES)
                        apply_color_theme(selected_color_idx)
                    elif selected_settings_idx == 1:
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
