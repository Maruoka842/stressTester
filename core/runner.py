import subprocess
import os
import tempfile
import shutil
import uuid

class Runner:
    def __init__(self, code, language, timeout):
        self.code = code
        self.language = language
        self.temp_dir = tempfile.mkdtemp()
        self.executable = None
        self.source_file = None
        self.timeout = timeout

    def compile(self):
        pass

    def run(self, input_str):
        pass

    def cleanup(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

class PythonRunner(Runner):
    def __init__(self, code, language, timeout):
        super().__init__(code, language, timeout)

    def compile(self):
        self.source_file = os.path.join(self.temp_dir, "script.py")
        with open(self.source_file, "w", encoding="utf-8") as f:
            f.write(self.code)
        return True, "Compilation successful"

    def run(self, input_str):
        try:
            process = subprocess.run(
                ["python", self.source_file],
                input=input_str,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            return process.stdout, process.stderr, process.returncode
        except FileNotFoundError:
            return "", "Python executable not found. Please ensure Python is installed and in your PATH.", -1
        except subprocess.TimeoutExpired:
            return "", "Timeout", -1
        except Exception as e:
            return "", str(e), -1

class CppRunner(Runner):
    def __init__(self, code, language, timeout):
        super().__init__(code, language, timeout)

    def compile(self):
        self.source_file = os.path.join(self.temp_dir, "main.cpp")
        self.executable = os.path.join(self.temp_dir, "main.exe")
        with open(self.source_file, "w", encoding="utf-8") as f:
            f.write(self.code)
        
        try:
            process = subprocess.run(
                ["g++", self.source_file, "-o", self.executable],
                capture_output=True,
                text=True
            )
        except FileNotFoundError:
            return False, "g++ compiler not found. Please install MinGW-w64 and add it to your system's PATH."

        if process.returncode != 0:
            return False, process.stderr
        return True, "Compilation successful"

    def run(self, input_str):
        if not os.path.exists(self.executable):
            return "", "Executable not found", -1
        try:
            process = subprocess.run(
                [self.executable],
                input=input_str,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            return process.stdout, process.stderr, process.returncode
        except subprocess.TimeoutExpired:
            return "", "Timeout", -1
        except Exception as e:
            return "", str(e), -1

class JavaRunner(Runner):
    def __init__(self, code, language, timeout):
        super().__init__(code, language, timeout)

    def compile(self):
        # Java requires class name to match filename. We'll assume Main or try to find it?
        # For simplicity, we'll enforce the user to use "public class Main" or just "class Main"
        # Or we can parse it. Let's assume Main for now.
        self.source_file = os.path.join(self.temp_dir, "Main.java")
        with open(self.source_file, "w", encoding="utf-8") as f:
            f.write(self.code)
        
        try:
            process = subprocess.run(
                ["javac", self.source_file],
                capture_output=True,
                text=True
            )
        except FileNotFoundError:
            return False, "javac compiler not found. Please install a JDK and add it to your system's PATH."
        if process.returncode != 0:
            return False, process.stderr
        return True, "Compilation successful"

    def run(self, input_str):
        # java -cp temp_dir Main
        try:
            process = subprocess.run(
                ["java", "-cp", self.temp_dir, "Main"],
                input=input_str,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            return process.stdout, process.stderr, process.returncode
        except FileNotFoundError:
            return "", "Java runtime not found. Please install a JRE/JDK and add it to your system's PATH.", -1
        except subprocess.TimeoutExpired:
            return "", "Timeout", -1
        except Exception as e:
            return "", str(e), -1

def get_runner(language, code, timeout):
    if language == "python":
        return PythonRunner(code, language, timeout)
    elif language == "cpp":
        return CppRunner(code, language, timeout)
    elif language == "java":
        return JavaRunner(code, language, timeout)
    return None
