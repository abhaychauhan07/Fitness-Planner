from flask import Flask, render_template, request, redirect, url_for, session, flash, g
import sqlite3, os, math
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from datetime import datetime, timedelta
from ml_recommender import FitnessRecommender
from dynamic_adjuster import DynamicAdjuster

load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET','dev_secret')

USE_MYSQL = os.environ.get('USE_MYSQL','false').lower() == 'true'
DB_PATH = os.path.join(os.path.dirname(__file__), 'data.db')

# Initialize ML components
ml_recommender = FitnessRecommender()
dynamic_adjuster = DynamicAdjuster()

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        # For demo we use sqlite fallback
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    with open(os.path.join(os.path.dirname(__file__), 'sql', 'sqlite_schema.sql'),'r') as f:
        db.executescript(f.read())
    # insert demo user if not exists
    cur = db.execute('SELECT * FROM users WHERE email = ?', ('demo@demo.com',))
    if not cur.fetchone():
        db.execute(
            'INSERT INTO users (name,email,password_hash,age,gender,height_cm,weight_kg,activity_level) '
            'VALUES (?,?,?,?,?,?,?,?)',
            (
                'Demo User',
                'demo@demo.com',
                'pbkdf2:sha256:260000$kQCLOQahH1s3iHDN$5e99b3e0ebdcb3ac48645dcb26a80c9d3e7209f67f1f31c9a2328e1f3aa2bca5',
                25,
                'Male',
                175,
                70,
                'Moderate'
            )
        )

