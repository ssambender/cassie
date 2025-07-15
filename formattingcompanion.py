import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from mutagen.mp3 import MP3


class AutocompleteEntry(tk.Entry):
    """An Entry widget with simple autocomplete dropdown."""

    def __init__(self, autocomplete_list, *args, textvariable=None, **kwargs):
        if textvariable is None:
            self.var = tk.StringVar()
        else:
            self.var = textvariable
        super().__init__(*args, textvariable=self.var, **kwargs)
        self.autocomplete_list = autocomplete_list
        self.var.trace("w", self.changed)
        self.bind("<Right>", self.selection)
        self.bind("<Down>", self.move_down)

        self.listbox_up = False

    def changed(self, name, index, mode):
        if self.var.get() == '':
            self.close_listbox()
        else:
            words = self.comparison()
            if words:
                if not self.listbox_up:
                    self.open_listbox()
                self.listbox.delete(0, tk.END)
                for w in words:
                    self.listbox.insert(tk.END,w)
            else:
                self.close_listbox()

    def selection(self, event):
        if self.listbox_up:
            self.var.set(self.listbox.get(tk.ACTIVE))
            self.close_listbox()
            self.icursor(tk.END)

    def move_down(self, event):
        if self.listbox_up:
            self.listbox.focus()
            self.listbox.selection_set(0)
            self.listbox.activate(0)

    def open_listbox(self):
        if self.listbox_up:
            return
        self.listbox = tk.Listbox()
        self.listbox.bind("<<ListboxSelect>>", self.on_listbox_select)
        self.listbox.bind("<Right>", self.selection)
        self.listbox.place(x=self.winfo_x(), y=self.winfo_y()+self.winfo_height())
        self.listbox_up = True

    def close_listbox(self):
        if self.listbox_up:
            self.listbox.destroy()
            self.listbox_up = False

    def on_listbox_select(self, event):
        if self.listbox_up:
            self.var.set(self.listbox.get(tk.ACTIVE))
            self.close_listbox()
            self.icursor(tk.END)

    def comparison(self):
        pattern = self.var.get().lower()
        return [w for w in self.autocomplete_list if w.lower().startswith(pattern)]

    def update_autocomplete_list(self, new_list):
        self.autocomplete_list = new_list


