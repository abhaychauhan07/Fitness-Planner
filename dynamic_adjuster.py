"""
Dynamic Schedule Adjustment System
Automatically adjusts workout and diet plans based on user behavior, 
sleep patterns, and adherence
"""
from datetime import datetime, timedelta
from collections import defaultdict


class DynamicAdjuster:
    """Handles automatic adjustment of workout schedules and diet plans"""
    
    def __init__(self):
        self.min_sleep_hours = 7.0  # Minimum recommended sleep
        self.max_sleep_hours = 9.0  # Maximum recommended sleep
    
    def analyze_sleep_quality(self, sleep_data):
        """
        Analyze sleep quality from wearable data
        Args:
            sleep_data: List of sleep records with sleep_hours
        Returns:
            dict with sleep_quality score and recommendations
        """
        if not sleep_data:
            return {'quality': 'unknown', 'score': 0.5, 'recommendation': 'No sleep data available'}
        
        # Get recent sleep data (last 7 days)
        recent_sleep = [s.get('sleep_hours', 0) for s in sleep_data[-7:]]
        
        if not recent_sleep:
            return {'quality': 'unknown', 'score': 0.5}
        
        avg_sleep = sum(recent_sleep) / len(recent_sleep)
        latest_sleep = recent_sleep[-1] if recent_sleep else 0
        
        # Calculate sleep quality score (0-1)
        if self.min_sleep_hours <= avg_sleep <= self.max_sleep_hours:
            quality_score = 1.0
            quality = 'excellent'
        elif avg_sleep >= 6.0 and avg_sleep < self.min_sleep_hours:
            quality_score = 0.7
            quality = 'moderate'
        elif avg_sleep >= self.max_sleep_hours and avg_sleep <= 10.0:
            quality_score = 0.8
            quality = 'good'
        elif avg_sleep < 6.0:
            quality_score = 0.3
            quality = 'poor'
        else:
            quality_score = 0.5
            quality = 'irregular'
        
        # Adjust score based on latest sleep
        if latest_sleep < 6.0:
            quality_score *= 0.8
            quality = 'poor'
        
        # Generate recommendations
        if quality_score < 0.6:
            recommendation = 'Consider reducing workout intensity today. Prioritize rest and recovery.'
        elif quality_score < 0.8:
            recommendation = 'Moderate intensity workout recommended. Ensure adequate hydration.'
        else:
            recommendation = 'Good sleep quality. You can proceed with planned workout intensity.'
        
        return {
            'quality': quality,
            'score': quality_score,
            'avg_sleep': round(avg_sleep, 1),
            'latest_sleep': round(latest_sleep, 1),
            'recommendation': recommendation
        }
    
    def detect_skipped_workouts(self, schedule_data, workout_data):
        """
        Detect workouts that were scheduled but not completed
        Args:
            schedule_data: List of scheduled workouts
            workout_data: List of completed workouts
        Returns:
            dict with skipped workouts and adherence rate
        """
        if not schedule_data:
            return {'skipped': [], 'adherence_rate': 1.0, 'total_scheduled': 0}
        
        # Get workout dates
        completed_dates = set()
        for workout in workout_data:
            workout_date = workout.get('date')
            if workout_date:
                completed_dates.add(workout_date)
        
        # Find skipped workouts
        skipped = []
        today = datetime.now().date()
        
        for schedule in schedule_data:
            scheduled_date = datetime.strptime(schedule.get('scheduled_date'), '%Y-%m-%d').date()
            status = schedule.get('status', 'pending')
            
            # Check if workout was skipped (past date, not completed, status still pending)
            if scheduled_date < today and status == 'pending' and str(scheduled_date) not in completed_dates:
                skipped.append({
                    'id': schedule.get('id'),
                    'date': str(scheduled_date),
                    'workout_type': schedule.get('workout_type'),
                    'days_ago': (today - scheduled_date).days
                })
        
        total_scheduled = len(schedule_data)
        completed_count = len([s for s in schedule_data if s.get('status') == 'completed'])
        adherence_rate = completed_count / total_scheduled if total_scheduled > 0 else 1.0
        
        return {
            'skipped': skipped,
            'adherence_rate': round(adherence_rate, 2),
            'total_scheduled': total_scheduled,
            'completed_count': completed_count
        }
    
    def adjust_workout_schedule(self, user_data, skipped_workouts, sleep_quality, 
                                current_schedule, recent_activity):
        """
        Automatically adjust workout schedule based on adherence and sleep
        Args:
            user_data: User profile
            skipped_workouts: Result from detect_skipped_workouts
            sleep_quality: Result from analyze_sleep_quality
            current_schedule: List of upcoming scheduled workouts
            recent_activity: Recent workout history
        Returns:
            dict with adjustments and recommendations
        """
        adjustments = []
        recommendations = []
        
        adherence_rate = skipped_workouts.get('adherence_rate', 1.0)
        sleep_score = sleep_quality.get('score', 0.8)
        
        # If adherence is low, reduce frequency
        if adherence_rate < 0.7:
            adjustments.append({
                'type': 'reduce_frequency',
                'message': 'Low adherence detected. Reducing workout frequency by 20%.',
                'adjustment': -0.2
            })
            recommendations.append('Consider scheduling fewer workouts per week to improve consistency.')
        
        # If sleep quality is poor, reduce intensity
        if sleep_score < 0.6:
            adjustments.append({
                'type': 'reduce_intensity',
                'message': f"Poor sleep quality ({sleep_quality.get('quality')}). Reducing workout intensity.",
                'adjustment': -0.3
            })
            recommendations.append(sleep_quality.get('recommendation', ''))
        
        # If user has been very active, allow recovery
        if recent_activity:
            days_since_last = recent_activity.get('days_since_last_workout', 0)
            if days_since_last < 1:
                adjustments.append({
                    'type': 'add_recovery',
                    'message': 'Recent activity detected. Adding rest day.',
                    'adjustment': 'rest_day'
                })
                recommendations.append('Consider a rest day or light activity (yoga, walking).')
        
        # Adjust upcoming schedule
        modified_schedule = []
        for schedule in current_schedule:
            scheduled_date = datetime.strptime(schedule.get('scheduled_date'), '%Y-%m-%d').date()
            today = datetime.now().date()
            
            # Only adjust future workouts
            if scheduled_date >= today:
                modified = schedule.copy()
                
                # Apply intensity reduction if sleep is poor
                if sleep_score < 0.6:
                    duration = schedule.get('duration_min', 30)
                    modified['duration_min'] = max(15, int(duration * 0.7))
                    modified['note'] = 'Intensity reduced due to poor sleep quality'
                
                # Convert to rest day if needed
                if adjustments and any(a.get('adjustment') == 'rest_day' for a in adjustments):
                    if scheduled_date == today + timedelta(days=1):
                        modified['workout_type'] = 'Rest Day'
                        modified['duration_min'] = 0
                        modified['note'] = 'Recovery day recommended'
                
                modified_schedule.append(modified)
            else:
                modified_schedule.append(schedule)
        
        return {
            'adjustments': adjustments,
            'recommendations': recommendations,
            'modified_schedule': modified_schedule,
            'adherence_rate': adherence_rate,
            'sleep_score': sleep_score
        }
    
    def adjust_diet_plan(self, user_data, activity_level, sleep_quality, current_diet):
        """
        Adjust diet plan based on activity and sleep
        Args:
            user_data: User profile
            activity_level: Recent activity level (from wearable data)
            sleep_quality: Sleep quality analysis
            current_diet: Current diet recommendations
        Returns:
            Adjusted diet plan
        """
        base_calories = current_diet.get('maintenance_kcal', 2000)
        adjusted = current_diet.copy()
        
        sleep_score = sleep_quality.get('score', 0.8)
        
        # If sleep is poor, reduce calorie recommendation slightly
        if sleep_score < 0.6:
            adjusted['maintenance_kcal'] = int(base_calories * 0.95)
            adjusted['adjustment_note'] = 'Calories reduced by 5% due to poor sleep quality'
        
        # Adjust protein based on activity
        if activity_level:
            steps = activity_level.get('avg_steps', 0)
            if steps > 10000:
                # High activity - increase protein
                protein_multiplier = 2.0  # g per kg bodyweight
            elif steps < 5000:
                # Low activity - normal protein
                protein_multiplier = 1.6
            else:
                protein_multiplier = 1.8
            
            weight = user_data.get('weight_kg', 70)
            adjusted['protein_g_per_day'] = round(protein_multiplier * weight, 1)
        
        return adjusted
    
    def generate_weekly_schedule(self, user_data, preferences=None):
        """
        Generate a weekly workout schedule
        Args:
            user_data: User profile
            preferences: User workout preferences
        Returns:
            List of scheduled workouts for the week
        """
        today = datetime.now().date()
        schedule = []
        
        # Default workout types based on activity level
        activity = (user_data.get('activity_level') or 'Moderate').lower()
        if activity in ['sedentary', 'light']:
            workout_types = ['Walking', 'Yoga', 'Cycling']
            frequency = 3  # 3 days per week
        elif activity == 'moderate':
            workout_types = ['Running', 'Cycling', 'Swimming', 'Weightlifting']
            frequency = 4  # 4 days per week
        else:
            workout_types = ['Running', 'HIIT', 'Weightlifting', 'Cycling']
            frequency = 5  # 5 days per week
        
        # Schedule workouts throughout the week
        days_scheduled = 0
        day_offset = 0
        
        while days_scheduled < frequency and day_offset < 7:
            scheduled_date = today + timedelta(days=day_offset)
            day_of_week = scheduled_date.weekday()
            
            # Avoid scheduling on consecutive days for beginners
            if activity in ['sedentary', 'light'] and days_scheduled > 0:
                day_offset += 1  # Skip a day
                continue
            
            workout_type = workout_types[days_scheduled % len(workout_types)]
            
            # Set duration based on workout type
            duration_map = {
                'Walking': 30,
                'Yoga': 45,
                'Cycling': 40,
                'Running': 35,
                'Swimming': 40,
                'Weightlifting': 45,
                'HIIT': 30
            }
            duration = duration_map.get(workout_type, 30)
            
            schedule.append({
                'scheduled_date': str(scheduled_date),
                'workout_type': workout_type,
                'duration_min': duration,
                'status': 'pending'
            })
            
            days_scheduled += 1
            day_offset += 1
        
        return schedule

