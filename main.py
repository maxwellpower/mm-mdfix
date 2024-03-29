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

# -*- coding: utf-8 -*-

VERSION = "1.0.2"

# List of supported programming languages to check for
languages = [
    "1c", "abnf", "accesslog", "actionscript", "ada", "ada83", "ada95", "ada2005",
    "ada2012", "algol", "angelscript", "apache", "apl", "applescript", "arcade",
    "arduino", "armasm", "asciidoc", "aspectj", "as", "as3", "autohotkey", "autoit",
    "avrasm", "awk", "axapta", "bash", "basic", "bcpl", "bnf", "brainfuck", "bsdmake",
    "c", "c++", "c#", "cal", "capnproto", "ceylon", "clean", "clojure-repl", "clojure",
    "cmake", "coffeescript", "coffee", "coffee-script", "coq", "cos", "cobol", "cpp",
    "crmsh", "crystal", "cs", "csharp", "csp", "css", "d", "dart", "dlang", "delphi",
    "diff", "django", "dns", "dockerfile", "docker", "dos", "dsconfig", "dts", "dust",
    "ebnf", "ecmascript", "eiffel", "elixir", "elm", "erb", "erlang-repl", "erlang",
    "erl", "ex", "exs", "excel", "f", "f90", "fix", "flix", "fortran", "fsharp", "gams", 
    "gauss", "gcode", "gherkin", "glsl", "gml", "go", "golo", "golang", "gradle", 
    "graphql", "groovy", "gnumake", "haml", "handlebars", "haskell", "haxe", "hsp", 
    "http", "hy", "html", "inform7", "ini", "irpf90", "isbl", "java", "javascript", 
    "jboss-cli", "jscript", "json", "julia-repl", "julia", "kotlin", "kts", "lasso", 
    "latex", "ldif", "leaf", "less", "lisp", "livecodeserver", "livescript", "llvm", 
    "lsl", "log", "lua", "m", "makefile", "make", "markdown", "md", "mathematica", 
    "matlab", "maxima", "mel", "mercury", "mipsasm", "mizar", "mkd", "modula-2", 
    "modula-3", "mojolicious", "monkey", "moonscript", "mf", "n1ql", "nestedtext", 
    "nginx", "nim", "nix", "node-repl", "nsis", "objective-c++", "objective_c", 
    "objectivec", "objc", "ocaml", "openscad", "oxygene", "pascal", "parser3", "pas", 
    "patch", "perl", "pf", "pgsql", "php-template", "php", "php3", "php4", "php5", 
    "pl", "plaintext", "pony", "posh", "powershell", "pp", "postgres", "postgresql", 
    "processing", "profile", "prolog", "properties", "protobuf", "puppet", 
    "purebasic", "py", "python-repl", "python", "q", "qml", "r", "rails", "rb", 
    "reasonml", "rib", "roboconf", "routeros", "rs", "rsl", "ruby", "ruleslanguage", 
    "rust", "s", "sas", "scala", "scheme", "scilab", "scss", "sh", "shell", "simula", 
    "smali", "smalltalk", "sml", "sqf", "sql", "squeak", "stan", "stata", "st", 
    "step21", "stylus", "styl", "subunit", "swift", "taggerscript", "tap", "tcl", 
    "text", "thrift", "tp", "ts", "tsx", "twig", "typescript", "udiff", "vala", 
    "vb", "vbnet", "vbscript-html", "vbscript", "verilog", "vhdl", "vim", 
    "visualbasic", "wasm", "wren", "x86asm", "xl", "xml", "xhtml", "xquery", 
    "yaml", "yml", "zephir"
]

import os
import re
import psycopg2
import logging

# Setup basic logging to stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Check if the environment variables are set
if not (os.environ.get('DB_HOST') or os.environ.get('DB_USER') or os.environ.get('DB_PASSWORD') or os.environ.get('DB_NAME')):
    logging.error("Environment Variables are NOT set!")
    exit()

# Fetch database connection details from environment variables
DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT', 5432)
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_NAME = os.environ.get('DB_NAME')
CHANNEL_ID = os.environ.get('CHANNEL_ID', None)
COMMIT_MODE = os.environ.get('COMMIT_MODE', 'false').lower() == 'true'
DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'

logging.info(f"Starting mm-mdfix v{VERSION} ...")
if COMMIT_MODE:
    logging.info("COMMIT MODE: ENABLED")
