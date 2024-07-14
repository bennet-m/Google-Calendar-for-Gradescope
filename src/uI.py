import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import webbrowser
from logo import logo
import base64
from io import BytesIO

entry_values = {}

def ui():
    # Function to handle login
    def popUp():
        global entry_values
        school = school_var.get()
        username = username_entry.get()
        password = password_entry.get()

        if not school or not username or not password:
            messagebox.showerror("Input Error", "All fields are required.")
            return

        # Store values in the global dictionary
        entry_values = {"school": school, "username": username, "password": password}

        # Destroy the root window
        root.destroy()

    # Autocomplete functionality for the Combobox
    def on_keyrelease(event):
        value = event.widget.get()
        if value == '':
            school_dropdown['values'] = schools
        else:
            data = [item for item in schools if value.lower() in item.lower()]
            school_dropdown['values'] = data
        school_dropdown.event_generate('<<ComboboxSelected>>')

    # Create the main window
    root = tk.Tk()
    root.title("Gradescope Google Calendar Integration")
    root.geometry("400x450")

    # Load and set logo image
    try:
        image_data = base64.b64decode(logo)
        logo_image = Image.open(BytesIO(image_data))
        logo_image = logo_image.resize((100, 100), Image.LANCZOS)
        logo_photo = ImageTk.PhotoImage(logo_image)
        logo_label = tk.Label(root, image=logo_photo)
        logo_label.pack(pady=10)
        root.iconphoto(True, logo_photo)
    except Exception as e:
        print(f"Logo loading error: {e}")

    # Style customization
    style = ttk.Style()
    style.configure('TCombobox', foreground='black', background='white', fieldbackground='white')

    # Dropdown for school selection
    school_var = tk.StringVar()
    schools = ["Harvey Mudd College", "Other (all schools are supported)"]

    school_label = tk.Label(root, text="Select Your School:")
    school_label.pack(pady=5)

    school_dropdown = ttk.Combobox(root, textvariable=school_var, style='TCombobox')
    school_dropdown['values'] = schools
    school_dropdown.pack(pady=5)
    school_dropdown.bind('<KeyRelease>', on_keyrelease)

    # Textbox for username
    username_label = tk.Label(root, text="Gradescope account email:")
    username_label.pack(pady=5)

    username_entry = tk.Entry(root)
    username_entry.pack(pady=5)

    # Textbox for password
    password_label = tk.Label(root, text="Gradescope password:")
    password_label.pack(pady=5)

    password_entry = tk.Entry(root, show="*")
    password_entry.pack(pady=5)

    forgot_password_link = tk.Label(root, text="I login using \"School Credentials\" on Gradescope. What do I do?", cursor="hand1", font=("Arial", 10), underline=True)
    forgot_password_link.pack(pady=5)

    # Function to handle forgot password
    def forgotPassword():
        # Open the website link in a web browser
        webbrowser.open("https://gradesynccalendar.xyz/src/web/account.html")

    # Bind the forgot password link to the function
    forgot_password_link.bind("<Button-1>", lambda e: forgotPassword())

    login_button = tk.Button(root, text="Login", command=popUp)
    login_button.pack(pady=20)

    # Run the application
    root.mainloop()

    # Retrieve the entry values after the main loop is terminated
    school = entry_values.get("school")
    username = entry_values.get("username")
    password = entry_values.get("password")
    
    return(school, username, password)

#Notifies the User of a Duo popup when logging in with their HMC account
def duo():
    messagebox.showinfo("Duo Authentication", "Check for a Duo push")
