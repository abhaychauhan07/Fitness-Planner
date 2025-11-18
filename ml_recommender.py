"""
ML-based Recommendation System for Personalized Fitness Planner
Uses scikit-learn for workout and diet recommendations
"""
import numpy as np
from datetime import datetime, timedelta

try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
    from sklearn.preprocessing import LabelEncoder
    from sklearn.model_selection import train_test_split
    import pandas as pd
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("Warning: scikit-learn not available. Using fallback recommendations.")


class FitnessRecommender:
    """ML-based recommendation system for fitness and diet plans"""
    
    def __init__(self):
        self.workout_model = None
        self.calorie_model = None
        self.workout_encoder = LabelEncoder() if ML_AVAILABLE else None
        self.is_trained = False
    
    def prepare_training_data(self, workout_data, diet_data, user_data):
        """
        Prepare training data from historical user data
        Args:
            workout_data: List of workout records
            diet_data: List of diet records  
            user_data: User profile data
        Returns:
            X, y for workout recommendations and calorie predictions
        """
        if not ML_AVAILABLE or not workout_data:
            return None, None, None, None
        
        # Prepare features from user data and history
        features = []
        workout_targets = []
        calorie_targets = []
        
        for i, workout in enumerate(workout_data):
            # Feature: user profile + recent activity
            user_features = [
                user_data.get('age', 25),
                user_data.get('weight_kg', 70),
                user_data.get('height_cm', 170),
                1 if user_data.get('gender') == 'Male' else 0,
            ]
            
            # Activity level encoding
            activity_map = {'sedentary': 1, 'light': 2, 'moderate': 3, 'active': 4, 'very active': 5}
            activity_level = user_data.get('activity_level', 'Moderate').lower()
            user_features.append(activity_map.get(activity_level, 3))
            
            # Recent workout frequency (days between workouts)
            if i > 0:
                prev_date = datetime.strptime(workout_data[i-1].get('date', workout_data[0].get('date')), '%Y-%m-%d')
                curr_date = datetime.strptime(workout.get('date'), '%Y-%m-%d')
                days_diff = (curr_date - prev_date).days
                user_features.append(days_diff)
            else:
                user_features.append(0)
            
            # Day of week
            workout_date = datetime.strptime(workout.get('date'), '%Y-%m-%d')
            user_features.append(workout_date.weekday())
            
            features.append(user_features)
            workout_targets.append(workout.get('workout_type', 'Running'))
            
            # Calorie target based on workout type and duration
            base_calories = workout.get('calories_burned', 200)
            calorie_targets.append(base_calories)
        
        # Match diet data for calorie prediction
        if diet_data:
            diet_features = []
            diet_calorie_targets = []
            
            for diet in diet_data[:min(len(features), len(diet_data))]:
                diet_feat = [
                    user_data.get('age', 25),
                    user_data.get('weight_kg', 70),
                    user_data.get('height_cm', 170),
                    1 if user_data.get('gender') == 'Male' else 0,
                    activity_map.get(activity_level, 3),
                ]
                diet_features.append(diet_feat)
                diet_calorie_targets.append(diet.get('calories', 500))
        
        return (np.array(features) if features else None, 
                workout_targets if workout_targets else None,
                np.array(diet_features) if diet_data and diet_features else None,
                diet_calorie_targets if diet_data and diet_calorie_targets else None)
    
    def train_models(self, workout_data, diet_data, user_data):
        """Train ML models on user's historical data"""
        if not ML_AVAILABLE:
            return False
        
        if not workout_data:
            return False
        
        try:
            X, workout_targets, X_diet, diet_targets = self.prepare_training_data(
                workout_data, diet_data, user_data
            )
            
            if X is None or len(X) < 3:  # Need at least 3 samples
                return False
            
            # Encode workout types
            if workout_targets:
                workout_targets_encoded = self.workout_encoder.fit_transform(workout_targets)
                
                # Train workout type classifier
                self.workout_model = RandomForestClassifier(n_estimators=50, random_state=42)
                self.workout_model.fit(X, workout_targets_encoded)
                
                # Train calorie predictor
                if X_diet is not None and len(X_diet) >= 3:
                    self.calorie_model = GradientBoostingRegressor(n_estimators=50, random_state=42)
                    self.calorie_model.fit(X_diet, diet_targets)
                
                self.is_trained = True
                return True
        except Exception as e:
            print(f"Error training models: {e}")
            return False
        
        return False
    
    def predict_workout_type(self, user_data, recent_activity=None):
        """
        Predict optimal workout type for user
        Args:
            user_data: User profile dict
            recent_activity: Recent workout history
        Returns:
            Recommended workout type
        """
        if not ML_AVAILABLE or not self.is_trained or not self.workout_model:
            # Fallback to rule-based
            return self._fallback_workout_recommendation(user_data, recent_activity)
        
        try:
            # Prepare features
            activity_map = {'sedentary': 1, 'light': 2, 'moderate': 3, 'active': 4, 'very active': 5}
            activity_level = user_data.get('activity_level', 'Moderate').lower()
            
            today = datetime.now()
            features = np.array([[
                user_data.get('age', 25),
                user_data.get('weight_kg', 70),
                user_data.get('height_cm', 170),
                1 if user_data.get('gender') == 'Male' else 0,
                activity_map.get(activity_level, 3),
                recent_activity.get('days_since_last_workout', 1) if recent_activity else 1,
                today.weekday()
            ]])
            
            # Predict
            prediction_encoded = self.workout_model.predict(features)[0]
            workout_type = self.workout_encoder.inverse_transform([prediction_encoded])[0]
            return workout_type
        except:
            return self._fallback_workout_recommendation(user_data, recent_activity)
    
    def predict_daily_calories(self, user_data, goal='maintenance'):
        """
        Predict daily calorie needs using ML
        Args:
            user_data: User profile dict
            goal: 'maintenance', 'weight_loss', or 'weight_gain'
        Returns:
            Recommended daily calories
        """
        if not ML_AVAILABLE or not self.is_trained or not self.calorie_model:
            # Fallback to BMR calculation
            return self._fallback_calorie_recommendation(user_data, goal)
        
        try:
            activity_map = {'sedentary': 1, 'light': 2, 'moderate': 3, 'active': 4, 'very active': 5}
            activity_level = user_data.get('activity_level', 'Moderate').lower()
            
            features = np.array([[
                user_data.get('age', 25),
                user_data.get('weight_kg', 70),
                user_data.get('height_cm', 170),
                1 if user_data.get('gender') == 'Male' else 0,
                activity_map.get(activity_level, 3),
            ]])
            
            base_calories = self.calorie_model.predict(features)[0]
            
            # Adjust based on goal
            if goal == 'weight_loss':
                return max(1200, int(base_calories - 500))
            elif goal == 'weight_gain':
                return int(base_calories + 400)
            else:
                return int(base_calories)
        except:
            return self._fallback_calorie_recommendation(user_data, goal)
    
    def _fallback_workout_recommendation(self, user_data, recent_activity=None):
        """Fallback rule-based workout recommendation"""
        activity = (user_data.get('activity_level') or 'Moderate').lower()
        
        # Simple rule-based logic
        if activity in ['sedentary', 'light']:
            workouts = ['Walking', 'Yoga', 'Cycling']
        elif activity == 'moderate':
            workouts = ['Running', 'Cycling', 'Swimming']
        else:
            workouts = ['Running', 'HIIT', 'Weightlifting']
        
        # If we have recent activity, try to vary
        if recent_activity and recent_activity.get('last_workout_type'):
            last_type = recent_activity['last_workout_type']
            workouts = [w for w in workouts if w != last_type]
        
        return workouts[0] if workouts else 'Running'
    
    def _fallback_calorie_recommendation(self, user_data, goal='maintenance'):
        """Fallback BMR-based calorie recommendation"""
        weight = user_data.get('weight_kg') or 70
        height = user_data.get('height_cm') or 170
        age = user_data.get('age') or 25
        gender = user_data.get('gender') or 'Male'
        activity = (user_data.get('activity_level') or 'Moderate').lower()
        
        # Mifflin-St Jeor BMR
        if gender == 'Male':
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161
        
        multiplier = {'sedentary': 1.2, 'light': 1.375, 'moderate': 1.55, 
                     'active': 1.725, 'very active': 1.9}.get(activity, 1.55)
        maintenance = int(bmr * multiplier)
        
        if goal == 'weight_loss':
            return max(1200, maintenance - 500)
        elif goal == 'weight_gain':
            return maintenance + 400
        return maintenance