else:
    logging.info("COMMIT MODE: DISABLED")

# Connect to the PostgreSQL database
try:
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=DB_NAME
    )
except psycopg2.OperationalError as e:
    logging.error(f"Failed to connect to the database: {e}")
    exit()

cursor = conn.cursor()
update_cursor = conn.cursor()

if cursor:
    logging.debug(f"Connecting to {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME} ...")
    logging.info(f"Successfully connected to database {DB_NAME}")

# Fetch messages from the posts table, optionally filtered by channelid, and where deleteat is set to 0 or NULL
if CHANNEL_ID:
    if DEBUG:
        cursor.execute("SELECT count(id) FROM posts WHERE channelid = %s AND (deleteat = 0) AND TRIM(message) <> ''", (CHANNEL_ID,))
        debugCount = cursor.fetchone()[0]
    cursor.execute(
        "SELECT id, message FROM posts WHERE channelid = %s AND (deleteat = 0) AND TRIM(message) <> ''", (CHANNEL_ID,))
else:
    if DEBUG:
        cursor.execute("SELECT count(id) FROM posts WHERE deleteat = 0 AND TRIM(message) <> ''")
        debugCount = cursor.fetchone()[0]
    cursor.execute(
        "SELECT id, message FROM posts WHERE deleteat = 0 AND TRIM(message) <> ''")

# Output the number of rows found
if DEBUG:
    logging.debug(f"Found {debugCount} posts to process!")

# Function to process each match
def format_code_blocks(message, languages):
    # Define the regex pattern for code blocks
    pattern = r'```((?:.|\n)*)```'

    # Function to process each match
    def process_match(match):

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

        content = match.group(1).strip()  # Get the content inside the ticks
        first_word = content.split()[0] if content else ""

        # If the content starts with a known language or already has newlines, return as is
        if first_word in languages or content.startswith('\n'):
            logging.debug(f"{first_word} Detected")
            return match.group(0)  # Return the original match without changes

        # Process the content to ensure it has the desired format
        content = process_content(content)

        # Check if the content ends with three backticks without a newline
        if content.endswith('```'):
            content = content[:-3]  # Remove the trailing backticks
            logging.debug(f"CONTENT RESULT: {result}")
        # Return the processed content wrapped in code block ticks
        result = "```\n" + content + "\n```"
        logging.debug(f"REGEX RESULT: {result}")
        return result

    # Use re.sub to replace each match with the processed version
    result = re.sub(pattern, process_match, message)
    return result

# Process and update each message

logging.info(f"Processing posts ...")

for record in cursor:
    post_id, message = record
    # Check if the message contains a code block
    if '```' in message:
        logging.debug(f"Found a message with a code block (Post ID: {post_id})")
        formatted_message = format_code_blocks(message, languages)
        if message != formatted_message:
            logging.info(f"Processing Post ID: {post_id}")
            logging.info("Original Message:\n-----------------\n" + message)
            logging.info("Formatted Message:\n------------------\n" + formatted_message)
            if COMMIT_MODE:
                try:
                    update_cursor.execute(
                        "UPDATE posts SET message = %s WHERE id = %s", (formatted_message, post_id))
                    conn.commit()  # Commit the update

                    # Fetch the updated message from the database to verify
                    verification_cursor = conn.cursor()
                    verification_cursor.execute(
                        "SELECT message FROM posts WHERE id = %s", (post_id,))
                    updated_message = verification_cursor.fetchone()[0]
                    verification_cursor.close()

                    # Compare the updated message with the formatted message
                    if updated_message.strip() == formatted_message.strip():
                        logging.info(f"Post ID: {post_id} - Update verified successfully.")
                    else:
                        logging.critical(f"Post ID: {post_id} - Update verification failed. The message in the database does not match the expected formatted message.")
                        exit(1)

                except Exception as e:
                    logging.error(f"Error while committing Post ID: {post_id}. Error: {e}")
                    conn.rollback()  # Rollback in case of error
        else:
            logging.debug(f"No formatting changes required for Post ID: {post_id}")
            logging.debug(f"Message:\n{message}\n")

# Commit the changes, rollback if not in commit mode
if COMMIT_MODE:
    logging.info("Changes committed to the database.")
else:
    logging.warning("No changes were committed to the database! Run in COMMIT_MODE to apply changes.")

# Close the cursors and the connection
cursor.close()
update_cursor.close()
conn.close()
