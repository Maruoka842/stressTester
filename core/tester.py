import threading
import queue
import time
import difflib
from core.runner import get_runner

class StressTester:
    def __init__(self, code_a, lang_a, code_b, lang_b, code_c, lang_c, log_queue, timeout):
        self.runner_a = get_runner(lang_a, code_a, timeout)
        self.runner_b = get_runner(lang_b, code_b, timeout)
        self.runner_c = get_runner(lang_c, code_c, timeout)
        self.log_queue = log_queue
        self.running = False
        self.thread = None
        self.timeout = timeout

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run_loop)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def _log(self, message):
        self.log_queue.put(message)

    def _run_loop(self):
        self._log("Starting stress test...")
        
        # Compile all
        runners = [("A", self.runner_a), ("B", self.runner_b), ("C", self.runner_c)]
        for name, runner in runners:
            self._log(f"Compiling {name}...")
            success, msg = runner.compile()
            if not success:
                self._log(f"Compilation failed for {name}:\n{msg}")
                self.running = False
                return
        
        self._log("Compilation successful. Running tests...")
        
        case_count = 0
        while self.running:
            case_count += 1
            # Run A to generate input
            input_str, stderr, ret = self.runner_a.run("")
            if ret != 0:
                self._log(f"Generator A failed (Case {case_count}):\nError:\n{stderr}\n(No input for generator)")
                self.running = False
                break
            
            # --- Parallel execution for B and C ---
            results = {}
            def run_and_store(runner_name, runner, input_str):
                out, err, ret = runner.run(input_str)
                results[runner_name] = (out, err, ret)

            thread_b = threading.Thread(target=run_and_store, args=('B', self.runner_b, input_str))
            thread_c = threading.Thread(target=run_and_store, args=('C', self.runner_c, input_str))

            thread_b.start()
            thread_c.start()

            thread_b.join()
            thread_c.join()

            out_b, err_b, ret_b = results['B']
            out_c, err_c, ret_c = results['C']
            # --- End of parallel execution ---

            if ret_b != 0:
                self._log(f"Solution B failed (Case {case_count}):\nError:\n{err_b}")
                self._log(f"Input:\n---\n{input_str.strip()}\n---")
                self._log(f"_INPUT_::{input_str.strip()}")
                self.running = False
                break

            if ret_c != 0:
                self._log(f"Solution C failed (Case {case_count}):\nInput:\n---\n{input_str.strip()}\n---\nError:\n{err_c}")
                self._log(f"_INPUT_::{input_str.strip()}")
                self.running = False
                break

            # Compare
            if out_b.strip() != out_c.strip():
                self._log(f"Discrepancy found at Case {case_count}!")
                self._log("_DISCREPANCY_START_")
                self._log(f"_INPUT_::{input_str.strip()}")
                self._log(f"_OUTPUT_B_::{out_b.strip()}")
                self._log(f"_OUTPUT_C_::{out_c.strip()}")
                
                diff_text = _generate_side_by_side_diff(out_b, out_c)
                self._log(f"_DIFF_::{diff_text}")
                self._log("_DISCREPANCY_END_")

                self.running = False
                break
            
            if case_count % 10 == 0:
                self._log(f"Checked {case_count} cases...")
            
            # Small sleep to prevent UI freezing if too fast? No, queue handles it.
            # But maybe don't spam too hard.
            # time.sleep(0.01) 

        self._log("Stress test stopped.")
        
        # Cleanup
        self.runner_a.cleanup()
        self.runner_b.cleanup()
        self.runner_c.cleanup()

def _generate_side_by_side_diff(s1, s2, width=80):
    """
    Generates a simplified side-by-side diff view.
    """
    s1_lines = s1.strip().splitlines()
    s2_lines = s2.strip().splitlines()

    diff = list(difflib.ndiff(s1_lines, s2_lines))

    lines = []
    half_width = width // 2 - 2  # -2 for separator

    lines.append("Solution 1 (B)".ljust(half_width) + " | " + "Solution 2 (C)".ljust(half_width))
    lines.append("-" * (half_width) + "-+-" + "-" * (half_width))

    i = 0
    while i < len(diff):
        line = diff[i]
        tag = line[0]
        content = line[2:]

        if tag == ' ': # Line is common
            lines.append(content.ljust(half_width) + " | " + content.ljust(half_width))
            i += 1
        elif tag == '-': # Line is in s1 only
            line1_content = content
            # Check if next line is an addition (part of a change)
            if i + 1 < len(diff) and diff[i+1][0] == '+':
                line2_content = diff[i+1][2:]
                lines.append(f"- {line1_content}".ljust(half_width) + " | " + f"+ {line2_content}".ljust(half_width))
                i += 2
            else:
                lines.append(f"- {line1_content}".ljust(half_width) + " | " + "".ljust(half_width))
                i += 1
        elif tag == '+': # Line is in s2 only
            lines.append("".ljust(half_width) + " | " + f"+ {content}".ljust(half_width))
            i += 1
        elif tag == '?': # Ignore the hint line for ndiff
            i += 1
        else: # Should not happen, but as a safeguard
            i += 1
    
    return "\n".join(lines)
