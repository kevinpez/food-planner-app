from flask import Blueprint, request, jsonify
from flask_wtf.csrf import validate_csrf, ValidationError
from models import db, Food, FoodLog, AIRecommendation
from services.nutrition_api import search_food_by_upc, search_food_by_name
from services.ai_service import get_meal_recommendation
from services.auth0_service import requires_auth, get_current_user
from datetime import datetime

api_bp = Blueprint('api', __name__)

@api_bp.route('/food/search-upc/<upc>')
@requires_auth
def search_upc(upc):
    current_user = get_current_user()
    try:
        # First check if we have this UPC in our database
        food = Food.query.filter_by(upc_code=upc).first()
        
        if food:
            return jsonify({
                'success': True,
                'food': {
                    'id': food.id,
                    'name': food.name,
                    'brand': food.brand,
                    'upc_code': food.upc_code,
                    'ingredients': food.ingredients,
                    'nutrition_data': food.get_nutrition_data()
                }
            })
        
        # If not found locally, search external API
        external_food = search_food_by_upc(upc)
        if external_food:
            return jsonify({
                'success': True,
                'food': {
                    'id': external_food.id,
                    'name': external_food.name,
                    'brand': external_food.brand,
                    'upc_code': external_food.upc_code,
                    'ingredients': external_food.ingredients,
                    'nutrition_data': external_food.get_nutrition_data()
                }
            })
        
        return jsonify({
            'success': False,
            'message': 'Food not found for this UPC code'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error searching for UPC: {str(e)}'
        }), 500

@api_bp.route('/food/search-name')
@requires_auth
def search_name():
    current_user = get_current_user()
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({
            'success': False,
            'message': 'Search query is required'
        })
    
    try:
        # Search local database first
        foods = Food.query.filter(
            Food.name.ilike(f'%{query}%')
        ).limit(10).all()
        
        # If no local results, search external API
        if not foods:
            foods = search_food_by_name(query)
        
        food_list = []
        for food in foods:
            food_list.append({
                'id': food.id,
                'name': food.name,
                'brand': food.brand,
                'upc_code': food.upc_code,
                'ingredients': food.ingredients,
                'nutrition_data': food.get_nutrition_data()
            })
        
        return jsonify({
            'success': True,
            'foods': food_list
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error searching for foods: {str(e)}'
        }), 500

@api_bp.route('/food/log', methods=['POST'])
@requires_auth
def log_food():
    current_user = get_current_user()
    # Validate CSRF token
    try:
        validate_csrf(request.headers.get('X-CSRFToken'))
    except ValidationError:
        return jsonify({'success': False, 'message': 'CSRF token validation failed'}), 400
    
    data = request.get_json()
    
    food_id = data.get('food_id')
    quantity = data.get('quantity')
    meal_type = data.get('meal_type')
    notes = data.get('notes', '')
    
    if not all([food_id, quantity, meal_type]):
        return jsonify({
            'success': False,
            'message': 'Missing required fields'
        }), 400
    
    if quantity <= 0:
        return jsonify({
            'success': False,
            'message': 'Quantity must be greater than 0'
        }), 400
    
    # Get the food item
    food = Food.query.get(food_id)
    if not food:
        return jsonify({
            'success': False,
            'message': 'Food item not found'
        }), 404
    
    # Create new food log entry
    food_log = FoodLog(
        user_id=current_user.id,
        food_id=food_id,
        quantity=quantity,
        meal_type=meal_type,
        notes=notes
    )
    
    try:
        db.session.add(food_log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully logged {quantity}g of {food.name}',
            'log_id': food_log.id
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error logging food: {str(e)}'
        }), 500

