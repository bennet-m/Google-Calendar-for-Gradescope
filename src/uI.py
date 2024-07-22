import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import webbrowser
from logo import logo
import base64
from io import BytesIO

entry_values = {}

#logger
import logging
logger = logging.getLogger(__name__)

def get_school():
    def next_screen():
        school = school_var.get()
        if not school:
            messagebox.showerror("Input Error", "Please select a school.")
            return
        entry_values["school"] = school
        root.destroy()

    root = tk.Tk()
    root.title("GradeSync - Select School")
    root.geometry("600x450")

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
        logging.info(f"Logo loading error: {e}")

    header = tk.Label(root, text="Welcome to GradeSync!", font=("Helvetica", 16))
    header.pack(pady=10)
    instructions = tk.Label(root, text="Please enter the login info you use for Gradescope so we can connect to your account.", font=("Helvetica", 12))
    instructions.pack(pady=10)

    school_var = tk.StringVar()
    schools = ["Harvey Mudd College", "Other (all schools are supported)"]

    school_label = tk.Label(root, text="Select Your School:")
    school_label.pack(pady=5)

    school_dropdown = ttk.Combobox(root, textvariable=school_var, values=schools)
    school_dropdown.pack(pady=5)

    next_button = tk.Button(root, text="Next", command=next_screen)
    next_button.pack(pady=20)

    root.mainloop()

def get_email_password(school):
    def next_screen():
        username = username_entry.get()
        password = password_entry.get()
        if not username or not password:
            messagebox.showerror("Input Error", "Email and Password are required.")
            return
        entry_values["username"] = username
        entry_values["password"] = password
        root.destroy()

    root = tk.Tk()
    root.title("GradeSync - Login")
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
        logging.info(f"Logo loading error: {e}")
    if school != "Harvey Mudd College":
        username_label = tk.Label(root, text="Gradescope account email:")
        username_label.pack(pady=5)

        username_entry = tk.Entry(root)
        username_entry.pack(pady=5)

        password_label = tk.Label(root, text="Gradescope password:")
        password_label.pack(pady=5)

        password_entry = tk.Entry(root, show="*")
        password_entry.pack(pady=5)
        forgot_password_link = tk.Label(root, text="I login using \"School Credentials\" on Gradescope. What do I do?", cursor="hand1", underline=True, fg="lightblue")
        forgot_password_link.pack(pady=5)

        def sso_setup():
            webbrowser.open("https://gradesynccalendar.xyz/src/web/account.html")

        forgot_password_link.config(font=("Helvetica", 12, "underline"))
        forgot_password_link.bind("<Button-1>", lambda e: sso_setup())
    else:
        username_label = tk.Label(root, text="Mudd username:")
        username_label.pack(pady=5)

        username_entry = tk.Entry(root)
        username_entry.pack(pady=5)

        password_label = tk.Label(root, text="Mudd password:")
        password_label.pack(pady=5)

        password_entry = tk.Entry(root, show="*")
        password_entry.pack(pady=5)

    next_button = tk.Button(root, text="Next", command=next_screen)
    next_button.pack(pady=20)
    
    root.bind('<Return>', lambda event: 
        next_button.invoke())

    root.mainloop()

def admin_permission():
    def finish_setup():
        entry_values["admin"] = admin_var.get()
        root.destroy()

    root = tk.Tk()
    root.title("GradeSync - Admin Access")
    root.geometry("400x400")

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
        logging.info(f"Logo loading error: {e}")
    finish = tk.Label(root, text="Finished! Your calendar should be updated.")
    finish.pack(pady=10)
    question = tk.Label(root, text="Would you like GradeSync to run periodically in the background of your computer? This will help you stay updated on your classes.", wraplength=350)
    question.pack(pady=10)

    admin_var = tk.IntVar()
    admin_checkbox = tk.Checkbutton(root, text="Yes. I will accept the popup asking for admin access.", variable=admin_var)
    admin_checkbox.pack(pady=10)

    finish_button = tk.Button(root, text="Finish", command=finish_setup)
    finish_button.pack(pady=10)

    root.mainloop()

def get_admin_permission():
    admin_permission()
    return entry_values.get("admin") == 1

def get_login():
    get_school()
    school = entry_values.get("school")
    get_email_password(school)
    return entry_values.get("school"), entry_values.get("username"), entry_values.get("password")

#pushes a Message to a User
def message(title,text):
    root = tk.Tk()
    root.withdraw()
    root.update()
    messagebox.showinfo(title, text)
    root.update()
    root.destroy()
    root.mainloop()

#Notifies the User of a Duo popup when logging in with their HMC account
def duo():
    message("Duo Authentication", "Check for a Duo push")

#Incorrect login Notice
def incorrect_login():
    message("Incorrect Login", "Your Password and/or Username was incorrect.")