-- MySQL dump for Personalized Fitness Nutrition Planner (Option B)
CREATE DATABASE IF NOT EXISTS fitness_planner;
USE fitness_planner;

DROP TABLE IF EXISTS Community;
DROP TABLE IF EXISTS Progress;
DROP TABLE IF EXISTS WearableData;
DROP TABLE IF EXISTS Diet;
DROP TABLE IF EXISTS Workout;
DROP TABLE IF EXISTS UserTable;

CREATE TABLE UserTable (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(150) UNIQUE,
    password_hash VARCHAR(255),
    age INT,
    gender VARCHAR(20),
    height_cm INT,
    weight_kg FLOAT,
    activity_level VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Workout (
    workout_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    date DATE,
    workout_type VARCHAR(100),
    duration_min INT,
    calories_burned INT,
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES UserTable(user_id) ON DELETE CASCADE
);

CREATE TABLE Diet (
    diet_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    date DATE,
    meal_type VARCHAR(50),
    calories INT,
    protein_g FLOAT,
    carbs_g FLOAT,
    fats_g FLOAT,
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES UserTable(user_id) ON DELETE CASCADE
);

CREATE TABLE WearableData (
    wearable_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    recorded_at DATETIME,
    steps INT,
    heart_rate INT,
    sleep_hours FLOAT,
    calories_burned INT,
    FOREIGN KEY (user_id) REFERENCES UserTable(user_id) ON DELETE CASCADE
);

CREATE TABLE Progress (
    progress_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    date DATE,
    weight_kg FLOAT,
    bmi FLOAT,
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES UserTable(user_id) ON DELETE CASCADE
);

CREATE TABLE Community (
    community_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    points INT DEFAULT 0,
    badges VARCHAR(255),
    rank INT DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES UserTable(user_id) ON DELETE CASCADE
);

CREATE TABLE workout_schedule (
    schedule_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    scheduled_date DATE,
    workout_type VARCHAR(100),
    duration_min INT,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES UserTable(user_id) ON DELETE CASCADE
);

CREATE TABLE challenges (
    challenge_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    description TEXT,
    start_date DATE,
    end_date DATE,
    target_metric VARCHAR(50),
    target_value FLOAT,
    points_reward INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_challenges (
    user_challenge_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    challenge_id INT,
    progress_value FLOAT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES UserTable(user_id) ON DELETE CASCADE,
    FOREIGN KEY (challenge_id) REFERENCES challenges(challenge_id) ON DELETE CASCADE
);

-- sample user
INSERT INTO UserTable (name, email, password_hash, age, gender, height_cm, weight_kg, activity_level)
VALUES ('Demo User','demo@demo.com','<hashed_password_here>',25,'Male',175,70,'Moderate');

-- sample related data
INSERT INTO Workout (user_id, date, workout_type, duration_min, calories_burned, notes) VALUES
(1,'2025-11-15','Running',30,300,'Morning run'),
(1,'2025-11-16','Strength',45,400,'Gym session');

INSERT INTO Diet (user_id, date, meal_type, calories, protein_g, carbs_g, fats_g, notes) VALUES
(1,'2025-11-16','Breakfast',450,25,50,12,'Oats and eggs'),
(1,'2025-11-16','Lunch',700,40,80,20,'Rice and chicken');

INSERT INTO WearableData (user_id, recorded_at, steps, heart_rate, sleep_hours, calories_burned) VALUES
(1,'2025-11-16 08:00:00',7000,72,7.5,500);

INSERT INTO Progress (user_id, date, weight_kg, bmi, notes) VALUES
(1,'2025-11-01',70,22.9,'Starting point');

INSERT INTO Community (user_id, points, badges, rank) VALUES
(1,320,'Consistent Runner,Top5',2);
