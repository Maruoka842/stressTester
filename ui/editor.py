import customtkinter as ctk
from pygments import lex
from pygments.lexers import get_lexer_by_name
from pygments.token import Token

class CodeEditor(ctk.CTkFrame):
    def __init__(self, master, title="Code", language="python", templates=None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.title = title
        self.templates = templates if templates is not None else {}
        self.lexer = None
        self._after_id = None

        # Header
        self.header = ctk.CTkFrame(self, height=30, fg_color="transparent")
        self.header.pack(fill="x", padx=5, pady=2)

        self.label = ctk.CTkLabel(self.header, text=self.title, font=ctk.CTkFont(weight="bold"))
        self.label.pack(side="left")

        self.lang_var = ctk.StringVar(value=language)
        self.lang_menu = ctk.CTkOptionMenu(
            self.header, 
            variable=self.lang_var, 
            values=list(self.templates.keys()),
            width=100
        )
        self.lang_menu.pack(side="right")

        # Editor Area
        self.text_area = ctk.CTkTextbox(self, font=("Consolas", 14), undo=True)
        self.text_area.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Configure tags for syntax highlighting
        self._configure_tags()
        
        # Bind events
        self.text_area.bind("<KeyRelease>", self._on_key_release, add="+")
        
        # Set listener and initial template
        self.lang_var.trace_add("write", self._on_language_change)
        self._on_language_change()

    def _configure_tags(self):
        # Using colors suitable for a dark theme (similar to VS Code)
        self.text_area._textbox.tag_configure("Token.Keyword", foreground="#569cd6")
        self.text_area._textbox.tag_configure("Token.Keyword.Constant", foreground="#569cd6")
        self.text_area._textbox.tag_configure("Token.Name.Class", foreground="#4ec9b0")
        self.text_area._textbox.tag_configure("Token.Name.Function", foreground="#dcdcaa")
        self.text_area._textbox.tag_configure("Token.Name.Builtin", foreground="#c586c0")
        self.text_area._textbox.tag_configure("Token.String", foreground="#ce9178")
        self.text_area._textbox.tag_configure("Token.String.Doc", foreground="#6a9955")
        self.text_area._textbox.tag_configure("Token.Comment", foreground="#6a9955")
        self.text_area._textbox.tag_configure("Token.Number", foreground="#b5cea8")
        self.text_area._textbox.tag_configure("Token.Operator", foreground="#d4d4d4")
        self.text_area._textbox.tag_configure("Token.Punctuation", foreground="#d4d4d4")

    def _on_key_release(self, event=None):
        if self._after_id:
            self.after_cancel(self._after_id)
        self._after_id = self.after(200, self._syntax_highlight)

    def _syntax_highlight(self):
        if not self.lexer:
            return

        # Clear existing tags
        for tag in self.text_area._textbox.tag_names():
            if tag.startswith("Token."):
                self.text_area._textbox.tag_remove(tag, "1.0", "end")
        
        # Add new tags
        text = self.text_area.get("1.0", "end-1c")
        
        # Use a running index to track position
        row, col = 1, 0
        for token, content in lex(text, self.lexer):
            start_index = f"{row}.{col}"
            
            # Calculate end position
            lines = content.split('\n')
            if len(lines) > 1:
                row += len(lines) - 1
                col = len(lines[-1])
            else:
                col += len(content)
            
            end_index = f"{row}.{col}"
            
            full_token_name = str(token)
            self.text_area._textbox.tag_add(full_token_name, start_index, end_index)
            
            # Fallback to parent token if specific tag doesn't exist
            if not self.text_area._textbox.tag_cget(full_token_name, "foreground"):
                parent_token_name = '.'.join(full_token_name.split('.')[:-1])
                if parent_token_name:
                    self.text_area._textbox.tag_add(parent_token_name, start_index, end_index)

    def _on_language_change(self, *args):
        lang = self.lang_var.get()
        try:
            self.lexer = get_lexer_by_name(lang)
        except Exception:
            self.lexer = None

        if self._is_code_empty_or_template():
             if lang in self.templates:
                self.set_code(self.templates[lang])
        
        self.after(50, self._syntax_highlight)

    def _is_code_empty_or_template(self):
        current_code = self.get_code().strip()
        if not current_code:
            return True
        for template in self.templates.values():
            if current_code == template.strip():
                return True
        return False

    def get_code(self):
        return self.text_area.get("1.0", "end-1c")

    def set_code(self, code):
        self.text_area.delete("1.0", "end")
        self.text_area.insert("1.0", code)
        self.after(50, self._syntax_highlight)
    
    def get_language(self):
        return self.lang_var.get()
