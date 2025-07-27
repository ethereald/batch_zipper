"""
Description: Tkinter-based GUI for batch zipping/unzipping folders using JSON encoding, with progress bar and console log.
"""
import os
import sys
import json
import base64
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, filedialog, Button, Label
from tkinter import ttk
from tkinter import simpledialog

def decode_password(b64):
    salt = "_Bz9!"
    try:
        b64core = b64.replace('@', '=').replace('!', 'A').replace('#', 'z')
        raw = base64.b64decode(b64core.encode('utf-8')).decode('utf-8')
        if raw.startswith(salt) and raw.endswith(salt):
            rev = raw[len(salt):-len(salt)]
            return rev[::-1]
    except Exception:
        pass
    return None

def prompt_password(parent=None):
    return simpledialog.askstring("Set Password", "Enter a password for Power User mode:", show='*', parent=parent)

def encode_password(pw):
    salt = "_Bz9!"
    rev = pw[::-1]
    b64 = base64.b64encode((salt + rev + salt).encode('utf-8')).decode('utf-8')
    obf = b64.replace('=', '@').replace('A', '!').replace('z', '#')
    return obf

def ensure_config(config_path):
    """
    Ensure the configuration file exists and load paths.
    Args:
        config_path (Path): Path to the config file.
    Returns:
        tuple: List of configured folder paths and the encoded password.
    Author: Kelvin
    """
    import base64
    import tkinter as tk

    if not config_path.exists():
        root = tk.Tk()
        root.withdraw()
        password = prompt_password(parent=root)
        root.destroy()
        if not password:
            password = "default"
        encoded_pw = encode_password(password)
        default = ["C:/Users/Kelvin/Pictures/AI Graphics"]
        encoded = [base64.b64encode(p.encode('utf-8')).decode('utf-8') for p in default]
        config_obj = {"meta": {"pw": encoded_pw}, "paths": encoded}
        with open(config_path, 'w') as f:
            json.dump(config_obj, f, indent=2)
    with open(config_path, 'r') as f:
        config_obj = json.load(f)
    if not config_obj.get("meta") or not config_obj["meta"].get("pw"):
        root = tk.Tk()
        root.withdraw()
        password = prompt_password(parent=root)
        root.destroy()
        if not password:
            password = "default"
        encoded_pw = encode_password(password)
        config_obj["meta"] = {"pw": encoded_pw}
        with open(config_path, 'w') as f:
            json.dump(config_obj, f, indent=2)
        with open(config_path, 'r') as f:
            config_obj = json.load(f)
    
    encoded_paths = config_obj.get("paths", [])
    encoded_pw = config_obj["meta"]["pw"]
    
    def decode_path(obf):
        try:
            return base64.b64decode(obf.encode('utf-8')).decode('utf-8')
        except Exception:
            return None
    
    decoded_paths = [p for p in [decode_path(p) for p in encoded_paths] if p is not None]
    print('DEBUG ensure_config returns:', decoded_paths, encoded_pw)
    return decoded_paths, encoded_pw

def save_config(config_path, paths):
    """
    Save the list of paths to the configuration file.
    Args:
        config_path (Path): Path to the config file.
        paths (list): List of folder paths.
    Author: Kelvin
    """
    import base64
    if config_path.exists():
        with open(config_path, 'r') as f:
            config_obj = json.load(f)
        encoded_pw = config_obj.get("meta", {}).get("pw", encode_password("default"))
    else:
        encoded_pw = encode_password("default")
    encoded = [base64.b64encode(p.encode('utf-8')).decode('utf-8') for p in paths if isinstance(p, str)]
    config_obj = {"meta": {"pw": encoded_pw}, "paths": encoded}
    with open(config_path, 'w') as f:
        json.dump(config_obj, f, indent=2)

def zipper_operation(folder, op):
    """
    Perform zip or unzip operation on a folder.
    Args:
        folder (str): Path to the folder.
        op (str): Operation type ('zip' or 'unzip').
    Author: Kelvin
    """
    from zipper import zip_folder, unzip_folder
    import builtins
    if hasattr(builtins, '_console_log'):
        _print = builtins.print
        def log_print(*args, **kwargs):
            msg = ' '.join(str(a) for a in args)
            builtins._console_log.insert('end', msg + '\n')
            builtins._console_log.see('end')
            _print(*args, **kwargs)
        builtins.print = log_print
    try:
        if op == 'zip':
            zip_folder(folder)
        elif op == 'unzip':
            unzip_folder(folder)
        else:
            messagebox.showerror("Error", f"Unknown operation: {op}")
    finally:
        if hasattr(builtins, '_console_log'):
            builtins.print = _print

def run_selected(op, paths, listbox, progress_bar=None):
    """
    Run the selected zip/unzip operation for all or selected paths.
    Args:
        op (str): Operation type ('zip' or 'unzip').
        paths (list): List of folder paths.
        listbox (Listbox or None): Tkinter Listbox widget or None for all paths.
        progress_bar (ttk.Progressbar, optional): Progress bar widget.
    Author: Kelvin
    """
    import builtins
    def update_progress(current, total, bar):
        bar['maximum'] = total
        bar['value'] = current
        bar.update_idletasks()

    if listbox is None:
        total = len(paths)
        for i, folder in enumerate(paths, 1):
            if hasattr(builtins, '_console_log'):
                builtins._console_log.insert('end', f"Working on: {folder}\n")
                builtins._console_log.see('end')
            zipper_operation(folder, op)
            if progress_bar:
                update_progress(i, total, progress_bar)
        if progress_bar:
            progress_bar['value'] = 0
        messagebox.showinfo("Done", f"{op.capitalize()} completed for {len(paths)} path(s)")
        return
    selected = listbox.curselection()
    if not selected:
        messagebox.showinfo("Info", "Select a path to run the operation.")
        return
    total = len(selected)
    for i, idx in enumerate(selected, 1):
        folder = paths[idx]
        if hasattr(builtins, '_console_log'):
            builtins._console_log.insert('end', f"Working on: {folder}\n")
            builtins._console_log.see('end')
        zipper_operation(folder, op)
        if progress_bar:
            update_progress(i, total, progress_bar)
    if progress_bar:
        progress_bar['value'] = 0
    messagebox.showinfo("Done", f"{op.capitalize()} completed for {len(selected)} path(s)")

