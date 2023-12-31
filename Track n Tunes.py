import tkinter as tk
from tkinter import filedialog
from tkinter.ttk import Progressbar
from PIL import Image, ImageTk
import threading
import pygame
from mutagen.mp3 import MP3
import os
import time
import webbrowser
from spotipy.oauth2 import SpotifyOAuth

# Initialize pygame mixer
pygame.mixer.init()

# Spotify API credentials
SPOTIFY_CLIENT_ID = '713e49f1e500481c9efae4daf8a1e4b2'
SPOTIFY_CLIENT_SECRET = '5e6f4dce27594601aa7fd57dfb49532f'
SPOTIFY_REDIRECT_URI = 'http://localhost:8888/callback'  # Replace 'your_redirect_uri' with the actual redirect URI

# Create a Spotify OAuth object
sp_oauth = SpotifyOAuth(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI)

# Store the current position of the music
current_position = 0
paused = False
selected_folder_path = ""  # Store the selected folder path
current_volume = 30  # Initial volume (from 0 to 100)

# Variable to track the visibility state of the music list
music_list_visible = True

# Variable to track the current track name position
track_name_position = 0
track_name_slide_speed = 2  # Adjust the sliding speed

# Declare canvas and text_id as global variables
canvas = None
text_id = None

# Create a flag to signal the threads to stop
stop_threads = False

def update_progress():
    global current_position
    while not stop_threads:
        if pygame.mixer.music.get_busy() and not paused:
            current_position = pygame.mixer.music.get_pos() / 1000
            pbar["value"] = current_position

            # Update the current time label
            current_time = format_time(current_position)
            lbl_current_time.config(text=current_time)

            # Check if the current song has reached its maximum duration
            if current_position >= pbar["maximum"]:
                stop_music()  # Stop the music playback
                pbar["value"] = 0  # Reset the pbar

                # Move to the next song
                next_song()

            window.update()
        time.sleep(0.1)

def format_time(seconds):
    minutes, seconds = divmod(int(seconds), 60)
    return f"{minutes:02d}:{seconds:02d}"

def slide_track_name():
    global track_name_position, window  # Declare window as a global variable
    while not stop_threads:
        track_name_position -= track_name_slide_speed
        if canvas and text_id and window:  # Check if canvas, text_id, and window are created
            canvas.coords(text_id, track_name_position, 10)
            if track_name_position < -canvas.winfo_width():
                track_name_position = canvas.winfo_width()

        if window:
            window.update()
        time.sleep(0.05)  # Adjust the speed by changing the delay

# Create a thread to update the progress bar
pt = threading.Thread(target=update_progress)
pt.daemon = True
pt.start()

# Create a thread to slide the track name
st = threading.Thread(target=slide_track_name)
st.daemon = True
st.start()

def set_volume(value):
    global current_volume
    current_volume = int(value)
    pygame.mixer.music.set_volume(current_volume / 100)

def select_music_folder():
    global selected_folder_path
    selected_folder_path = filedialog.askdirectory()
    if selected_folder_path:
        lbox.delete(0, tk.END)
        for filename in os.listdir(selected_folder_path):
            if filename.endswith(".mp3"):
                lbox.insert(tk.END, filename)  # Insert only the filename, not the full path

def browse_online():
    webbrowser.open('https://open.spotify.com')  # Open the Spotify website in the default web browser

def toggle_music_list():
    global music_list_visible
    if music_list_visible:
        lbox.pack_forget()  # Hide the listbox
    else:
        lbox.pack(pady=5, padx=10)  # Show the listbox
    music_list_visible = not music_list_visible

def previous_song():
    if len(lbox.curselection()) > 0:
        current_index = lbox.curselection()[0]
        if current_index > 0:
            lbox.selection_clear(0, tk.END)
            lbox.selection_set(current_index - 1)
            play_selected_song()

def next_song():
    if len(lbox.curselection()) > 0:
        current_index = lbox.curselection()[0]
        if current_index < lbox.size() - 1:
            lbox.selection_clear(0, tk.END)
            lbox.selection_set(current_index + 1)
            play_selected_song()

def play_selected_song():
    global current_position, paused
    if len(lbox.curselection()) > 0:
        current_index = lbox.curselection()[0]
        selected_song = lbox.get(current_index)
        full_path = os.path.join(selected_folder_path, selected_song)  # Add the full path again
        pygame.mixer.music.load(full_path)  # Load the selected song
        pygame.mixer.music.set_volume(current_volume / 100)  # Set the initial volume
        pygame.mixer.music.play(start=current_position)  # Play the song from the current position
        paused = False
        audio = MP3(full_path)
        song_duration = audio.info.length
        pbar["maximum"] = song_duration  # Set the maximum value of the pbar to the song duration

        # Update the total duration label
        total_duration = format_time(song_duration)
        lbl_total_duration.config(text=total_duration)

        # Update the track name label
        if canvas and text_id:  # Check if canvas and text_id are created
            canvas.itemconfig(text_id, text=selected_song)

def toggle_play_pause():
    global paused
    if paused:
        # Resume the paused music
        pygame.mixer.music.unpause()
        paused = False
        btn_play_pause.config(image=pause_icon)  # Change button image
    else:
        # Pause the currently playing music
        pygame.mixer.music.pause()
        paused = True
        btn_play_pause.config(image=play_icon)  # Change button image

