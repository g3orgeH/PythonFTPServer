import threading
from flask import Flask, request, jsonify
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
import json
import os
from datetime import datetime
from flask import send_from_directory, jsonify
from urllib.parse import unquote

# === FTP Server Setup ===
FTP_ROOT = "FTP_ROOT"
FTP_PORT = 2121

authorizer = DummyAuthorizer()
def load_users_from_file(path="users.json"):
    if not os.path.exists(path):
        print(f"User file {path} not found. Creating a new one...")
        with open(path, 'w') as f:
            json.dump([], f, indent=4)
        return

    with open(path, 'r') as f:
        users = json.load(f)
        for user in users:
            try:
                authorizer.add_user(
                    user["username"],
                    user["password"],
                    user.get("homedir", FTP_ROOT),
                    perm=user.get("perm", "elradfmw")
                )
                print(f"[+] Loaded user: {user['username']}")
            except Exception as e:
                print(f"[!] Error loading user {user['username']}: {e}")

# Call the loader
load_users_from_file()

#authorizer.add_anonymous(FTP_ROOT, perm="elradfmw") # Anonymous user



handler = FTPHandler
handler.authorizer = authorizer

server = FTPServer(("0.0.0.0", FTP_PORT), handler)

# === Management API ===
app = Flask(__name__)
app.secret_key = 'D7DfmEAH^T4@MA0NBavT'  # Make this strong!

from flask import session, redirect, url_for
@app.before_request
def require_login():
    allowed_routes = ['login', 'logout']  # add any more public routes here
    if request.endpoint not in allowed_routes and not session.get('logged_in'):
        return redirect(url_for('login'))

