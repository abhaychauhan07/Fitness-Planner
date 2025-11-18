# 🚀 How to Run the Project - Step by Step Guide

## Prerequisites
- Python 3.7 or higher installed
- pip (Python package installer)

## Quick Start Commands

### **Option 1: Using Virtual Environment (Recommended)**

#### **For Windows:**
```bash
# Step 1: Navigate to project directory
cd "c:\Users\abhay\OneDrive - Graphic Era University\Abhay Chauhan E2 02\personalized_fitness_planner_v2"

# Step 2: Create virtual environment
python -m venv venv

# Step 3: Activate virtual environment
venv\Scripts\activate

# Step 4: Install dependencies
pip install -r requirements.txt

# Step 5: Run the application
python app.py
```

#### **For Linux/Mac:**
```bash
# Step 1: Navigate to project directory
cd personalized_fitness_planner_v2

# Step 2: Create virtual environment
python3 -m venv venv

# Step 3: Activate virtual environment
source venv/bin/activate

# Step 4: Install dependencies
pip install -r requirements.txt

# Step 5: Run the application
python app.py
```

### **Option 2: Direct Installation (Without Virtual Environment)**

#### **For Windows:**
```bash
# Navigate to project directory
cd "c:\Users\abhay\OneDrive - Graphic Era University\Abhay Chauhan E2 02\personalized_fitness_planner_v2"

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

#### **For Linux/Mac:**
```bash
# Navigate to project directory
cd personalized_fitness_planner_v2

# Install dependencies
pip3 install -r requirements.txt

# Run the application
python3 app.py
```

## 📋 What Happens When You Run

1. **Database Initialization**: The app will automatically create `data.db` (SQLite database) if it doesn't exist
2. **Demo Data**: Demo user and sample data will be created automatically
3. **Server Starts**: Flask development server starts on `http://127.0.0.1:5000`

## 🌐 Access the Application

After running `python app.py`, open your browser and go to:
```
http://127.0.0.1:5000
```

or

```
http://localhost:5000
```

## 🔑 Demo Login Credentials

- **Email**: `demo@demo.com`
- **Password**: `DemoPass123`

## ✅ Verify Installation

After installation, you should see output like:
```
Initialized DB at C:\Users\abhay\...\data.db
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

## 🛠️ Troubleshooting

### **If you get "pip not found" error:**
```bash
python -m pip install -r requirements.txt
```

### **If you get "Python not found" error:**
- Make sure Python is installed and added to PATH
- Try using `python3` instead of `python` on Linux/Mac
- Try using `py` instead of `python` on Windows

### **If you get module import errors:**
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### **If port 5000 is already in use:**
- Close other applications using port 5000, or
- Modify `app.py` line 449 to use a different port:
```python
app.run(debug=True, port=5001)
```

### **If database errors occur:**
- Delete `data.db` file (if exists) and restart the app
- The app will recreate it automatically

## 📦 Dependencies Installed

The following packages will be installed:
- Flask==2.2.5 (Web framework)
- Werkzeug==2.2.3 (Security utilities)
- python-dotenv==1.0.0 (Environment variables)
- pymysql==1.0.3 (MySQL connector - optional)
- scikit-learn==1.3.2 (ML algorithms)
- numpy==1.24.3 (Numerical computing)
- pandas==2.0.3 (Data analysis)

## 🎯 Quick Test

1. Run the app using commands above
2. Open http://127.0.0.1:5000 in browser
3. Click "Sign Up" to create a new account OR
4. Click "Login" and use demo credentials:
   - Email: `demo@demo.com`
   - Password: `DemoPass123`
5. Explore the dashboard and features!

## 🔄 Stopping the Server

Press `Ctrl + C` in the terminal to stop the Flask server.

## 📝 Notes

- The app uses SQLite by default (no additional setup needed)
- Database is automatically created on first run
- Demo data is automatically inserted
- Debug mode is enabled (auto-reloads on code changes)
- All ML features work automatically when you log 3+ workouts

