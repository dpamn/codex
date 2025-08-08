import streamlit as st
from streamlit_ace import st_ace
import sqlite3
import subprocess
import os
import uuid
from hashlib import sha256

# Set page config at the very start
st.set_page_config(page_title="CodeX", layout="wide")  # Make the page use full width for better layout

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None

# Database Setup
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')
    conn.commit()
    conn.close()

def register_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    hashed_password = sha256(password.encode()).hexdigest()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()
    return True

def login_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    hashed_password = sha256(password.encode()).hexdigest()
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed_password))
    user = c.fetchone()
    conn.close()
    return user

# Initialize database
init_db()

# Sidebar for page selection
page = st.sidebar.radio("Choose a page", ["Authentication", "CodeX IDE"])

# Authentication Page
if page == "Authentication":
    st.sidebar.title("User Authentication")
    auth_mode = st.sidebar.radio("Choose Mode", ["Login", "Sign Up"])

    if auth_mode == "Sign Up":
        st.sidebar.subheader("Create a New Account")
        new_username = st.sidebar.text_input("Username", key="signup_username")
        new_password = st.sidebar.text_input("Password", type="password", key="signup_password")
        if st.sidebar.button("Register"):
            if register_user(new_username, new_password):
                st.sidebar.success("Account created successfully! Please log in.")
            else:
                st.sidebar.error("Username already exists. Please try a different one.")

    elif auth_mode == "Login":
        st.sidebar.subheader("Log In")
        username = st.sidebar.text_input("Username", key="login_username")
        password = st.sidebar.text_input("Password", type="password", key="login_password")
        if st.sidebar.button("Log In"):
            user = login_user(username, password)
            if user:
                st.sidebar.success(f"Welcome {username}!")
                st.session_state.logged_in = True
                st.session_state.username = username
            else:
                st.sidebar.error("Invalid username or password.")
                st.session_state.logged_in = False

# CodeX IDE Page (if logged in)
if page == "CodeX IDE":
    if st.session_state.logged_in:
        st.sidebar.title("User Actions")
        if st.sidebar.button("Log Out"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.success("You have successfully logged out.")
            st.rerun()  # Use st.rerun for a refresh

        st.title("CodeX - Online Code Compiler")
        st.markdown("Welcome to *CodeX*, your online code compiler! Write and execute code in multiple programming languages.")

        # Language Selection (Dropdown)
        st.subheader("Select Language")
        language = st.radio(
            "Choose a language to code:",
            ["Python", "C++", "JavaScript"],
            horizontal=True,
            help="Select the programming language for your code."

        )

        # Full-page layout with dynamic width
        col1, col2 = st.columns([1, 1])  # Equal column width

        # Code Editor
        with col1:
            editor_height = 300  # Adjusted height for a square layout
            code = st_ace(
                language=language.lower(),
                theme="monokai",
                font_size=14,
                height=editor_height,
                placeholder=f"# Write your {language} code here..."
            )

        # Input and Output Sections
        with col2:
            st.subheader("📥 Input")
            user_input = st.text_area("Enter input for your program (if required):", height=100)

            st.subheader("📤 Output")
            output_placeholder = st.empty()

        # Run Code Button
        if st.button("▶ Run Code"):
            if not code:
                st.warning("Please enter some code before running.")
            else:
                with st.spinner("Executing..."):
                    output = ""
                    file_id = str(uuid.uuid4())  # Unique ID for temp files
                    try:
                        if language == "Python":
                            filename = f"{file_id}.py"
                        elif language == "C++":
                            filename = f"{file_id}.cpp"
                        elif language == "JavaScript":
                            filename = f"{file_id}.js"

                        with open(filename, "w") as f:
                            f.write(code)

                        if language == "Python":
                            result = subprocess.run(
                                ["python", filename],
                                input=user_input,
                                capture_output=True,
                                text=True,
                                timeout=5
                            )
                        elif language == "C++":
                            subprocess.run(
                                ["g++", filename, "-o", f"{file_id}.out"],
                                capture_output=True,
                                text=True,
                                timeout=5
                            )
                            result = subprocess.run(
                                [f"./{file_id}.out"],
                                input=user_input,
                                capture_output=True,
                                text=True,
                                timeout=5
                            )
                        elif language == "JavaScript":
                            result = subprocess.run(
                                ["node", filename],
                                input=user_input,
                                capture_output=True,
                                text=True,
                                timeout=5
                            )

                        output = result.stdout + result.stderr
                        os.remove(filename)

                    except subprocess.TimeoutExpired:
                        output = "Error: Code execution timed out."
                    except Exception as e:
                        output = f"Error: {str(e)}"

                    output_placeholder.code(output)

        # Download Button
        file_extension = {
            "Python": "py",
            "C++": "cpp",
            "JavaScript": "js"
        }
        if code:
            st.download_button(
                label="💾 Download Your Code",
                data=code,
                file_name=f"code.{file_extension.get(language, 'txt')}",
                mime="text/plain"
            )
    else:
        st.warning("Please log in first to access the IDE.")
