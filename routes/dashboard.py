from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from models import db, FoodLog, DailyPlan, AIRecommendation
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def main():
    today = date.today()
    
    # Get today's food logs
    today_logs = FoodLog.query.filter(
        and_(
            FoodLog.user_id == current_user.id,
            func.date(FoodLog.logged_at) == today
        )
    ).all()
    
    # Calculate today's nutrition
    total_calories = sum(log.get_calories() for log in today_logs)
    
    # Get recent AI recommendations
    recent_recommendations = AIRecommendation.query.filter_by(
        user_id=current_user.id,
        is_used=False
    ).order_by(AIRecommendation.created_at.desc()).limit(3).all()
    
    # Get this week's summary
    week_start = today - timedelta(days=today.weekday())
    week_logs = FoodLog.query.filter(
        and_(
            FoodLog.user_id == current_user.id,
            FoodLog.logged_at >= week_start
        )
    ).all()
    
    # Group logs by date for the week
    week_summary = {}
    for log in week_logs:
        log_date = log.logged_at.date()
        if log_date not in week_summary:
            week_summary[log_date] = {'calories': 0, 'meals': 0}
        week_summary[log_date]['calories'] += log.get_calories()
        week_summary[log_date]['meals'] += 1
    
    return render_template('dashboard/main.html',
                         today_logs=today_logs,
                         total_calories=total_calories,
                         calorie_goal=current_user.daily_calorie_goal,
                         recent_recommendations=recent_recommendations,
                         week_summary=week_summary,
                         today=today)

@dashboard_bp.route('/nutrition')
@login_required
def nutrition():
    # Get date range from query params
    days = request.args.get('days', 7, type=int)
    end_date = date.today()
    start_date = end_date - timedelta(days=days-1)
    
    # Get food logs for the period
    logs = FoodLog.query.filter(
        and_(
            FoodLog.user_id == current_user.id,
            func.date(FoodLog.logged_at) >= start_date,
            func.date(FoodLog.logged_at) <= end_date
        )
    ).all()
    
    # Aggregate nutrition data by date
    nutrition_data = {}
    for log in logs:
        log_date = log.logged_at.date().isoformat()
        if log_date not in nutrition_data:
            nutrition_data[log_date] = {
                'calories': 0,
                'protein': 0,
                'carbs': 0,
                'fat': 0,
                'fiber': 0,
                'sugar': 0,
                'sodium': 0
            }
        
        # Add this log's nutrition to the date
        calories = log.get_calories() or 0
        nutrition_data[log_date]['calories'] += calories
        
        # Get other nutrients
        nutrients = log.get_nutrients()
        for nutrient, value in nutrients.items():
            if nutrient in nutrition_data[log_date]:
                nutrition_data[log_date][nutrient] += value
    
    return render_template('dashboard/nutrition.html',
                         nutrition_data=nutrition_data,
                         start_date=start_date,
                         end_date=end_date,
                         days=days)

@dashboard_bp.route('/meal-planner')
@login_required
def meal_planner():
    # Get the requested date or default to today
    requested_date = request.args.get('date')
    if requested_date:
        try:
            plan_date = datetime.strptime(requested_date, '%Y-%m-%d').date()
        except ValueError:
            plan_date = date.today()
    else:
        plan_date = date.today()
    
    # Get existing plan for this date
    existing_plan = DailyPlan.query.filter_by(
        user_id=current_user.id,
        date=plan_date
    ).first()
    
    # Get actual logged foods for this date
    logged_foods = FoodLog.query.filter(
        and_(
            FoodLog.user_id == current_user.id,
            func.date(FoodLog.logged_at) == plan_date
        )
    ).all()
    
    # Group logged foods by meal type
    logged_by_meal = {}
    for log in logged_foods:
        if log.meal_type not in logged_by_meal:
            logged_by_meal[log.meal_type] = []
        logged_by_meal[log.meal_type].append(log)
    
    return render_template('dashboard/meal_planner.html',
                         plan_date=plan_date,
                         existing_plan=existing_plan,
                         logged_by_meal=logged_by_meal,
                         meal_types=['breakfast', 'lunch', 'dinner', 'snack'])

@dashboard_bp.route('/ai-recommendations')
@login_required
def ai_recommendations():
    # Get recommendations for the user, excluding thumbs down (-1 rating)
    # Include NULL ratings (no rating yet) and thumbs up (1 rating)
    recommendations = AIRecommendation.query.filter(
        AIRecommendation.user_id == current_user.id,
        or_(AIRecommendation.rating.is_(None), AIRecommendation.rating == 1)
    ).order_by(AIRecommendation.created_at.desc()).limit(20).all()
    
    return render_template('dashboard/ai_recommendations.html',
                         recommendations=recommendations)

@dashboard_bp.route('/analytics')
@login_required
def analytics():
    # Get data for the last 30 days
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    # Get food logs for analytics
    logs = FoodLog.query.filter(
        and_(
            FoodLog.user_id == current_user.id,
            func.date(FoodLog.logged_at) >= start_date
        )
    ).all()
    
    # Analyze meal patterns
    meal_patterns = {}
    daily_calories = {}
    
    for log in logs:
        log_date = log.logged_at.date()
        meal_type = log.meal_type
        
        # Track meal patterns
        if meal_type not in meal_patterns:
            meal_patterns[meal_type] = 0
        meal_patterns[meal_type] += 1
        
        # Track daily calories
        if log_date not in daily_calories:
            daily_calories[log_date] = 0
        daily_calories[log_date] += log.get_calories()
    
    # Calculate averages
    total_days = len(daily_calories)
    avg_daily_calories = sum(daily_calories.values()) / total_days if total_days > 0 else 0
    
    # Prepare chart data
    chart_data = {
        'dates': [d.isoformat() for d in sorted(daily_calories.keys())],
        'calories': [daily_calories[d] for d in sorted(daily_calories.keys())],
        'goal': [current_user.daily_calorie_goal] * len(daily_calories)
    }
    
    return render_template('dashboard/analytics.html',
                         meal_patterns=meal_patterns,
                         avg_daily_calories=avg_daily_calories,
                         chart_data=chart_data,
                         calorie_goal=current_user.daily_calorie_goal,
                         total_days=total_days)