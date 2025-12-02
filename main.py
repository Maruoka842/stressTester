import customtkinter as ctk
from ui.app import StressTesterApp

def main():
    ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
    ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

    app = StressTesterApp()
    app.mainloop()

if __name__ == "__main__":
    main()
