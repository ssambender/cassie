import pygame
import os
import time

# === Setup ===
pygame.init()
pygame.mixer.init()
pygame.font.init()

# Set window size and title
WIDTH, HEIGHT = 320, 240
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Music Player")

# Define colors
RED = (180, 70, 37)
ORANGE = (213, 129, 28)
YELLOW = (225, 175, 30)
GREEN = (145, 179, 47)
BLUE = (82, 141, 202)
INDIGO = (160, 82, 202)
TAN = (227, 210, 177)
BROWN = (82, 66, 46)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Set colors and text
PRIMARY = TAN
SECONDARY = BROWN
font = pygame.font.SysFont('Arial', 16)

# Declare music var preferences
MUSIC_FOLDER = "music"
SEEK_SPEED = 5  # seconds per seek
SEEK_INTERVAL = 0.2  # seconds between seek steps

# === State ===
albums = sorted([f for f in os.listdir(MUSIC_FOLDER) if os.path.isdir(os.path.join(MUSIC_FOLDER, f))])
selected_album_idx = 0
songs = []
current_song_idx = 0
is_playing = False
is_in_album = False
last_seek_time = 0

# Time tracking
current_pos = 0.0  # seconds
last_play_time = 0  # pygame.time.get_ticks()
song_length = 0.0

clock = pygame.time.Clock()


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
            # Go to previous song and seek from its end minus the overflow
            current_song_idx -= 1
            play_song(0)  # temporarily load to get length
            prev_length = song_length
            overflow = -new_pos
            new_seek_pos = max(0, prev_length - overflow)
            play_song(start_pos=new_seek_pos)
        else:
            new_pos = 0
            play_song(start_pos=new_pos)
    elif new_pos >= song_length:
        if current_song_idx < len(songs) - 1:
            overflow = new_pos - song_length
            current_song_idx += 1
            play_song(start_pos=overflow)
        else:
            # At end of final song, just stop at end
            play_song(start_pos=song_length - 0.01)
    else:
        play_song(start_pos=new_pos)


def next_song(start_pos=0.0):
    global current_song_idx
    current_song_idx = (current_song_idx + 1) % len(songs)
    play_song(start_pos=start_pos)


def draw_interface():
    screen.fill(PRIMARY)
    y = 10

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

        # Time text
        minutes = int(current_pos) // 60
        seconds = int(current_pos) % 60
        time_str = f"{minutes}:{seconds:02d}"

        total_minutes = int(song_length) // 60
        total_seconds = int(song_length) % 60
        total_time_str = f"{total_minutes}:{total_seconds:02d}"

        screen.blit(font.render("Now Playing:", True, SECONDARY), (10, y))
        y += 20

        screen.blit(font.render(f"Album: {album}", True, SECONDARY), (10, y))
        y += 20

        screen.blit(font.render(f"Track: {current_song_idx + 1} / {len(songs)}", True, SECONDARY), (10, y))
        y += 20

        clean_name = song[5:] if len(song) > 5 else song  # remove first 5 characters
        if clean_name.lower().endswith(".mp3"):
            clean_name = clean_name[:-4]  # remove .mp3
        screen.blit(font.render(f"Song: {clean_name}", True, SECONDARY), (10, y))
        y += 20

        screen.blit(font.render(f"Time: {time_str} / {total_time_str}", True, SECONDARY), (10, y))
        y += 20

        # Song progress bar
        bar_x = 10
        bar_y = y + 5
        bar_width = WIDTH - 20
        bar_height = 6

        if song_length > 0:
            song_progress = min(current_pos / song_length, 1.0)
        else:
            song_progress = 0

        pygame.draw.rect(screen, SECONDARY, (bar_x, bar_y, bar_width, bar_height), 1)  # border
        pygame.draw.rect(screen, SECONDARY, (bar_x, bar_y, bar_width * song_progress, bar_height))  # fill

        y = bar_y + bar_height + 10

        # Album progress bar
        total_tracks = len(songs)
        if total_tracks > 0 and song_length > 0:
            album_progress = (current_song_idx + current_pos / song_length) / total_tracks
        else:
            album_progress = 0

        bar_y = y
        pygame.draw.rect(screen, SECONDARY, (bar_x, bar_y, bar_width, bar_height), 1)  # border
        pygame.draw.rect(screen, SECONDARY, (bar_x, bar_y, bar_width * album_progress, bar_height))  # fill

    pygame.display.flip()


# === Main Loop ===
running = True
while running:
    draw_interface()
    clock.tick(30)
    keys = pygame.key.get_pressed()
    now = time.time()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if not is_in_album:
                if event.key == pygame.K_3:
                    selected_album_idx = (selected_album_idx + 1) % len(albums)
                elif event.key == pygame.K_2:
                    selected_album_idx = (selected_album_idx - 1) % len(albums)
                elif event.key == pygame.K_1:
                    is_in_album = True
                    load_album(selected_album_idx)
                    play_song()
            else:
                if event.key == pygame.K_1:
                    if is_playing:
                        pause_song()
                    else:
                        resume_song()
                elif event.key == pygame.K_4:
                    # Stop playback and return to album menu
                    pygame.mixer.music.stop()
                    is_in_album = False
                    is_playing = False

    # Seek while holding keys
    if is_in_album:
        if keys[pygame.K_2] and time.time() - last_seek_time > SEEK_INTERVAL:
            seek(-1)
            last_seek_time = time.time()
        elif keys[pygame.K_3] and time.time() - last_seek_time > SEEK_INTERVAL:
            seek(1)
            last_seek_time = time.time()

pygame.quit()