def stop_music():
    global paused
    # Stop the currently playing music and reset the progress bar
    pygame.mixer.music.stop()
    paused = False

    # Clear the current time label
    lbl_current_time.config(text="00:00")

# Add a function to get the Spotify URI for a track
def get_spotify_track_uri(track_name):
    results = sp.search(q=track_name, type='track')
    if results['tracks']['items']:
        return results['tracks']['items'][0]['uri']
    return None

# Add a function to play a Spotify track
def play_spotify_track(track_uri):
    sp.start_playback(uris=[track_uri])

# Create the main window
window = tk.Tk()
window.title("Trak n Tunes Music Player")

# Set the window size for iPhone (412x915)
window.geometry("412x915")

# Set the window icon
icon_path = "music_icon.ico"
if os.path.exists(icon_path):
    window.iconbitmap(icon_path)

# Load the background image
background_image = Image.open("wallpaper.png")
background_photo = ImageTk.PhotoImage(background_image)

# Create a label to hold the background image
background_label = tk.Label(window, image=background_photo)
background_label.place(relx=0.5, rely=0.5, anchor="center")  # Center the image

# Create a label for the music player title
l_music_player = tk.Label(window, text="Trak n Tunes Music Player", font=("Magneto", 20, "bold"))
l_music_player.pack(pady=20)  # Increased padding

# Add a label for the tagline
l_tagline = tk.Label(window, text="Your Ultimate Music Experience.....", font=("Segoe Script", 12), fg="#666")
l_tagline.pack(pady=5)


# Create a button to select the music folder
btn_select_folder = tk.Button(window, text="Browse offline",
                              command=select_music_folder,
                              font=("Helvetica", 15), bg="#4CAF50", fg="white")
btn_select_folder.pack(pady=10)  # Increased padding

# Create a button to browse online
btn_browse_online = tk.Button(window, text="Browse Online", command=browse_online,
                              font=("Helvetica", 15), bg="#2196F3", fg="white")
btn_browse_online.pack(pady=10)

# Create a listbox to display the available songs
lbox = tk.Listbox(window, width=40, font=("Helvetica", 12))
lbox.pack(pady=10, padx=20)  # Increased padding and spacing

# Create a frame to hold the control buttons without a background color
btn_frame = tk.Frame(window, bg="")
btn_frame.pack(pady=10, padx=20, ipadx=10, ipady=5)  # Increased padding and spacing

# Load image icons and resize them
pause_icon = ImageTk.PhotoImage(Image.open("pause-button.png").resize((24, 24)))
play_icon = ImageTk.PhotoImage(Image.open("play-button.png").resize((24, 24)))
back_icon = ImageTk.PhotoImage(Image.open("back-button.png").resize((24, 24)))
next_icon = ImageTk.PhotoImage(Image.open("next-button.png").resize((24, 24)))

# Create a button to go to the previous song
btn_previous = tk.Button(btn_frame, image=back_icon, command=previous_song)
btn_previous.grid(row=0, column=0, padx=(0, 5))  # Grid layout

# Create a button to play/pause the music
btn_play_pause = tk.Button(btn_frame, image=play_icon, command=toggle_play_pause)
btn_play_pause.grid(row=0, column=1, padx=5)  # Grid layout

# Create a button to go to the next song
btn_next = tk.Button(btn_frame, image=next_icon, command=next_song)
btn_next.grid(row=0, column=2, padx=(5, 0))  # Grid layout

# Create a volume control slider
volume_slider = tk.Scale(window, from_=0, to=100, orient=tk.HORIZONTAL, command=set_volume)
volume_slider.set(current_volume)
volume_slider.pack(pady=10, padx=20)  # Increased padding and spacing

# Create a progress bar to indicate the current song's progress
pbar_frame = tk.Frame(window)
pbar_frame.pack(pady=10, padx=20)  # Increased padding and spacing

# Create a label for current time
lbl_current_time = tk.Label(pbar_frame, text="00:00", font=("Helvetica", 10))
lbl_current_time.grid(row=0, column=0, padx=(0, 5))  # Added padx

# Create a progress bar
pbar = Progressbar(pbar_frame, length=200, mode="determinate", style="TProgressbar")
pbar.grid(row=0, column=1)

# Create a label for total duration
lbl_total_duration = tk.Label(pbar_frame, text="00:00", font=("Helvetica", 10))
lbl_total_duration.grid(row=0, column=2, padx=(5, 0))  # Added padx

# Create a canvas to display the sliding track name
canvas = tk.Canvas(window, width=300, height=30)
canvas.pack(pady=10)

# Set the canvas background color to match the window background color
canvas.configure(bg=window.cget('bg'))

# Create text on the canvas
text_id = canvas.create_text(1, 10, text="", anchor=tk.W, font=("Helvetica", 10), fill="black")

# Create a button to toggle the visibility of the music list
btn_toggle_list = tk.Button(window, text="Playist", command=toggle_music_list,
                            font=("Helvetica", 12), bg="#2196F3", fg="white")
btn_toggle_list.pack(pady=10)

window.mainloop()

# Set the flag to stop threads when the window is closed
stop_threads = True