@api_bp.route('/ai/recommend', methods=['POST'])
@requires_auth
def ai_recommend():
    current_user = get_current_user()
    # Validate CSRF token
    try:
        validate_csrf(request.headers.get('X-CSRFToken'))
    except ValidationError:
        return jsonify({'success': False, 'message': 'CSRF token validation failed'}), 400
    
    data = request.get_json()
    recommendation_type = data.get('type', 'meal')
    
    try:
        # Get user's recent food logs for context
        recent_logs = FoodLog.query.filter_by(user_id=current_user.id)\
            .order_by(FoodLog.logged_at.desc())\
            .limit(10).all()
        
        # Get user preferences
        dietary_restrictions = current_user.get_dietary_restrictions()
        calorie_goal = current_user.daily_calorie_goal
        preferred_cuisine = current_user.preferred_cuisine
        
        # Get AI recommendation
        recommendation_text = get_meal_recommendation(
            recent_logs=recent_logs,
            dietary_restrictions=dietary_restrictions,
            calorie_goal=calorie_goal,
            preferred_cuisine=preferred_cuisine,
            recommendation_type=recommendation_type
        )
        
        # Save the recommendation
        ai_recommendation = AIRecommendation(
            user_id=current_user.id,
            recommendation_type=recommendation_type,
            recommendation_text=recommendation_text
        )
        
        # Set context data
        context_data = {
            'recent_foods': [log.food.name for log in recent_logs[:5]],
            'dietary_restrictions': dietary_restrictions,
            'calorie_goal': calorie_goal,
            'preferred_cuisine': preferred_cuisine
        }
        ai_recommendation.set_context_data(context_data)
        
        db.session.add(ai_recommendation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'recommendation': {
                'id': ai_recommendation.id,
                'type': recommendation_type,
                'text': recommendation_text
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting AI recommendation: {str(e)}'
        }), 500

@api_bp.route('/ai/recommendation/<int:recommendation_id>/rate', methods=['POST'])
@requires_auth
def rate_recommendation(recommendation_id):
    current_user = get_current_user()
    try:
        data = request.get_json()
        rating = data.get('rating')  # 1 for thumbs up, -1 for thumbs down
        
        if rating not in [1, -1]:
            return jsonify({
                'success': False,
                'message': 'Rating must be 1 (thumbs up) or -1 (thumbs down)'
            }), 400
        
        # Find the recommendation
        recommendation = AIRecommendation.query.filter_by(
            id=recommendation_id,
            user_id=current_user.id
        ).first()
        
        if not recommendation:
            return jsonify({
                'success': False,
                'message': 'Recommendation not found'
            }), 404
        
        # Update the rating
        recommendation.rating = rating
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Rating saved successfully'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error saving rating: {str(e)}'
        }), 500

@api_bp.route('/nutrition/summary')
@requires_auth
def nutrition_summary():
    current_user = get_current_user()
    try:
        from datetime import date, timedelta
        from sqlalchemy import func, and_
        
        # Get date range
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
        
        # Calculate totals
        total_calories = sum(log.get_calories() for log in logs)
        total_items = len(logs)
        
        # Calculate daily averages
        daily_data = {}
        for log in logs:
            log_date = log.logged_at.date().isoformat()
            if log_date not in daily_data:
                daily_data[log_date] = {
                    'calories': 0,
                    'protein': 0,
                    'carbs': 0,
                    'fat': 0,
                    'items': 0
                }
            
            daily_data[log_date]['calories'] += log.get_calories()
            daily_data[log_date]['items'] += 1
            
            # Add other nutrients
            nutrients = log.get_nutrients()
            for nutrient in ['protein', 'carbs', 'fat']:
                if f'{nutrient}_per_100g' in nutrients:
                    daily_data[log_date][nutrient] += nutrients[f'{nutrient}_per_100g']
        
        avg_daily_calories = total_calories / days if days > 0 else 0
        
        return jsonify({
            'success': True,
            'summary': {
                'total_calories': total_calories,
                'total_items': total_items,
                'avg_daily_calories': avg_daily_calories,
                'daily_data': daily_data,
                'calorie_goal': current_user.daily_calorie_goal,
                'period_days': days
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error calculating nutrition summary: {str(e)}'
        }), 500

@api_bp.route('/user/preferences', methods=['GET', 'POST'])
@requires_auth
def user_preferences():
    current_user = get_current_user()
    if request.method == 'POST':
        data = request.get_json()
        
        try:
            # Update user preferences
            if 'daily_calorie_goal' in data:
                current_user.daily_calorie_goal = data['daily_calorie_goal']
            
            if 'preferred_cuisine' in data:
                current_user.preferred_cuisine = data['preferred_cuisine']
            
            if 'dietary_restrictions' in data:
                current_user.set_dietary_restrictions(data['dietary_restrictions'])
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Preferences updated successfully'
            })
        
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'Error updating preferences: {str(e)}'
            }), 500
    
    else:
        # GET request - return current preferences
        return jsonify({
            'success': True,
            'preferences': {
                'daily_calorie_goal': current_user.daily_calorie_goal,
                'preferred_cuisine': current_user.preferred_cuisine,
                'dietary_restrictions': current_user.get_dietary_restrictions()
            }
        })