"""
Simple demo data generator that works without Flask-SQLAlchemy dependencies
"""

import sqlite3
import json
import random
from datetime import datetime, timedelta

# Try to import config, fall back to default if not available
try:
    from config import Config
except ImportError:
    Config = None

# Meal patterns with realistic calorie distributions
MEAL_PATTERNS = {
    'breakfast': {
        'calorie_range': (300, 600),
        'foods': [
            'Oatmeal', 'Greek Yogurt', 'Banana', 'Eggs', 'Whole Wheat Bread',
            'Avocado', 'Almonds', 'Organic Quinoa'
        ],
        'quantities': (80, 150)
    },
    'lunch': {
        'calorie_range': (400, 800),
        'foods': [
            'Chicken Breast', 'Brown Rice', 'Broccoli', 'Salmon Fillet', 'Sweet Potato',
            'Turkey Sandwich', 'Caesar Salad', 'Quinoa', 'Spinach'
        ],
        'quantities': (100, 200)
    },
    'dinner': {
        'calorie_range': (500, 900),
        'foods': [
            'Salmon Fillet', 'Chicken Breast', 'Brown Rice', 'Sweet Potato', 'Broccoli',
            'Spinach', 'Quinoa', 'Pizza Slice', 'Burger with Fries'
        ],
        'quantities': (120, 250)
    },
    'snack': {
        'calorie_range': (100, 300),
        'foods': [
            'Almonds', 'Banana', 'Greek Yogurt', 'Red Seedless Grapes', 
            'Dark Chocolate 85% Cacao', 'Avocado'
        ],
        'quantities': (30, 100)
    }
}

# Seasonal variations
SEASONAL_FOODS = {
    'winter': ['Campbell\'s Tomato Soup', 'Oatmeal', 'Sweet Potato'],
    'spring': ['Spinach', 'Broccoli', 'Salmon Fillet'],
    'summer': ['Red Seedless Grapes', 'Banana', 'Caesar Salad'],
    'autumn': ['Sweet Potato', 'Quinoa', 'Dark Chocolate 85% Cacao']
}

def get_season(date):
    """Get season based on date"""
    month = date.month
    if month in [12, 1, 2]:
        return 'winter'
    elif month in [3, 4, 5]:
        return 'spring'
    elif month in [6, 7, 8]:
        return 'summer'
    else:
        return 'autumn'

def get_database_path():
    """Get the database path from config or use default"""
    import os
    
    try:
        if Config and hasattr(Config, 'SQLALCHEMY_DATABASE_URI'):
            db_path = Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')
            # Ensure absolute path
            if not os.path.isabs(db_path):
                db_path = os.path.join('/home/ubuntu/food-planner-app', db_path)
            return db_path
    except Exception as e:
    
    # Always use absolute path
    default_path = os.path.abspath('/home/ubuntu/food-planner-app/instance/food_planner.db')
    return default_path

def select_realistic_food_for_meal(meal_type, available_foods, season):
    """Select a realistic food for the given meal type and season"""
    meal_foods = MEAL_PATTERNS[meal_type]['foods']
    seasonal_foods = SEASONAL_FOODS.get(season, [])
    
    # Prefer seasonal foods (30% chance)
    food_pool = meal_foods.copy()
    if random.random() < 0.3 and seasonal_foods:
        food_pool.extend(seasonal_foods)
    
    # Find matching foods in database
    matching_foods = []
    for food_id, food_name, nutrition_json in available_foods:
        for preferred_food in food_pool:
            if preferred_food.lower() in food_name.lower():
                matching_foods.append((food_id, food_name, nutrition_json))
                break
    
    # Fallback to any available food if no matches
    if not matching_foods:
        matching_foods = available_foods
    
    return random.choice(matching_foods)

def get_realistic_quantity_for_meal(meal_type, nutrition_json):
    """Get realistic quantity based on meal type and food nutrition"""
    base_range = MEAL_PATTERNS[meal_type]['quantities']
    
    # Parse nutrition data
    try:
        nutrition = json.loads(nutrition_json) if nutrition_json else {}
        calories_per_100g = nutrition.get('calories_per_100g', 200)
        calories_per_100g = float(calories_per_100g) if calories_per_100g is not None else 200
    except (ValueError, TypeError, json.JSONDecodeError):
        calories_per_100g = 200
    
    # Adjust based on calorie density
    if calories_per_100g > 500:  # High calorie foods (oils, nuts)
        return random.randint(15, 50)
    elif calories_per_100g > 300:  # Medium-high calorie foods
        return random.randint(50, 120)
    else:  # Lower calorie foods
        return random.randint(base_range[0], base_range[1])

def create_demo_data_with_path(user_id, db_path, months=6):
    """Create demo data using specified database path"""
    return _create_demo_data_internal(user_id, db_path, months)