class MP3RenamerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MP3 File Renamer")
        self.root.geometry("1000x600")
        self.root.resizable(False, False)
        self.root.configure(bg="#F08820")

        self.source_folder = ""
        self.dest_folder = ""
        self.mp3_files = []
        self.selected_file = None
        self.success_label = None

        self.create_widgets()

        # heading image
        self.bg_image = Image.open("headerimage.png")
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        self.bg_label = tk.Label(self.root, image=self.bg_photo)
        self.bg_label.place(x=375, y=90, width=253, height=100)

        # left arrow
        self.arrow_image = Image.open("arrow.png")
        self.arrow_photo = ImageTk.PhotoImage(self.arrow_image)
        self.arrow_label_left = tk.Label(self.root, image=self.arrow_photo)
        self.arrow_label_left.place(x=336, y=355, width=49, height=49)
        self.arrow_label_right = tk.Label(self.root, image=self.arrow_photo)
        self.arrow_label_right.place(x=620, y=355, width=49, height=49)

    def create_widgets(self):
        # Folder buttons
        self.source_button = tk.Button(self.root, text="Choose", fg="#F08820", cursor="hand2", command=self.select_source)
        self.source_button.place(x=240, y=12, width=90)

        self.dest_button = tk.Button(self.root, text="Choose", fg="#F08820", cursor="hand2", command=self.select_dest)
        self.dest_button.place(x=880, y=12, width=90)

        # Folder Source Labels
        tk.Label(self.root, text="SOURCE FILES / IN", fg="white", bg="#F08820", font=("Helvetica", 10, "bold")).place(
            x=105, y=15)
        tk.Label(self.root, text="FINAL FILES / OUT", fg="white", bg="#F08820", font=("Helvetica", 10, "bold")).place(
            x=750, y=15)

        # Treeviews for folder structure
        style = ttk.Style()
        style.theme_use("default")
        style.map("Treeview",
                  background=[("selected", "#cccccc")],  # selected bg color
                  foreground=[("selected", "black")]  # selected text color
                  )

        self.source_tree = ttk.Treeview(self.root)
        self.source_tree["show"] = "tree"  # Hides the header bar
        source_scroll = ttk.Scrollbar(self.root, orient="vertical", command=self.source_tree.yview)  # @
        self.source_tree.configure(yscrollcommand=source_scroll.set)                                 # @

        source_scroll.place(x=15, y=49, height=520)  # Align to the right of the tree               # @
        self.source_tree.place(x=30, y=49, width=300, height=520)
        self.source_tree.bind("<<TreeviewSelect>>", self.on_file_select)

        # Destination tree setup
        self.dest_tree = ttk.Treeview(self.root)
        self.dest_tree["show"] = "tree"
        self.dest_tree.place(x=670, y=49, width=300, height=520)

        # Destination tree scrollbar
        dest_scroll = ttk.Scrollbar(self.root, orient="vertical", command=self.dest_tree.yview)
        self.dest_tree.configure(yscrollcommand=dest_scroll.set)
        dest_scroll.place(x=970, y=49, height=520)

        # Entry fields ############
        self.track_var = tk.StringVar()
        self.artist_var = tk.StringVar()
        self.album_var = tk.StringVar()
        self.number_var = tk.StringVar()

        # Track Name
        tk.Label(self.root, text="Track Name", fg="white", bg="#F08820").place(x=390, y=275)
        tk.Entry(self.root, textvariable=self.track_var).place(x=390, y=295, width=200)
        tk.Button(self.root, text="✕", fg="white", bg="#F08820", cursor="hand2", command=lambda: self.track_var.set("")).place(x=595, y=293, width=22, height=22)

        # Artist Name
        tk.Label(self.root, text="Artist Name", fg="white", bg="#F08820").place(x=390, y=325)
        tk.Entry(self.root, textvariable=self.artist_var).place(x=390, y=345, width=200)
        tk.Button(self.root, text="✕", fg="white", bg="#F08820", cursor="hand2", command=lambda: self.artist_var.set("")).place(x=595, y=343, width=22, height=22)

        # Album Name
        tk.Label(self.root, text="Album Name", fg="white", bg="#F08820").place(x=390, y=375)
        self.album_entry = AutocompleteEntry([], self.root, textvariable=self.album_var)
        self.album_entry.place(x=390, y=395, width=200)
        tk.Button(self.root, text="✕", fg="white", bg="#F08820", cursor="hand2", command=lambda: self.album_var.set("")).place(x=595, y=393, width=22, height=22)

        # Track Number
        tk.Label(self.root, text="# in Album", fg="white", bg="#F08820").place(x=390, y=425)
        tk.Entry(self.root, textvariable=self.number_var).place(x=390, y=445, width=200)
        tk.Button(self.root, text="✕", fg="white", bg="#F08820", cursor="hand2", command=lambda: self.number_var.set("")).place(x=595, y=443, width=22, height=22)

        # Transfer/save Button
        tk.Button(self.root, text="TRANSFER", fg="#F08820", cursor="hand2", command=self.save_file).place(x=450, y=495, width=100)
        self.success_label = tk.Label(self.root, text="", fg="white", bg="#F08820")
        self.success_label.place(x=436, y=550)

        # Info Box Canvas with image background
        self.info_canvas = tk.Canvas(self.root, width=338, height=63, highlightthickness=0, bd=0)
        self.info_canvas.place(x=330, y=200)

        self.box_image = Image.open("infobox.png")
        self.box_photo = ImageTk.PhotoImage(self.box_image)
        self.info_canvas.create_image(0, 0, image=self.box_photo, anchor="nw")

        # Add text directly on the canvas (initially blank)
        self.info_text = self.info_canvas.create_text(
            169, 32,  # Center of canvas (half of 338x63)
            text="",
            fill="#804C19",
            font=("Helvetica", 10, "bold"),
            anchor="center"
        )


    def populate_tree(self, tree, base_folder):
        tree.delete(*tree.get_children())
        node_map = {base_folder: ""}  # root folder not shown as node

        all_entries = []
        for root_dir, dirs, files in os.walk(base_folder):
            dirs.sort()
            files = sorted([f for f in files if f.lower().endswith(".mp3")])
            all_entries.append((root_dir, dirs, files))

        for root_dir, dirs, files in all_entries:
            parent_dir = os.path.dirname(root_dir)
            parent_node = node_map.get(parent_dir, "")

            if root_dir == base_folder:
                current_node = ""
            else:
                current_node = tree.insert(parent_node, "end", text=os.path.basename(root_dir), open=True)  # auto opens
                node_map[root_dir] = current_node

            # Sort: directories (handled already) appear first, files after
            for f in files:
                full_path = os.path.join(root_dir, f)
                tree.insert(current_node, "end", text=f, values=(full_path,))

    def select_source(self):
        self.source_folder = filedialog.askdirectory()
        if self.source_folder:
            self.source_button.config(text="Change")
            self.populate_tree(self.source_tree, self.source_folder)

    def select_dest(self):
        self.dest_folder = filedialog.askdirectory()
        if self.dest_folder:
            self.dest_button.config(text="Change")
            self.populate_tree(self.dest_tree, self.dest_folder)
            self.update_album_autocomplete_list()

    def update_album_autocomplete_list(self):
        # Scan the output folder for folders (albums)
        if not self.dest_folder or not os.path.exists(self.dest_folder):
            self.album_entry.update_autocomplete_list([])
            return
        album_names = [name for name in os.listdir(self.dest_folder)
                       if os.path.isdir(os.path.join(self.dest_folder, name))]
        self.album_entry.update_autocomplete_list(album_names)

    def on_file_select(self, event):
        selected = self.source_tree.focus()
        values = self.source_tree.item(selected, 'values')
        if values:
            self.selected_file = values[0]
            base = os.path.splitext(os.path.basename(self.selected_file))[0]
            self.track_var.set(base)

            try:
                audio = MP3(self.selected_file)
                file_size_mib = os.path.getsize(self.selected_file) / (1024 * 1024)
                bitrate_kbps = int(audio.info.bitrate / 1000)
                duration_sec = int(audio.info.length)
                minutes = duration_sec // 60
                seconds = duration_sec % 60

                info_text = f"{file_size_mib:.2f} MiB | {bitrate_kbps} kbps | {minutes}:{seconds:02d} min"
                self.info_canvas.itemconfig(self.info_text, text=info_text)
            except Exception as e:
                self.file_info_label.config(text="Unable to read audio info")

    def save_file(self):
        if not all([self.track_var.get(), self.artist_var.get(), self.number_var.get(), self.dest_folder]):
            messagebox.showerror("Missing Data", "Please fill in all fields and select an output folder.")
            return

        # Validate number between 01–99
        try:
            track_num = int(self.number_var.get())
            if not (1 <= track_num <= 99):
                messagebox.showerror("Invalid Number", "Album number must be between 01 and 99.")
                return
        except ValueError:
            messagebox.showerror("Invalid Number", "Album number must be a valid number.")
            return

        if self.selected_file is None:
            messagebox.showerror("No File Selected", "Please select a file to rename.")
            return

        album_name = self.album_var.get().strip()

        if album_name:
            album_folder_path = os.path.join(self.dest_folder, album_name)
            if not os.path.exists(album_folder_path):
                os.makedirs(album_folder_path)
            save_folder = album_folder_path
        else:
            save_folder = self.dest_folder

        new_name = f"{self.number_var.get().zfill(2)} - {self.track_var.get()} - {self.artist_var.get()}.mp3"
        dest_path = os.path.join(save_folder, new_name)

        if os.path.exists(dest_path):
            if not messagebox.askyesno("File Exists", "Output file already exists. Overwrite?"):
                return

        shutil.copy2(self.selected_file, dest_path)
        self.populate_tree(self.dest_tree, self.dest_folder)
        self.update_album_autocomplete_list()

        self.success_label.config(text="File saved successfully!")
        self.root.after(2000, lambda: self.success_label.config(text=""))


if __name__ == "__main__":
    root = tk.Tk()
    app = MP3RenamerApp(root)
    root.mainloop()
