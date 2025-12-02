import customtkinter as ctk
from ui.editor import CodeEditor
import queue
import json
from core.tester import StressTester

class StressTesterApp(ctk.CTk):
    TEMPLATES = {
        'generator': {
            'python': """import random

# Generate 1 to 5 random numbers between 1 and 100
num_count = random.randint(1, 5)
nums = [str(random.randint(1, 100)) for _ in range(num_count)]
print(" ".join(nums))
""",
            'cpp': """#include <iostream>
#include <vector>
#include <random>
#include <chrono>

int main() {
    std::mt19937 rng(std::chrono::steady_clock::now().time_since_epoch().count());
    std::uniform_int_distribution<int> count_dist(1, 5);
    std::uniform_int_distribution<int> num_dist(1, 100);
    int num_count = count_dist(rng);
    for (int i = 0; i < num_count; ++i) {
        std::cout << num_dist(rng) << (i == num_count - 1 ? "" : " ");
    }
    std::cout << std::endl;
    return 0;
}
""",
            'java': """import java.util.Random;
import java.util.stream.Collectors;
import java.util.ArrayList;
import java.util.List;

public class Main {
    public static void main(String[] args) {
        Random rand = new Random();
        int numCount = rand.nextInt(5) + 1;
        List<String> nums = new ArrayList<>();
        for (int i = 0; i < numCount; i++) {
            nums.add(String.valueOf(rand.nextInt(100) + 1));
        }
        System.out.println(String.join(" ", nums));
    }
}
"""
        },
        'solution': {
            'python': """# Read numbers from stdin, and print if they are even or odd
import sys

for line in sys.stdin:
    nums = map(int, line.strip().split())
    for num in nums:
        if num % 2 == 0:
            print(f"{num} is even")
        else:
            print(f"{num} is odd")
""",
            'cpp': """#include <iostream>
#include <string>

int main() {
    int num;
    while (std::cin >> num) {
        if (num % 2 == 0) {
            std::cout << num << " is even" << std::endl;
        } else {
            std::cout << num << " is odd" << std::endl;
        }
    }
    return 0;
}
""",
            'java': """import java.util.Scanner;

public class Main {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        while (scanner.hasNextInt()) {
            int num = scanner.nextInt();
            if (num % 2 == 0) {
                System.out.println(num + " is even");
            } else {
                System.out.println(num + " is odd");
            }
        }
        scanner.close();
    }
}
"""
        }
    }

    def __init__(self):
        super().__init__()

        self.title("Stress Tester GUI")
        self.geometry("1200x800")
        self.settings_file = "settings.json"
        self.settings = self.load_settings()

        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1) # Editors
        self.grid_rowconfigure(1, weight=0) # Controls
        self.grid_rowconfigure(2, weight=0) # Resize Handle
        self.grid_rowconfigure(3, weight=1, minsize=250) # Log/Result Area

        # Discrepancy data handling
        self.in_discrepancy_mode = False
        self.discrepancy_data = {}

        self.create_widgets()
        
        self._resizing = False
        self._resize_start_y = 0
        self._frame_start_height = 0
        self.last_failing_input = None

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        # Editors
        lang_a = self.settings['languages'].get('editor_a', 'python')
        code_a = self.settings['codes'].get('editor_a')
        self.editor_a = CodeEditor(self, title="Generator (A)", language=lang_a, templates=self.TEMPLATES['generator'])
        if code_a:
            self.editor_a.set_code(code_a)
        self.editor_a.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        lang_b = self.settings['languages'].get('editor_b', 'python')
        code_b = self.settings['codes'].get('editor_b')
        self.editor_b = CodeEditor(self, title="Solution 1 (B)", language=lang_b, templates=self.TEMPLATES['solution'])
        if code_b:
            self.editor_b.set_code(code_b)
        self.editor_b.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        lang_c = self.settings['languages'].get('editor_c', 'python')
        code_c = self.settings['codes'].get('editor_c')
        self.editor_c = CodeEditor(self, title="Solution 2 (C)", language=lang_c, templates=self.TEMPLATES['solution'])
        if code_c:
            self.editor_c.set_code(code_c)
        self.editor_c.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")

        # Controls
        self.control_frame = ctk.CTkFrame(self)
        self.control_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

        self.start_button = ctk.CTkButton(self.control_frame, text="Start Stress Test", command=self.start_test, fg_color="green")
        self.start_button.pack(side="left", padx=10, pady=10)

        self.stop_button = ctk.CTkButton(self.control_frame, text="Stop", command=self.stop_test, fg_color="red", state="disabled")
        self.stop_button.pack(side="left", padx=10, pady=10)
        
        self.status_label = ctk.CTkLabel(self.control_frame, text="Ready")
        self.status_label.pack(side="left", padx=20)

        self.timeout_label = ctk.CTkLabel(self.control_frame, text="Timeout (seconds):")
        self.timeout_label.pack(side="left", padx=(20, 5), pady=10)
        self.timeout_entry = ctk.CTkEntry(self.control_frame, width=70)
        self.timeout_entry.insert(0, "2")
        self.timeout_entry.pack(side="left", padx=(0, 10), pady=10)

        self.copy_input_button = ctk.CTkButton(self.control_frame, text="Copy Input", command=self.copy_last_input, state="disabled")
        self.copy_input_button.pack(side="left", padx=10, pady=10)

        # Resize Handle
        self.resize_handle = ctk.CTkFrame(self, height=5, cursor="sb_v_double_arrow")
        self.resize_handle.grid(row=2, column=0, columnspan=3, sticky="ew", padx=5)
        self.resize_handle.bind("<ButtonPress-1>", self.start_resizing)
        self.resize_handle.bind("<B1-Motion>", self.resize_log)
        self.resize_handle.bind("<ButtonRelease-1>", self.stop_resizing)

        # --- Bottom Frame for Logs and Results ---
        self.bottom_frame = ctk.CTkFrame(self)
        self.bottom_frame.grid(row=3, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
        self.bottom_frame.grid_rowconfigure(0, weight=1)
        self.bottom_frame.grid_columnconfigure(0, weight=1)

        # --- Log Area ---
        self.log_area = ctk.CTkTextbox(self.bottom_frame, font=("Consolas", 12))
        self.log_area.bind("<KeyPress>", self._prevent_modification)
        self.log_area.bind("<<Paste>>", self._prevent_modification)

        # --- Result Frame ---
        self.result_frame = ctk.CTkFrame(self.bottom_frame)
        self.result_frame.grid_rowconfigure(1, weight=1) # Comparison row
        self.result_frame.grid_rowconfigure(3, weight=1) # Diff row
        self.result_frame.grid_columnconfigure(0, weight=1)
        self.result_frame.grid_columnconfigure(1, weight=1)
        self.result_frame.grid_columnconfigure(2, weight=1)

        font = ("Consolas", 12)
        bold_font = ctk.CTkFont(family="Consolas", size=12, weight="bold")

        # Labels for columns
        ctk.CTkLabel(self.result_frame, text="Input", font=bold_font).grid(row=0, column=0, sticky="ew", padx=5, pady=(2,0))
        ctk.CTkLabel(self.result_frame, text="Output B", font=bold_font).grid(row=0, column=1, sticky="ew", padx=5, pady=(2,0))
        ctk.CTkLabel(self.result_frame, text="Output C", font=bold_font).grid(row=0, column=2, sticky="ew", padx=5, pady=(2,0))
        
        # Textboxes
        self.input_text = ctk.CTkTextbox(self.result_frame, font=font, wrap="none")
        self.input_text.grid(row=1, column=0, sticky="nsew", padx=(5,2), pady=5)
        self.output_b_text = ctk.CTkTextbox(self.result_frame, font=font, wrap="none")
        self.output_b_text.grid(row=1, column=1, sticky="nsew", padx=2, pady=5)
        self.output_c_text = ctk.CTkTextbox(self.result_frame, font=font, wrap="none")
        self.output_c_text.grid(row=1, column=2, sticky="nsew", padx=(2,5), pady=5)
        
        ctk.CTkLabel(self.result_frame, text="Difference", font=bold_font).grid(row=2, column=0, columnspan=3, sticky="ew", padx=5, pady=(10,0))
        self.diff_text = ctk.CTkTextbox(self.result_frame, font=font, wrap="none")
        self.diff_text.grid(row=3, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
        
        for widget in [self.input_text, self.output_b_text, self.output_c_text, self.diff_text]:
            widget.bind("<KeyPress>", self._prevent_modification)
            widget.bind("<<Paste>>", self._prevent_modification)

        self.show_log_view()

        self.log_queue = queue.Queue()
        self.tester = None

    def show_log_view(self):
        self.result_frame.grid_forget()
        self.log_area.grid(row=0, column=0, sticky="nsew")

    def show_discrepancy_results(self):
        self.log_area.grid_forget()
        self.result_frame.grid(row=0, column=0, sticky="nsew")

        self.input_text.delete("1.0", "end")
        self.output_b_text.delete("1.0", "end")
        self.output_c_text.delete("1.0", "end")
        self.diff_text.delete("1.0", "end")

        self.input_text.insert("1.0", self.discrepancy_data.get("input", ""))
        self.output_b_text.insert("1.0", self.discrepancy_data.get("output_b", ""))
        self.output_c_text.insert("1.0", self.discrepancy_data.get("output_c", ""))
        self.diff_text.insert("1.0", self.discrepancy_data.get("diff", ""))

    def log(self, message):
        self.log_area.insert("end", message + "\n")
        self.log_area.see("end")

    def check_queue(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()

                if msg == "_DISCREPANCY_START_":
                    self.in_discrepancy_mode = True
                    self.discrepancy_data = {}
                    continue
                
                if msg == "_DISCREPANCY_END_":
                    self.in_discrepancy_mode = False
                    self.show_discrepancy_results()
                    continue

                if self.in_discrepancy_mode:
                    if msg.startswith("_INPUT_::"):
                        data = msg[len("_INPUT_::"):]
                        self.discrepancy_data["input"] = data
                        self.last_failing_input = data
                        self.copy_input_button.configure(state="normal")
                    elif msg.startswith("_OUTPUT_B_::"):
                        self.discrepancy_data["output_b"] = msg[len("_OUTPUT_B_::"):]
                    elif msg.startswith("_OUTPUT_C_::"):
                        self.discrepancy_data["output_c"] = msg[len("_OUTPUT_C_::"):]
                    elif msg.startswith("_DIFF_::"):
                        self.discrepancy_data["diff"] = msg[len("_DIFF_::"):]
                else:
                    if msg.startswith("_INPUT_::"):
                        self.last_failing_input = msg[len("_INPUT_::"):]
                        self.copy_input_button.configure(state="normal")
                    else:
                        self.log(msg)
        except queue.Empty:
            pass
        
        if self.tester and self.tester.running:
            self.after(100, self.check_queue)
        else:
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            if self.status_label.cget("text") not in ["Ready", "Stopping..."]:
                if self.in_discrepancy_mode:
                    pass
                else:
                    self.status_label.configure(text="Stopped")


    def start_test(self):
        self.show_log_view()
        self.log_area.delete("1.0", "end")
        self.last_failing_input = None
        self.copy_input_button.configure(state="disabled")

        code_a = self.editor_a.get_code()
        lang_a = self.editor_a.get_language()
        code_b = self.editor_b.get_code()
        lang_b = self.editor_b.get_language()
        code_c = self.editor_c.get_code()
        lang_c = self.editor_c.get_language()

        if not code_a.strip() or not code_b.strip() or not code_c.strip():
            self.log("Error: All code fields must be filled.")
            return

        try:
            timeout_val = float(self.timeout_entry.get())
            if timeout_val <= 0:
                self.log("Error: Timeout must be a positive number.")
                return
        except ValueError:
            self.log("Error: Invalid timeout value. Please enter a number.")
            return

        self.tester = StressTester(code_a, lang_a, code_b, lang_b, code_c, lang_c, self.log_queue, timeout_val)
        self.tester.start() # type: ignore
        
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status_label.configure(text="Running...")
        self.after(100, self.check_queue)

    def stop_test(self):
        if self.tester:
            self.tester.stop()
            self.status_label.configure(text="Stopping...")

    def copy_last_input(self):
        if self.last_failing_input:
            self.clipboard_clear()
            self.clipboard_append(self.last_failing_input)
            self.log("Failing input copied to clipboard.")

    def _prevent_modification(self, event):
        if not hasattr(event, 'keysym'):
            return "break"
        if event.state & 4 and event.keysym.lower() in ['c', 'a']:
            return
        if event.keysym in ['Left', 'Right', 'Up', 'Down', 'Home', 'End', 'Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'Prior', 'Next', 'Delete', 'BackSpace']:
            return
        return "break"

    def start_resizing(self, event):
        self._resizing = True
        self._resize_start_y = event.y_root
        self._frame_start_height = self.bottom_frame.winfo_height()
        self.grid_rowconfigure(3, weight=0)

    def resize_log(self, event):
        if self._resizing:
            delta_y = event.y_root - self._resize_start_y
            new_height = self._frame_start_height - delta_y
            if new_height > 100:
                self.grid_rowconfigure(3, minsize=new_height)
    
    def stop_resizing(self, event=None):
        self._resizing = False
        self.grid_rowconfigure(3, weight=1)

    def load_settings(self):
        """Loads language and code settings from the settings file."""
        try:
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)
                if isinstance(settings, dict) and 'languages' in settings and 'codes' in settings:
                    return settings
                return self.get_default_settings()
        except (FileNotFoundError, json.JSONDecodeError):
            return self.get_default_settings()

    def save_settings(self):
        """Saves current language and code settings to the settings file."""
        settings = {
            'languages': {
                'editor_a': self.editor_a.get_language(),
                'editor_b': self.editor_b.get_language(),
                'editor_c': self.editor_c.get_language(),
            },
            'codes': {
                'editor_a': self.editor_a.get_code(),
                'editor_b': self.editor_b.get_code(),
                'editor_c': self.editor_c.get_code(),
            }
        }
        with open(self.settings_file, 'w') as f:
            json.dump(settings, f, indent=4)
            
    def get_default_settings(self):
        """Returns the default settings."""
        return {
            'languages': {
                'editor_a': 'python',
                'editor_b': 'python',
                'editor_c': 'python',
            },
            'codes': {
                'editor_a': '',
                'editor_b': '',
                'editor_c': '',
            }
        }

    def on_closing(self):
        """Called when the window is closed."""
        self.save_settings()
        self.destroy()