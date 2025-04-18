# PythonFTPServer

---

### 🚀 Getting Started

1. **Clone or Download the Repository**  
   Download this repository to your local machine.

2. **Open a Terminal**  
   Navigate to the project directory in your terminal.

3. **Install Dependencies**  
   Run the following command to install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

---


### 🖥️ Run the Server

Start the server by running:

```bash
python main.py
```

Press `Ctrl + C` to stop the server.

---

### 🔐 Updating Admin Panel Credentials

To change the default admin username and password:

1. Open the project directory in your terminal.
2. Run the following command, replacing `newuser` and `newpass` with your desired credentials:

```bash
sed -i "s/if username == 'admin' and password == 'admin':/if username == 'newuser' and password == 'newpass':/" main.py
```

This will update the credentials directly in `main.py`.  
Make sure to restart the server for changes to take effect.

Sure — here’s a clean and simple **Credits** section you can add to your README:

---

### 🙌 Credits

Developed by **g3orgeH**

---