def add_path(paths, config_path, listbox):
    """
    Add a new folder path to the configuration and listbox.
    Args:
        paths (list): List of folder paths.
        config_path (Path): Path to the config file.
        listbox (Listbox): Tkinter Listbox widget.
    Author: Kelvin
    """
    folder = filedialog.askdirectory()
    if folder:
        paths.append(folder)
        save_config(config_path, paths)
        listbox.insert(tk.END, folder)

def remove_path(paths, config_path, listbox):
    """
    Remove selected folder paths from the configuration and listbox.
    Args:
        paths (list): List of folder paths.
        config_path (Path): Path to the config file.
        listbox (Listbox): Tkinter Listbox widget.
    Author: Kelvin
    """
    selected = listbox.curselection()
    for idx in reversed(selected):
        del paths[idx]
        listbox.delete(idx)
    save_config(config_path, paths)

def main():
    import base64
    config_path = Path('directory.config')
    encoded_pw = ""
    paths = []
    try:
        result = ensure_config(config_path)
        if isinstance(result, tuple) and len(result) == 2:
            paths, encoded_pw = result
        else:
            paths, encoded_pw = [], ""
    except Exception as e:
        print('ERROR in main ensure_config:', e)
        paths, encoded_pw = [], ""    

    root = tk.Tk()
    root.title("Batch Zipper/Unzipper")

    power_user_var = tk.BooleanVar(value=False)

    def toggle_power_user():
        if power_user_var.get():
            from tkinter import simpledialog
            entered = simpledialog.askstring("Password Required", "Enter Power User password:", show='*', parent=root)
            actual_pw = decode_password(encoded_pw)
            if entered != actual_pw:
                messagebox.showerror("Access Denied", "Incorrect password.", parent=root)
                power_user_var.set(False)
                return
            listbox_frame.pack(pady=(0,10), fill='x')
            button_frame.pack(pady=10)
            console_frame.pack(fill='both', expand=True, padx=10, pady=(0,10))
        else:
            listbox_frame.pack_forget()
            button_frame.pack_forget()
            console_frame.pack_forget()

    power_user_check = tk.Checkbutton(root, text="Power User Mode", variable=power_user_var, command=toggle_power_user)
    power_user_check.pack(anchor='ne', padx=10, pady=(10,0))

    listbox_frame = tk.Frame(root)
    listbox_label = Label(listbox_frame, text="Configured Directories:")
    listbox_label.pack(anchor='w')
    dir_listbox = tk.Listbox(listbox_frame, height=8, width=80, selectmode=tk.MULTIPLE)
    dir_listbox.pack(fill='x', expand=True)
    for p in paths:
        dir_listbox.insert(tk.END, p)

    button_frame = tk.Frame(root)
    Button(button_frame, text="Add Path", width=15, command=lambda: add_path(paths, config_path, dir_listbox)).grid(row=0, column=0, padx=5)
    Button(button_frame, text="Remove Selected", width=15, command=lambda: remove_path(paths, config_path, dir_listbox)).grid(row=0, column=1, padx=5)
    Button(button_frame, text="Zip Selected", width=15, command=lambda: run_selected('zip', paths, dir_listbox, progress_bar)).grid(row=0, column=2, padx=5)
    Button(button_frame, text="Unzip Selected", width=15, command=lambda: run_selected('unzip', paths, dir_listbox, progress_bar)).grid(row=0, column=3, padx=5)

    progress_bar = ttk.Progressbar(root, orient='horizontal', length=600, mode='determinate')
    progress_bar.pack(pady=(0,10))

    console_frame = tk.Frame(root)
    console_label = Label(console_frame, text="Console Log:")
    console_label.pack(anchor='w')
    console_log = tk.Text(console_frame, height=15, width=100)
    console_log.pack(fill='both', expand=True)
    import builtins
    builtins._console_log = console_log

    basic_button_frame = tk.Frame(root)
    Button(basic_button_frame, text="Zip All", width=15, command=lambda: run_selected('zip', paths, None, progress_bar)).grid(row=0, column=0, padx=5)
    Button(basic_button_frame, text="Unzip All", width=15, command=lambda: run_selected('unzip', paths, None, progress_bar)).grid(row=0, column=1, padx=5)
    basic_button_frame.pack(pady=10)

    toggle_power_user()

    root.protocol("WM_DELETE_WINDOW", root.quit)
    root.mainloop()

if __name__ == "__main__":
    def print_encoded_password(pw):
        import base64, random, string
        salt = "_Bz9!"
        rev = pw[::-1]
        b64 = base64.b64encode((salt + rev + salt).encode('utf-8')).decode('utf-8')
        obf = "PFX" + b64.replace('=', '@').replace('A', '!').replace('z', '#')
        suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=4))
        print(f"Encoded password for '{pw}': {obf + suffix}")

    main()