def check_and_create_tables():
    """Check if new tables exist, create them if missing (migration)"""
    # Use direct connection, not Flask's g context (for startup use)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if workout_schedule table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='workout_schedule'")
        if not cursor.fetchone():
            print("Creating missing table: workout_schedule")
            cursor.execute('''
                CREATE TABLE workout_schedule (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    scheduled_date DATE,
                    workout_type TEXT,
                    duration_min INTEGER,
                    status TEXT DEFAULT 'pending',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
        
        # Check if challenges table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='challenges'")
        if not cursor.fetchone():
            print("Creating missing table: challenges")
            cursor.execute('''
                CREATE TABLE challenges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    description TEXT,
                    start_date DATE,
                    end_date DATE,
                    target_metric TEXT,
                    target_value REAL,
                    points_reward INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        
        # Check if user_challenges table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_challenges'")
        if not cursor.fetchone():
            print("Creating missing table: user_challenges")
            cursor.execute('''
                CREATE TABLE user_challenges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    challenge_id INTEGER,
                    progress_value REAL DEFAULT 0,
                    status TEXT DEFAULT 'active',
                    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (challenge_id) REFERENCES challenges(id) ON DELETE CASCADE
                )
            ''')
        
        conn.commit()
    except Exception as e:
        print(f"Error creating tables: {e}")
        conn.rollback()
    finally:
        conn.close()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method=='POST':
        name = request.form['name']; email = request.form['email']; password = request.form['password']
        db = get_db()
        if db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone():
            flash('Email already registered','danger'); return redirect(url_for('signup'))
        pwd_hash = generate_password_hash(password)
        db.execute('INSERT INTO users (name,email,password_hash) VALUES (?,?,?)',(name,email,pwd_hash))
        db.commit()
        flash('Account created. Please login.','success'); return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        email = request.form['email']; password = request.form['password']
        db = get_db(); row = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        if row and check_password_hash(row['password_hash'], password):
            session['user_id'] = row['id']; session['name'] = row['name']
            flash('Logged in','success'); return redirect(url_for('dashboard'))
        flash('Invalid credentials','danger'); return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear(); flash('Logged out','info'); return redirect(url_for('index'))

def ensure_tables():
    """Ensure all required tables exist (called once at startup)"""
    if os.path.exists(DB_PATH):
        try:
            check_and_create_tables()
            print("✅ Database tables verified/created successfully")
        except Exception as e:
            print(f"⚠️ Table check error: {e}")
            # Try again with direct connection
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                # Create challenges table if missing
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='challenges'")
                if not cursor.fetchone():
                    cursor.execute('''
                        CREATE TABLE challenges (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT,
                            description TEXT,
                            start_date DATE,
                            end_date DATE,
                            target_metric TEXT,
                            target_value REAL,
                            points_reward INTEGER,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                conn.commit()
                conn.close()
                print("✅ Missing tables created successfully")
            except Exception as e2:
                print(f"❌ Failed to create tables: {e2}")

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    db = get_db(); uid = session['user_id']
    user = db.execute('SELECT * FROM users WHERE id = ?', (uid,)).fetchone()
    workouts = db.execute('SELECT * FROM workout WHERE user_id = ? ORDER BY date DESC LIMIT 6', (uid,)).fetchall()
    diets = db.execute('SELECT * FROM diet WHERE user_id = ? ORDER BY date DESC LIMIT 6', (uid,)).fetchall()
    progress = db.execute('SELECT * FROM progress WHERE user_id = ? ORDER BY date DESC LIMIT 6', (uid,)).fetchall()
    community = db.execute('SELECT * FROM community WHERE user_id = ?', (uid,)).fetchone()
    # prepare stats for charts
    steps = db.execute('SELECT recorded_at, steps FROM wearabled WHERE user_id = ? ORDER BY recorded_at DESC LIMIT 7', (uid,)).fetchall()
    return render_template('dashboard.html', user=user, workouts=workouts, diets=diets, progress=progress, community=community, steps=steps)

@app.route('/edit_profile', methods=['GET','POST'])
def edit_profile():
    if 'user_id' not in session: return redirect(url_for('login'))
    db = get_db(); uid = session['user_id']
    
    if request.method == 'POST':
        # Get form data
        age = request.form.get('age')
        gender = request.form.get('gender')
        height_cm = request.form.get('height_cm')
        weight_kg = request.form.get('weight_kg')
        activity_level = request.form.get('activity_level')
        
        # Update user profile
        update_fields = []
        params = []
        
        if age:
            update_fields.append('age = ?')
            params.append(int(age))
        if gender:
            update_fields.append('gender = ?')
            params.append(gender)
        if height_cm:
            update_fields.append('height_cm = ?')
            params.append(int(height_cm))
        if weight_kg:
            update_fields.append('weight_kg = ?')
            params.append(float(weight_kg))
        if activity_level:
            update_fields.append('activity_level = ?')
            params.append(activity_level)
        
        if update_fields:
            params.append(uid)
            query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
            db.execute(query, params)
            db.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('No changes made', 'info')
    
    # GET request - show edit form
    user = db.execute('SELECT * FROM users WHERE id = ?', (uid,)).fetchone()
    return render_template('edit_profile.html', user=user)

@app.route('/add_workout', methods=['GET','POST'])
def add_workout():
    if 'user_id' not in session: return redirect(url_for('login'))
    if request.method=='POST':
        uid = session['user_id']; date = request.form['date']; wtype = request.form['workout_type']
        duration = int(request.form['duration'] or 0); calories = int(request.form['calories'] or 0); notes = request.form.get('notes','')
        db = get_db()
        db.execute('INSERT INTO workout (user_id,date,workout_type,duration_min,calories_burned,notes) VALUES (?,?,?,?,?,?)',
                   (uid,date,wtype,duration,calories,notes)); db.commit()
        flash('Workout added','success'); return redirect(url_for('dashboard'))
    return render_template('add_workout.html')

@app.route('/add_diet', methods=['GET','POST'])
def add_diet():
    if 'user_id' not in session: return redirect(url_for('login'))
    if request.method=='POST':
        uid = session['user_id']; date = request.form['date']; meal = request.form['meal_type']
        calories = int(request.form['calories'] or 0); protein = float(request.form['protein'] or 0)
        carbs = float(request.form['carbs'] or 0); fats = float(request.form['fats'] or 0); notes = request.form.get('notes','')
        db = get_db()
        db.execute('INSERT INTO diet (user_id,date,meal_type,calories,protein_g,carbs_g,fats_g,notes) VALUES (?,?,?,?,?,?,?,?)',
                   (uid,date,meal,calories,protein,carbs,fats,notes)); db.commit()
        flash('Diet entry added','success'); return redirect(url_for('dashboard'))
    return render_template('add_diet.html')

@app.route('/wearable', methods=['GET','POST'])
def wearable():
    if 'user_id' not in session: return redirect(url_for('login'))
    if request.method=='POST':
        uid = session['user_id']; recorded_at = request.form['recorded_at']; steps = int(request.form['steps'] or 0)
        hr = int(request.form['heart_rate'] or 0); sleep = float(request.form['sleep_hours'] or 0); calories = int(request.form['calories_burned'] or 0)
        db = get_db(); db.execute('INSERT INTO wearabled (user_id,recorded_at,steps,heart_rate,sleep_hours,calories_burned) VALUES (?,?,?,?,?,?)',
                                  (uid,recorded_at,steps,hr,sleep,calories)); db.commit()
        
        # Trigger automatic adjustment based on wearable data
        try:
            # Get recent sleep data
            sleep_data = db.execute('SELECT sleep_hours FROM wearabled WHERE user_id = ? AND sleep_hours > 0 ORDER BY recorded_at DESC LIMIT 7', (uid,)).fetchall()
            sleep_records = [{'sleep_hours': s['sleep_hours']} for s in sleep_data]
            sleep_quality = dynamic_adjuster.analyze_sleep_quality(sleep_records)
            
            # Get schedule
            schedule = db.execute('SELECT * FROM workout_schedule WHERE user_id = ? AND status = ? ORDER BY scheduled_date', (uid, 'pending')).fetchall()
            schedule_list = [dict(s) for s in schedule]
            
            # Get workouts
            workouts = db.execute('SELECT * FROM workout WHERE user_id = ? ORDER BY date DESC LIMIT 10', (uid,)).fetchall()
            workout_list = [dict(w) for w in workouts]
            
            # Auto-adjust if sleep quality is poor
            if sleep_quality.get('score', 1.0) < 0.6:
                user = db.execute('SELECT * FROM users WHERE id = ?', (uid,)).fetchone()
                user_dict = dict(user)
                
                adjustment = dynamic_adjuster.adjust_workout_schedule(
                    user_dict, {'skipped': [], 'adherence_rate': 1.0}, 
                    sleep_quality, schedule_list, {}
                )
                
                # Update next scheduled workout if adjustment recommended
                if adjustment.get('adjustments'):
                    next_schedule = db.execute('SELECT * FROM workout_schedule WHERE user_id = ? AND status = ? AND scheduled_date >= date("now") ORDER BY scheduled_date LIMIT 1', (uid, 'pending')).fetchone()
                    if next_schedule:
                        if 'reduce_intensity' in [a.get('type') for a in adjustment['adjustments']]:
                            new_duration = max(15, int(next_schedule['duration_min'] * 0.7))
                            db.execute('UPDATE workout_schedule SET duration_min = ? WHERE id = ?', (new_duration, next_schedule['id']))
                            db.commit()
                            flash(f"⚠️ Schedule adjusted: {adjustment['adjustments'][0].get('message', 'Workout intensity reduced due to poor sleep quality')}", 'info')
        except Exception as e:
            print(f"Adjustment error: {e}")  # Don't break if adjustment fails
        
        flash('Wearable data saved','success'); return redirect(url_for('dashboard'))
    return render_template('wearable.html')

@app.route('/recommendations')
def recommendations():
    if 'user_id' not in session: return redirect(url_for('login'))
    db = get_db(); uid = session['user_id']; user = db.execute('SELECT * FROM users WHERE id = ?', (uid,)).fetchone()
    user_dict = dict(user)
    
    # Get workout and diet history for ML training
    workouts = db.execute('SELECT * FROM workout WHERE user_id = ? ORDER BY date DESC LIMIT 50', (uid,)).fetchall()
    diets = db.execute('SELECT * FROM diet WHERE user_id = ? ORDER BY date DESC LIMIT 50', (uid,)).fetchall()
    workout_list = [dict(w) for w in workouts]
    diet_list = [dict(d) for d in diets]
    
    # Train ML models if we have enough data
    ml_used = False
    if len(workout_list) >= 3:
        ml_used = ml_recommender.train_models(workout_list, diet_list, user_dict)
    
    # Get recommendations (ML-based if trained, else fallback)
    if ml_used:
        # Get recent activity for prediction
        last_workout = workout_list[0] if workout_list else None
        recent_activity = {
            'days_since_last_workout': (datetime.now().date() - datetime.strptime(last_workout['date'], '%Y-%m-%d').date()).days if last_workout else 1,
            'last_workout_type': last_workout.get('workout_type') if last_workout else None
        }
        
        predicted_workout = ml_recommender.predict_workout_type(user_dict, recent_activity)
        maintenance_kcal = ml_recommender.predict_daily_calories(user_dict, 'maintenance')
        weight_loss_kcal = ml_recommender.predict_daily_calories(user_dict, 'weight_loss')
        weight_gain_kcal = ml_recommender.predict_daily_calories(user_dict, 'weight_gain')
    else:
        # Fallback to rule-based
        weight = user['weight_kg'] or 70
        activity = (user['activity_level'] or 'Moderate').lower()
        bmr = 10 * weight + 6.25 * (user['height_cm'] or 170) - 5 * (user['age'] or 25) + (10 if user['gender']=='Male' else -161)
        multiplier = {'sedentary':1.2,'light':1.375,'moderate':1.55,'active':1.725,'very active':1.9}.get(activity,1.55)
        maintenance_kcal = int(bmr * multiplier)
        weight_loss_kcal = max(1200, maintenance_kcal - 500)
        weight_gain_kcal = maintenance_kcal + 400
        predicted_workout = 'Running'  # Default
    
    suggestions = {
        'maintenance_kcal': maintenance_kcal,
        'weight_loss_kcal': weight_loss_kcal,
        'weight_gain_kcal': weight_gain_kcal,
        'protein_g_per_day': round(1.6 * (user['weight_kg'] or 70), 1),
        'predicted_workout': predicted_workout,
        'ml_used': ml_used
    }
    
    # Workout suggestions based on history
    recent = db.execute('SELECT workout_type,count(*) as cnt FROM workout WHERE user_id = ? GROUP BY workout_type ORDER BY cnt DESC LIMIT 3',(uid,)).fetchall()
    
    # Get dynamic adjustments info
    schedule = db.execute('SELECT * FROM workout_schedule WHERE user_id = ? ORDER BY scheduled_date', (uid,)).fetchall()
    schedule_list = [dict(s) for s in schedule]
    skipped = dynamic_adjuster.detect_skipped_workouts(schedule_list, workout_list)
    
    sleep_data = db.execute('SELECT sleep_hours FROM wearabled WHERE user_id = ? AND sleep_hours > 0 ORDER BY recorded_at DESC LIMIT 7', (uid,)).fetchall()
    sleep_records = [{'sleep_hours': s['sleep_hours']} for s in sleep_data]
    sleep_quality = dynamic_adjuster.analyze_sleep_quality(sleep_records) if sleep_data else {'quality': 'unknown', 'score': 0.8}
    
    return render_template('recommendations.html', user=user, suggestions=suggestions, recent=recent, 
                         skipped=skipped, sleep_quality=sleep_quality, ml_used=ml_used)

@app.route('/community')
def community():
    if 'user_id' not in session: return redirect(url_for('login'))
    # Ensure tables exist before querying
    try:
        check_and_create_tables()
    except:
        pass
    
    db=get_db(); uid=session['user_id']
    # leaderboard: top 10 by points
    leaderboard = db.execute('SELECT u.name,c.points FROM community c JOIN users u ON c.user_id = u.id ORDER BY c.points DESC LIMIT 10').fetchall()
    me = db.execute('SELECT * FROM community WHERE user_id = ?', (uid,)).fetchone()
    
    # Get active challenges (handle if table doesn't exist)
    try:
        active_challenges = db.execute('''
            SELECT c.*, uc.status as user_status, uc.progress_value 
            FROM challenges c 
            LEFT JOIN user_challenges uc ON c.id = uc.challenge_id AND uc.user_id = ?
            WHERE c.end_date >= date('now') 
            ORDER BY c.start_date DESC
        ''', (uid,)).fetchall()
        
        # Get user's challenges
        my_challenges = db.execute('''
            SELECT c.*, uc.progress_value, uc.status 
            FROM user_challenges uc 
            JOIN challenges c ON uc.challenge_id = c.id 
            WHERE uc.user_id = ? AND uc.status = 'active'
        ''', (uid,)).fetchall()
    except sqlite3.OperationalError as e:
        # If tables don't exist, create them and return empty lists
        check_and_create_tables()
        active_challenges = []
        my_challenges = []
    
    return render_template('community.html', leaderboard=leaderboard, me=me, 
                         active_challenges=active_challenges, my_challenges=my_challenges)

@app.route('/schedule')
def schedule():
    if 'user_id' not in session: return redirect(url_for('login'))
    db = get_db(); uid = session['user_id']
    
    # Get current schedule
    schedule_items = db.execute('''
        SELECT * FROM workout_schedule 
        WHERE user_id = ? 
        ORDER BY scheduled_date ASC, status
    ''', (uid,)).fetchall()
    
    # Get skipped workouts analysis
    workouts = db.execute('SELECT * FROM workout WHERE user_id = ? ORDER BY date DESC', (uid,)).fetchall()
    schedule_list = [dict(s) for s in schedule_items]
    workout_list = [dict(w) for w in workouts]
    skipped = dynamic_adjuster.detect_skipped_workouts(schedule_list, workout_list)
    
    # Get sleep quality
    sleep_data = db.execute('SELECT sleep_hours FROM wearabled WHERE user_id = ? AND sleep_hours > 0 ORDER BY recorded_at DESC LIMIT 7', (uid,)).fetchall()
    sleep_records = [{'sleep_hours': s['sleep_hours']} for s in sleep_data]
    sleep_quality = dynamic_adjuster.analyze_sleep_quality(sleep_records) if sleep_data else {'quality': 'unknown', 'score': 0.8}
    
    user = db.execute('SELECT * FROM users WHERE id = ?', (uid,)).fetchone()
    user_dict = dict(user)
    
    # Get adjustments
    adjustment = dynamic_adjuster.adjust_workout_schedule(
        user_dict, skipped, sleep_quality, schedule_list, {}
    )
    
    return render_template('schedule.html', schedule=schedule_items, skipped=skipped, 
                         sleep_quality=sleep_quality, adjustment=adjustment)

@app.route('/schedule/generate', methods=['POST'])
def generate_schedule():
    if 'user_id' not in session: return redirect(url_for('login'))
    db = get_db(); uid = session['user_id']
    user = db.execute('SELECT * FROM users WHERE id = ?', (uid,)).fetchone()
    user_dict = dict(user)
    
    # Generate weekly schedule
    weekly_schedule = dynamic_adjuster.generate_weekly_schedule(user_dict)
    
    # Clear existing pending schedules
    db.execute('DELETE FROM workout_schedule WHERE user_id = ? AND status = ?', (uid, 'pending'))
    
    # Insert new schedule
    for item in weekly_schedule:
        db.execute('''
            INSERT INTO workout_schedule (user_id, scheduled_date, workout_type, duration_min, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (uid, item['scheduled_date'], item['workout_type'], item['duration_min'], item['status']))
    
    db.commit()
    flash('Weekly schedule generated successfully!', 'success')
    return redirect(url_for('schedule'))

@app.route('/schedule/complete/<int:schedule_id>', methods=['POST'])
def complete_schedule(schedule_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    db = get_db(); uid = session['user_id']
    
    # Mark schedule as completed
    db.execute('UPDATE workout_schedule SET status = ? WHERE id = ? AND user_id = ?', 
               ('completed', schedule_id, uid))
    db.commit()
    
    # Award points
    community = db.execute('SELECT * FROM community WHERE user_id = ?', (uid,)).fetchone()
    if community:
        new_points = (community['points'] or 0) + 10
        db.execute('UPDATE community SET points = ? WHERE user_id = ?', (new_points, uid))
    else:
        db.execute('INSERT INTO community (user_id, points) VALUES (?, ?)', (uid, 10))
    db.commit()
    
    flash('Workout marked as completed! +10 points', 'success')
    return redirect(url_for('schedule'))

@app.route('/challenges')
def challenges():
    if 'user_id' not in session: return redirect(url_for('login'))
    db = get_db(); uid = session['user_id']
    
    # Get all active challenges
    all_challenges = db.execute('''
        SELECT c.*, 
               COUNT(DISTINCT uc.user_id) as participants,
               uc.status as user_status
        FROM challenges c
        LEFT JOIN user_challenges uc ON c.id = uc.challenge_id
        LEFT JOIN user_challenges my_uc ON c.id = my_uc.challenge_id AND my_uc.user_id = ?
        WHERE c.end_date >= date('now')
        GROUP BY c.id
        ORDER BY c.start_date DESC
    ''', (uid,)).fetchall()
    
    # Get user's active challenges
    my_challenges = db.execute('''
        SELECT c.*, uc.progress_value, uc.status 
        FROM user_challenges uc 
        JOIN challenges c ON uc.challenge_id = c.id 
        WHERE uc.user_id = ? AND uc.status = 'active'
    ''', (uid,)).fetchall()
    
    return render_template('challenges.html', challenges=all_challenges, my_challenges=my_challenges)

@app.route('/challenges/join/<int:challenge_id>', methods=['POST'])
def join_challenge(challenge_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    db = get_db(); uid = session['user_id']
    
    # Check if already joined
    existing = db.execute('SELECT * FROM user_challenges WHERE user_id = ? AND challenge_id = ?', 
                         (uid, challenge_id)).fetchone()
    if existing:
        flash('You are already part of this challenge!', 'info')
        return redirect(url_for('challenges'))
    
    # Join challenge
    db.execute('INSERT INTO user_challenges (user_id, challenge_id, status) VALUES (?, ?, ?)', 
               (uid, challenge_id, 'active'))
    db.commit()
    
    flash('Successfully joined challenge!', 'success')
    return redirect(url_for('challenges'))

@app.route('/challenges/create', methods=['GET', 'POST'])
def create_challenge():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    if request.method == 'POST':
        db = get_db()
        name = request.form['name']
        description = request.form['description']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        target_metric = request.form['target_metric']
        target_value = float(request.form['target_value'])
        points_reward = int(request.form['points_reward'])
        
        db.execute('''
            INSERT INTO challenges (name, description, start_date, end_date, target_metric, target_value, points_reward)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, description, start_date, end_date, target_metric, target_value, points_reward))
        db.commit()
        
        flash('Challenge created successfully!', 'success')
        return redirect(url_for('challenges'))
    
    return render_template('create_challenge.html')

# Simple route to seed demo data if needed (disabled by default)
@app.route('/seed_demo')
def seed_demo():
    return "Disabled"

if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        with open(os.path.join(os.path.dirname(__file__), 'sql', 'sqlite_schema.sql'),'r') as f:
            conn.executescript(f.read())
        # insert demo user and sample data
        pwd = 'db9f57e3dab2c039c93c6c0c7687f1f6b32d24f00c4d527f406e67a5145e8e3c'
        conn.execute("INSERT INTO users (name,email,password_hash,age,gender,height_cm,weight_kg,activity_level) VALUES (?,?,?,?,?,?,?,?)",
                     ('Demo User','demo@demo.com',pwd,25,'Male',175,70,'Moderate'))
        uid = conn.execute("SELECT id FROM users WHERE email = 'demo@demo.com'").fetchone()[0]
        conn.execute("INSERT INTO workout (user_id,date,workout_type,duration_min,calories_burned,notes) VALUES (?,?,?,?,?,?)",
                     (uid,'2025-11-15','Running',30,300,'Morning run'))
        conn.execute("INSERT INTO diet (user_id,date,meal_type,calories,protein_g,carbs_g,fats_g,notes) VALUES (?,?,?,?,?,?,?,?)",
                     (uid,'2025-11-16','Breakfast',450,25,50,12,'Oats and eggs'))
        conn.execute("INSERT INTO wearabled (user_id,recorded_at,steps,heart_rate,sleep_hours,calories_burned) VALUES (?,?,?,?,?,?)",
                     (uid,'2025-11-16 08:00:00',7000,72,7.5,500))
        conn.execute("INSERT INTO progress (user_id,date,weight_kg,bmi,notes) VALUES (?,?,?,?,?)",
                     (uid,'2025-11-01',70,22.9,'Start'))
        conn.execute("INSERT INTO community (user_id,points,badges,rank) VALUES (?,?,?,?)",(uid,320,'Consistent Runner',2))
        conn.commit(); conn.close()
        print('Initialized DB at', DB_PATH)
    else:
        # Database exists, check for missing tables (migration)
        ensure_tables()
    app.run(debug=True)
