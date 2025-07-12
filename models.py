from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    auth0_user_id = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    picture_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # User preferences
    daily_calorie_goal = db.Column(db.Integer, default=2000)
    dietary_restrictions = db.Column(db.Text)  # JSON string
    preferred_cuisine = db.Column(db.String(100))
    
    # Relationships
    food_logs = db.relationship('FoodLog', backref='user', lazy='dynamic')
    daily_plans = db.relationship('DailyPlan', backref='user', lazy='dynamic')
    ai_recommendations = db.relationship('AIRecommendation', backref='user', lazy='dynamic')
    
    @classmethod
    def get_by_auth0_id(cls, auth0_user_id):
        return cls.query.filter_by(auth0_user_id=auth0_user_id).first()
    
    @classmethod
    def create_from_auth0(cls, auth0_user_info):
        user = cls(
            auth0_user_id=auth0_user_info['sub'],
            email=auth0_user_info['email'],
            name=auth0_user_info.get('name', auth0_user_info['email']),
            picture_url=auth0_user_info.get('picture')
        )
        return user
    
    def set_dietary_restrictions(self, restrictions_list):
        self.dietary_restrictions = json.dumps(restrictions_list)
    
    def get_dietary_restrictions(self):
        if self.dietary_restrictions:
            return json.loads(self.dietary_restrictions)
        return []
    
    def __repr__(self):
        return f'<User {self.name} ({self.email})>'

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
        
        # Ensure calories_per_100g is numeric
        try:
            calories_per_100g = float(calories_per_100g) if calories_per_100g is not None else 0
        except (ValueError, TypeError):
            calories_per_100g = 0
            
        return (calories_per_100g * self.quantity) / 100
    
    def get_nutrients(self):
        food_nutrition = self.food.get_nutrition_data()
        nutrients = {}
        for nutrient, value_per_100g in food_nutrition.items():
            try:
                # Convert to float and calculate based on quantity
                numeric_value = float(value_per_100g) if value_per_100g is not None else 0
                nutrients[nutrient] = (numeric_value * self.quantity) / 100
            except (ValueError, TypeError):
                # Skip non-numeric values
                continue
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
    rating = db.Column(db.Integer)  # 1 for thumbs up, -1 for thumbs down, None for no rating
    
    def set_context_data(self, context_dict):
        self.context_data = json.dumps(context_dict)
    
    def get_context_data(self):
        if self.context_data:
            return json.loads(self.context_data)
        return {}
    
    def __repr__(self):
        return f'<AIRecommendation {self.recommendation_type} for {self.user.username}>'