#! /usr/local/bin/python

# Mattermost Message Formatter

# Copyright (c) 2023 Maxwell Power
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom
# the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
# AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import os
import re
import psycopg2
import sys
import select

# ANSI escape codes for styling
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"
SEPARATOR = "\n" + BOLD + "-"*30 + "\n"

# Check if the environment variables are set
if not (os.environ.get('DB_HOST') or os.environ.get('DB_USER') or os.environ.get('DB_PASSWORD') or os.environ.get('DB_NAME')):
    print(RED + "[ERROR]: Environment Variables are NOT set!" + RESET)
    exit()
else:
    # Fetch database connection details from environment variables
    DB_HOST = os.environ.get('DB_HOST')
    DB_PORT = os.environ.get('DB_PORT')
    DB_USER = os.environ.get('DB_USER')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
    DB_NAME = os.environ.get('DB_NAME')
    CHANNEL_ID = os.environ.get('CHANNEL_ID', None)
    COMMIT_MODE = os.environ.get('COMMIT_MODE')
    DEBUG = os.environ.get('DEBUG')

# List of supported programming languages to check for
languages = [
    "1c", "abnf", "accesslog", "actionscript", "ada", "angelscript", "apache",
    "applescript", "arcade", "arduino", "armasm", "asciidoc", "aspectj",
    "autohotkey", "autoit", "avrasm", "awk", "axapta", "bash", "basic", "bnf",
    "brainfuck", "c", "cal", "capnproto", "ceylon", "clean", "clojure-repl",
    "clojure", "cmake", "coffeescript", "coq", "cos", "cpp", "crmsh", "crystal",
    "csharp", "csp", "css", "d", "dart", "delphi", "diff", "django", "dns",
    "dockerfile", "dos", "dsconfig", "dts", "dust", "ebnf", "elixir", "elm",
    "erb", "erlang-repl", "erlang", "excel", "fix", "flix", "fortran", "fsharp",
    "gams", "gauss", "gcode", "gherkin", "glsl", "gml", "go", "golo", "gradle",
    "graphql", "groovy", "haml", "handlebars", "haskell", "haxe", "hsp", "http",
    "hy", "inform7", "ini", "irpf90", "isbl", "java", "javascript", "jboss-cli",
    "json", "julia-repl", "julia", "kotlin", "lasso", "latex", "ldif", "leaf",
    "less", "lisp", "livecodeserver", "livescript", "llvm", "lsl", "log", "lua",
    "makefile", "markdown", "mathematica", "matlab", "maxima", "mel", "mercury",
    "mipsasm", "mizar", "mojolicious", "monkey", "moonscript", "n1ql", "nestedtext",
    "nginx", "nim", "nix", "node-repl", "nsis", "objectivec", "ocaml", "openscad",
    "oxygene", "parser3", "perl", "pf", "pgsql", "php-template", "php", "plaintext",
    "pony", "powershell", "processing", "profile", "prolog", "properties", "protobuf",
    "puppet", "purebasic", "python-repl", "python", "q", "qml", "r", "reasonml",
    "rib", "roboconf", "routeros", "rsl", "ruby", "ruleslanguage", "rust", "sas",
    "scala", "scheme", "scilab", "scss", "shell", "smali", "smalltalk", "sml",
    "sqf", "sql", "stan", "stata", "step21", "stylus", "subunit", "swift",
    "taggerscript", "tap", "tcl", "text", "thrift", "tp", "twig", "typescript",
    "vala", "vbnet", "vbscript-html", "vbscript", "verilog", "vhdl", "vim", "wasm",
    "wren", "x86asm", "xl", "xml", "xquery", "yaml", "zephir"
]

# Mattermost supports some additional aliases for formatting
additional_language_aliases = [
    "as", "as3",
    "sh",
    "coffee", "coffee-script",
    "c++", "c",
    "cs", "c#",
    "dlang",
    "patch", "udiff",
    "docker",
    "ex", "exs",
    "erl",
    "make", "mf", "gnumake", "bsdmake",
    "md", "mkd",
    "m",
    "objective_c", "objc",
    "pl",
    "pas",
    "postgres", "postgresql",
    "php3", "php4", "php5",
    "posh",
    "pp",
    "py",
    "s",
    "rb",
    "rs",
    "st", "squeak",
    "styl",
    "ts", "tsx",
    "vb", "visualbasic"
]

languages.extend(additional_language_aliases)

def process_content(content):
    # Split the content by lines
    lines = content.split('\n')

    # Remove any trailing or leading empty lines
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    # Join the lines back together
    return '\n'.join(lines)

def debug_print(message):
    if DEBUG:
        print(message)

# Connect to the PostgreSQL database
conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=DB_PASSWORD,
    dbname=DB_NAME
)
cursor = conn.cursor()

# Fetch messages from the posts table, optionally filtered by channelid, and where deleteat is set to 0 or NULL
if CHANNEL_ID:
    cursor.execute(
        "SELECT id, message FROM posts WHERE channelid = %s AND (deleteat = 0) AND TRIM(message) <> ''", (CHANNEL_ID,))
else:
    cursor.execute(
        "SELECT id, message FROM posts WHERE deleteat = 0 AND TRIM(message) <> ''")

# Function to process each match
def format_code_blocks(message, languages):
    # Define the regex pattern for code blocks
    pattern = r'```((?:.|\n)*)```'

    # Function to process each match
    def process_match(match):

        content = match.group(1).strip()  # Get the content inside the ticks
        first_word = content.split()[0] if content else ""

        # If the content starts with a known language or already has newlines, return as is
        if first_word in languages or content.startswith('\n'):
            debug_print(BLUE + f"[DEBUG]: {first_word} Detected" + RESET)
            return match.group(0)  # Return the original match without changes

        # Process the content to ensure it has the desired format
        # <-- This is the function we discussed earlier
        content = process_content(content)

        # Check if the content ends with three backticks without a newline
        if content.endswith('```'):
            content = content[:-3]  # Remove the trailing backticks

        # Return the processed content wrapped in code block ticks
        return "```\n" + content + "\n```"

    # Use re.sub to replace each match with the processed version
    result = re.sub(pattern, process_match, message)
    return result

# Process and update each message
for record in cursor:
    post_id, message = record
    # Check if the message contains a code block
    if '```' in message:
        debug_print(BLUE +
              f"[DEBUG]: Found a message with a code block (Post ID: {post_id})" + RESET)
        formatted_message = format_code_blocks(message, languages)
        if message != formatted_message:
            print(GREEN + BOLD + f"Processing Post ID: {post_id}\n" + RESET)
            print(YELLOW + "Original Message:\n-----------------" + RESET)
            print(message + "\n")
            print(YELLOW + "Formatted Message:\n------------------" + RESET)
            print(formatted_message)
            print(SEPARATOR)
            if COMMIT_MODE:
                cursor.execute(
                    "UPDATE posts SET message = %s WHERE id = %s", (formatted_message, post_id))
        else:
            debug_print(
                BLUE + f"[DEBUG]: No formatting changes required for Post ID: {post_id}\n[DEBUG]: Message:\n{message}" + RESET)
            debug_print(SEPARATOR)

# Commit the changes, rollback if not in commit mode
if COMMIT_MODE:
    print(GREEN + "Changes committed to the database." + RESET)
else:
    print(RED + "No changes were committed to the database. Run in COMMIT_MODE to apply changes." + RESET)
cursor.close()
conn.close()
