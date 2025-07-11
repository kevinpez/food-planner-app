from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # User preferences
    daily_calorie_goal = db.Column(db.Integer, default=2000)
    dietary_restrictions = db.Column(db.Text)  # JSON string
    preferred_cuisine = db.Column(db.String(100))
    
    # Relationships
    food_logs = db.relationship('FoodLog', backref='user', lazy='dynamic')
    daily_plans = db.relationship('DailyPlan', backref='user', lazy='dynamic')
    ai_recommendations = db.relationship('AIRecommendation', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def set_dietary_restrictions(self, restrictions_list):
        self.dietary_restrictions = json.dumps(restrictions_list)
    
    def get_dietary_restrictions(self):
        if self.dietary_restrictions:
            return json.loads(self.dietary_restrictions)
        return []
    
    def __repr__(self):
        return f'<User {self.username}>'

class Food(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    upc_code = db.Column(db.String(20), unique=True, nullable=True)
    name = db.Column(db.String(200), nullable=False)
    brand = db.Column(db.String(100))
    ingredients = db.Column(db.Text)
    nutrition_data = db.Column(db.Text)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    food_logs = db.relationship('FoodLog', backref='food', lazy='dynamic')
    
    def set_nutrition_data(self, nutrition_dict):
        self.nutrition_data = json.dumps(nutrition_dict)
    
    def get_nutrition_data(self):
        if self.nutrition_data:
            return json.loads(self.nutrition_data)
        return {}
    
    def get_calories_per_100g(self):
        nutrition = self.get_nutrition_data()
        return nutrition.get('calories_per_100g', 0)
    
    def __repr__(self):
        return f'<Food {self.name}>'

class FoodLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    food_id = db.Column(db.Integer, db.ForeignKey('food.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)  # in grams
    meal_type = db.Column(db.String(20), nullable=False)  # breakfast, lunch, dinner, snack
    logged_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    
    def get_calories(self):
        food_nutrition = self.food.get_nutrition_data()
        calories_per_100g = food_nutrition.get('calories_per_100g', 0)
        return (calories_per_100g * self.quantity) / 100
    
    def get_nutrients(self):
        food_nutrition = self.food.get_nutrition_data()
        nutrients = {}
        for nutrient, value_per_100g in food_nutrition.items():
            if isinstance(value_per_100g, (int, float)):
                nutrients[nutrient] = (value_per_100g * self.quantity) / 100
        return nutrients
    
    def __repr__(self):
        return f'<FoodLog {self.food.name} - {self.quantity}g>'

class DailyPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    meals_planned = db.Column(db.Text)  # JSON string
    nutritional_goals = db.Column(db.Text)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_meals_planned(self, meals_dict):
        self.meals_planned = json.dumps(meals_dict)
    
    def get_meals_planned(self):
        if self.meals_planned:
            return json.loads(self.meals_planned)
        return {}
    
    def set_nutritional_goals(self, goals_dict):
        self.nutritional_goals = json.dumps(goals_dict)
    
    def get_nutritional_goals(self):
        if self.nutritional_goals:
            return json.loads(self.nutritional_goals)
        return {}
    
    def __repr__(self):
        return f'<DailyPlan {self.user.username} - {self.date}>'

class AIRecommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recommendation_type = db.Column(db.String(50), nullable=False)  # meal, snack, alternative
    recommendation_text = db.Column(db.Text, nullable=False)
    context_data = db.Column(db.Text)  # JSON string with context used for recommendation
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_used = db.Column(db.Boolean, default=False)
    
    def set_context_data(self, context_dict):
        self.context_data = json.dumps(context_dict)
    
    def get_context_data(self):
        if self.context_data:
            return json.loads(self.context_data)
        return {}
    
    def __repr__(self):
        return f'<AIRecommendation {self.recommendation_type} for {self.user.username}>'