# Login Page
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # Simple hardcoded check (replace with database for production!)
        if username == 'admin' and password == 'admin':
            session['logged_in'] = True
            return redirect(url_for('admin_panel'))
        else:
            return 'Invalid credentials', 401
    return '''
    <form method="post">
        Username: <input name="username"><br>
        Password: <input name="password" type="password"><br>
        <input type="submit" value="Login">
    </form>
    '''

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Decorator to protect your admin panel
def login_required(f):
    def wrap(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('/'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

@app.route('/admin_panel')
def admin_panel():
    return '''
    <h2>FTP User Manager</h2>
    <!-- Logout Button -->
    <form action="/logout" method="get" style="margin-bottom: 20px;">
        <button type="submit">Logout</button>
    </form>
    <form action="/add_user" method="post" onsubmit="submitForm(event)">
        <label>Username:</label><br>
        <input type="text" name="username" required><br>
        <label>Password:</label><br>
        <input type="password" name="password" required><br>
        <label>Home Directory:</label><br>
        <input type="text" name="homedir" value="FTP_ROOT"><br>
        <label>Permissions:</label><br>
        <select name="perm" id="perm">
          <option value="">No Access</option>
          <option value="r">Read Only</option>
          <option value="lr">Read + List</option>
          <option value="elradf">Standard User</option>
          <option value="elradfmw" selected>Full Access</option>
        </select>
        <button type="submit">Add User</button>
    </form>

    <br><hr><br>

    <button onclick="listUsers()">List Users</button>
    <ul id="userList"></ul>
    
    <h3>FTP Server Directory Listing</h3>
    <button onclick="loadFtpData()">Refresh FTP Data</button>
    <ul id="ftpDataBox" style="background:#eee; padding:10px; border:1px solid #ccc;"></ul>
    
    <h3>Upload a File to FTP</h3>
    <form action="/upload_file" method="post" enctype="multipart/form-data">
        <label for="file">Choose File:</label><br>
        <input type="file" name="file" id="file" required><br><br>
        <button type="submit">Upload</button>
    </form>
    <br><hr><br>


    <script>
        async function submitForm(event) {
            event.preventDefault();
            const form = event.target.closest('form');
            const formData = new FormData(form);
            const jsonData = {};
            formData.forEach((value, key) => { jsonData[key] = value; });
            const res = await fetch('/add_user', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(jsonData)
            });
            const result = await res.json();
            alert(JSON.stringify(result));
        }

        async function listUsers() {
            const res = await fetch('/list_users');
            const data = await res.json();
            let userList = document.getElementById('userList');
            userList.innerHTML = '';
            data.users.forEach(user => {
                let li = document.createElement('li');
                li.textContent = user;
                let delButton = document.createElement('button');
                delButton.textContent = 'Remove';
                delButton.onclick = async function() {
                    await fetch('/remove_user', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({username: user})
                    });
                    listUsers();  // Refresh list
                };
                li.appendChild(delButton);
                userList.appendChild(li);
            });
        }
        async function loadFtpData(path = '', parentElement = null) {
            const res = await fetch('/ftp_data' + (path ? `?path=${encodeURIComponent(path)}` : ''));
            const data = await res.json();
        
            if (!parentElement) {
                // First load: clear and create root <ul>
                const ftpDataBox = document.getElementById('ftpDataBox');
                ftpDataBox.innerHTML = '';
                parentElement = document.createElement('ul');
                ftpDataBox.appendChild(parentElement);
            }
        
            if (Array.isArray(data)) {
                data.forEach(item => {
                    let li = document.createElement('li');
                    li.textContent = item.name + ' ';
        
                    if (item.is_file) {
                        let downloadButton = document.createElement('button');
                        downloadButton.textContent = 'Download';
                        downloadButton.onclick = function() {
                            window.location.href = '/download_file/' + encodeURIComponent(path ? `${path}/${item.name}` : item.name);
                        };
        
                        let delButton = document.createElement('button');
                        delButton.textContent = 'Delete';
                        delButton.onclick = async function() {
                            await deleteFile(path ? `${path}/${item.name}` : item.name);
                            parentElement.removeChild(li);  // Remove from UI directly
                        };
        
                        li.appendChild(downloadButton);
                        li.appendChild(delButton);
        
                    } else {
                        // Folder logic
                        let toggleButton = document.createElement('button');
                        toggleButton.textContent = '[+]';
                        let isLoaded = false;
                        let subList = document.createElement('ul');
                        subList.style.display = 'none';
        
                        toggleButton.onclick = async function() {
                            if (!isLoaded) {
                                await loadFtpData(path ? `${path}/${item.name}` : item.name, subList);
                                isLoaded = true;
                            }
                            subList.style.display = subList.style.display === 'none' ? 'block' : 'none';
                            toggleButton.textContent = subList.style.display === 'none' ? '[+]' : '[-]';
                        };
        
                        li.appendChild(toggleButton);
                        li.appendChild(subList);
                    }
        
                    parentElement.appendChild(li);
                });
            } else {
                let errorLi = document.createElement('li');
                errorLi.textContent = `Error: ${data.error}`;
                parentElement.appendChild(errorLi);
            }
        }





        
        async function deleteFile(filePath) {
            const res = await fetch('/delete_file', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ file: filePath })
            });
            const data = await res.json();
            if (data.status !== "success") {
                alert('Error deleting file: ' + data.error);
            }
        }

    </script>
    '''

def save_user_to_file(user, path="users.json"):
    try:
        if os.path.exists(path):
            with open(path, 'r') as f:
                users = json.load(f)
        else:
            users = []

        users.append(user)

        with open(path, 'w') as f:
            json.dump(users, f, indent=4)

        print(f"[+] Saved user {user['username']} to {path}")
    except Exception as e:
        print(f"[!] Error saving user: {e}")
def delete_user_by_username(username, path="users.json"):
    try:
        if not os.path.exists(path):
            print(f"[!] File {path} does not exist.")
            return

        with open(path, 'r') as f:
            users = json.load(f)

        original_count = len(users)
        # Filter out the user
        users = [user for user in users if user.get("username") != username]

        if len(users) == original_count:
            print(f"[!] User '{username}' not found.")
            return

        with open(path, 'w') as f:
            json.dump(users, f, indent=4)

        print(f"[-] User '{username}' has been deleted from {path}.")

    except Exception as e:
        print(f"[!] Error deleting user: {e}")
@app.route('/ftp_data')
def ftp_data():
    path = request.args.get('path', '')
    target_dir = os.path.join(FTP_ROOT, path)

    try:
        files = []
        for item in os.listdir(target_dir):
            full_path = os.path.join(target_dir, item)
            files.append({"name": item, "is_file": os.path.isfile(full_path)})
        return jsonify(files)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/upload_file', methods=['POST'])
def upload_file():
    try:
        file = request.files['file']
        filename = file.filename
        file_path = os.path.join(FTP_ROOT, filename)
        file.save(file_path)
        return jsonify({"status": "success", "file": filename}), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/delete_file', methods=['POST'])
def delete_file():
    data = request.json
    file_path = data.get('file')

    try:
        full_path = os.path.join(FTP_ROOT, file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            return jsonify({"status": "success", "file": file_path}), 200
        else:
            return jsonify({"status": "error", "error": "File not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500





@app.route('/download_file/<path:filename>')
def download_file(filename):
    try:
        # Decode URL-encoded characters (e.g., %20 to space)
        decoded_filename = unquote(filename)

        # Normalize path to ensure it uses forward slashes, even on Windows
        decoded_filename = decoded_filename.replace("\\", "/")

        # Join with the base directory to get the full path
        safe_path = os.path.join(FTP_ROOT, decoded_filename)

        # Log the safe path for debugging
        print(f"Requested file path: {safe_path}")

        # Ensure the file is within the FTP_ROOT directory (prevent path traversal)
        if not os.path.commonprefix([safe_path, FTP_ROOT]) == FTP_ROOT:
            print(f"Security check failed: {safe_path} is outside of {FTP_ROOT}")
            return jsonify({"status": "error", "error": "Invalid file path"}), 400

        # Check if the file exists and is a valid file (not a directory)
        if os.path.exists(safe_path) and os.path.isfile(safe_path):
            print(f"File found: {safe_path}")
            return send_from_directory(FTP_ROOT, decoded_filename, as_attachment=True)
        else:
            print(f"File not found: {safe_path}")
            return jsonify({"status": "error", "error": "File not found"}), 404

    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route('/add_user', methods=['POST'])
def add_user():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    homedir = data.get('homedir', FTP_ROOT)
    perm = data.get('perm', 'elradfmw')

    try:
        authorizer.add_user(username, password, homedir, perm=perm)
        save_user_to_file({
            "username": username,
            "password": password,
            "homedir": homedir,
            "perm": perm
        })
        return jsonify({"status": "success", "user": username})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route('/list_users', methods=['GET'])
def list_users():
    users = list(authorizer.user_table.keys())
    return jsonify({"users": users})


@app.route('/remove_user', methods=['POST'])
def remove_user():
    data = request.json
    username = data.get('username')
    try:
        authorizer.remove_user(username)
        delete_user_by_username(username)
        return jsonify({"status": "success", "user": username})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


# === Threads for Web + FTP ===
def run_ftp():
    while True:
        print(f"FTP server running on port {FTP_PORT}")
        server.serve_forever()
        with open("log.txt", "a") as file:
            file.write("FTP Server failed at: "+datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")


def run_web():
    while True:
        app.run(host='0.0.0.0', port=443, ssl_context=('cert.pem', 'key.pem'))


        with open("log.txt", "a") as file:
            file.write("Web Server failed at: "+datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")


if __name__ == '__main__':
    threading.Thread(target=run_ftp).start()
    threading.Thread(target=run_web).start()