def _create_demo_data_internal(user_id, db_path, months=6):
    """Internal function to create demo data"""
    
    # Try multiple times in case of database locks
    max_retries = 3
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(db_path, timeout=10.0)
            conn.execute('PRAGMA journal_mode=WAL')  # Enable WAL mode for better concurrency
            break
        except sqlite3.OperationalError as e:
            if attempt == max_retries - 1:
                return {
                    'success': False,
                    'error': f'Database connection failed after {max_retries} attempts: {str(e)}',
                    'message': 'Failed to create demo data - database unavailable'
                }
            import time
            time.sleep(0.5)  # Wait before retry
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        if 'food' not in tables:
            return {
                'success': False,
                'error': f'Food table not found. Available tables: {tables}',
                'message': 'Failed to create demo data - food table missing'
            }
        
        # Get available foods with nutrition data
        cursor.execute('SELECT id, name, nutrition_data FROM food WHERE nutrition_data IS NOT NULL')
        available_foods = cursor.fetchall()
        
        if not available_foods:
            return {
                'success': False,
                'error': 'No foods with nutrition data available',
                'message': 'Failed to create demo data - no foods available'
            }
        
        # Get user's calorie goal
        cursor.execute('SELECT daily_calorie_goal FROM user WHERE id = ?', (user_id,))
        user_data = cursor.fetchone()
        target_calories = user_data[0] if user_data else 2000
        
        # Generate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)
        
        logs_created = 0
        current_date = start_date
        total_calories = 0
        meal_counts = {}
        dates_with_logs = set()
        
        while current_date <= end_date:
            # 85% chance of logging on any given day
            if random.random() < 0.85:
                season = get_season(current_date)
                is_weekend = current_date.weekday() >= 5
                daily_logs = []
                
                # Breakfast (95% chance)
                if random.random() > 0.05:
                    food_id, food_name, nutrition_json = select_realistic_food_for_meal('breakfast', available_foods, season)
                    quantity = get_realistic_quantity_for_meal('breakfast', nutrition_json)
                    
                    breakfast_time = current_date.replace(
                        hour=random.randint(6, 9),
                        minute=random.randint(0, 59),
                        second=0,
                        microsecond=0
                    )
                    
                    daily_logs.append(('breakfast', food_id, quantity, breakfast_time))
                
                # Lunch (90% chance)
                if random.random() > 0.1:
                    food_id, food_name, nutrition_json = select_realistic_food_for_meal('lunch', available_foods, season)
                    quantity = get_realistic_quantity_for_meal('lunch', nutrition_json)
                    
                    lunch_time = current_date.replace(
                        hour=random.randint(11, 14),
                        minute=random.randint(0, 59),
                        second=0,
                        microsecond=0
                    )
                    
                    daily_logs.append(('lunch', food_id, quantity, lunch_time))
                
                # Dinner (98% chance)
                if random.random() > 0.02:
                    food_id, food_name, nutrition_json = select_realistic_food_for_meal('dinner', available_foods, season)
                    quantity = get_realistic_quantity_for_meal('dinner', nutrition_json)
                    
                    dinner_time = current_date.replace(
                        hour=random.randint(17, 21),
                        minute=random.randint(0, 59),
                        second=0,
                        microsecond=0
                    )
                    
                    daily_logs.append(('dinner', food_id, quantity, dinner_time))
                
                # Snacks (variable)
                snack_probability = 0.7 if is_weekend else 0.5
                num_snacks = random.choices([0, 1, 2], weights=[0.3, 0.6, 0.1])[0]
                
                for i in range(num_snacks):
                    if random.random() < snack_probability:
                        food_id, food_name, nutrition_json = select_realistic_food_for_meal('snack', available_foods, season)
                        quantity = get_realistic_quantity_for_meal('snack', nutrition_json)
                        
                        snack_hour = random.choice([10, 15, 20])
                        snack_time = current_date.replace(
                            hour=snack_hour,
                            minute=random.randint(0, 59),
                            second=0,
                            microsecond=0
                        )
                        
                        daily_logs.append(('snack', food_id, quantity, snack_time))
                
                # Insert all daily logs
                for meal_type, food_id, quantity, logged_at in daily_logs:
                    cursor.execute('''
                        INSERT INTO food_log (user_id, food_id, quantity, meal_type, logged_at, notes)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        user_id,
                        food_id,
                        quantity,
                        meal_type,
                        logged_at.isoformat(),
                        f'Demo data for {current_date.strftime("%B %d, %Y")}'
                    ))
                    
                    logs_created += 1
                    meal_counts[meal_type] = meal_counts.get(meal_type, 0) + 1
                    
                    # Calculate calories for statistics
                    try:
                        cursor.execute('SELECT nutrition_data FROM food WHERE id = ?', (food_id,))
                        food_nutrition = cursor.fetchone()
                        if food_nutrition and food_nutrition[0]:
                            nutrition = json.loads(food_nutrition[0])
                            calories_per_100g = float(nutrition.get('calories_per_100g', 0))
                            total_calories += (calories_per_100g * quantity) / 100
                    except:
                        pass
                
                if daily_logs:
                    dates_with_logs.add(current_date.date())
            
            current_date += timedelta(days=1)
        
        # Commit all changes
        conn.commit()
        
        # Calculate statistics
        unique_dates = len(dates_with_logs)
        avg_calories_per_day = round(total_calories / unique_dates) if unique_dates > 0 else 0
        
        return {
            'success': True,
            'logs_created': logs_created,
            'unique_dates': unique_dates,
            'avg_calories_per_day': avg_calories_per_day,
            'meal_breakdown': meal_counts,
            'date_range': f'{months} months',
            'message': f'Successfully created {logs_created} demo food logs across {unique_dates} days'
        }
        
    except Exception as e:
        conn.rollback()
        return {
            'success': False,
            'error': str(e),
            'message': f'Failed to create demo data: {str(e)}'
        }
    finally:
        conn.close()