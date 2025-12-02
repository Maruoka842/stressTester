# Stress Tester GUI

A graphical user interface for stress testing competitive programming solutions.

This tool allows you to test two different solutions against each other using a generator script. It's useful for finding edge cases where one solution might be failing or producing a different output.

![Screenshot of the application](https://i.imgur.com/YOUR_SCREENSHOT_HERE.png) 
*(Note: You will need to take a screenshot of your application and replace the link above.)*

## Features

-   Side-by-side code editors for a generator and two solutions.
-   Supports multiple languages: Python, C++, and Java.
-   Runs solutions in parallel to maximize testing speed.
-   Stops automatically when a discrepancy is found.
-   Displays the failing test case, the outputs of both solutions, and a side-by-side diff.
-   Saves your code and language preferences automatically.
-   Adjustable timeout for running solutions.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
    cd YOUR_REPOSITORY
    ```

2.  **Install dependencies:**
    This project uses Python 3 and requires `customtkinter`.

    ```bash
    pip install -r requirements.txt
    ```
    *(I will create the `requirements.txt` file in the next step.)*

## How to Use

1.  **Run the application:**
    ```bash
    python main.py
    ```

2.  **Write your code:**
    -   **Generator (A):** Write a script that generates test case input and prints it to standard output.
    -   **Solution 1 (B):** Your first solution. It should read from standard input and print the result to standard output.
    -   **Solution 2 (C):** Your second solution (or a reference/brute-force solution) to compare against.

3.  **Select the language** for each script from the dropdown menu above each editor.

4.  **Set the timeout** (in seconds) that each solution is allowed to run for per test case.

5.  **Click "Start Stress Test".**

    -   The application will continuously generate test cases, run both solutions, and compare their outputs.
    -   The log panel at the bottom will show the progress.
    -   If the outputs of Solution B and Solution C are different, the test will stop, and the application will display the input that caused the issue, the two different outputs, and a highlighted diff.

6.  **Click "Stop"** to manually stop the test at any time.

## How it Works

1.  The **Generator (A)** is executed to produce a random test case.
2.  The standard output of the generator is passed as standard input to both **Solution 1 (B)** and **Solution 2 (C)**.
3.  The solutions are run in parallel in separate processes.
4.  The application captures the standard output of both solutions.
5.  The outputs are trimmed of leading/trailing whitespace and compared.
6.  If they don't match, the test is halted, and the results are displayed.
7.  This process repeats until a discrepancy is found or the user stops the test.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
