from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Food, FoodLog
from services.nutrition_api import search_food_by_upc, search_food_by_name
from services.auth0_service import requires_auth, get_current_user
from datetime import datetime

food_bp = Blueprint('food', __name__)

@food_bp.route('/log', methods=['GET', 'POST'])
@requires_auth
def log():
    if request.method == 'POST':
        food_id = request.form.get('food_id', type=int)
        quantity = request.form.get('quantity', type=float)
        meal_type = request.form.get('meal_type')
        notes = request.form.get('notes', '')
        
        if not all([food_id, quantity, meal_type]):
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('food.log'))
        
        if quantity <= 0:
            flash('Quantity must be greater than 0.', 'error')
            return redirect(url_for('food.log'))
        
        # Get the food item
        food = Food.query.get(food_id)
        if not food:
            flash('Food item not found.', 'error')
            return redirect(url_for('food.log'))
        
        # Create new food log entry
        current_user = get_current_user()
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
            flash(f'Successfully logged {quantity}g of {food.name}!', 'success')
            return redirect(url_for('dashboard.main'))
        except Exception as e:
            db.session.rollback()
            flash('Error logging food. Please try again.', 'error')
            return redirect(url_for('food.log'))
    
    return render_template('food/log.html')

@food_bp.route('/search')
@requires_auth
def search():
    query = request.args.get('q', '')
    upc = request.args.get('upc', '')
    
    foods = []
    
    if query:
        # Search by name
        foods = Food.query.filter(
            Food.name.ilike(f'%{query}%')
        ).limit(20).all()
        
        # If no local results, search external API
        if not foods:
            try:
                external_foods = search_food_by_name(query)
                foods.extend(external_foods)
            except Exception as e:
                flash('Error searching external food database.', 'warning')
    
    elif upc:
        # Search by UPC
        food = Food.query.filter_by(upc_code=upc).first()
        if food:
            foods = [food]
        else:
            try:
                external_food = search_food_by_upc(upc)
                if external_food:
                    foods = [external_food]
            except Exception as e:
                flash('Error searching for UPC code.', 'warning')
    
    return render_template('food/search.html', foods=foods, query=query, upc=upc)

@food_bp.route('/add-custom', methods=['GET', 'POST'])
@requires_auth
def add_custom():
    if request.method == 'POST':
        name = request.form.get('name')
        brand = request.form.get('brand', '')
        ingredients = request.form.get('ingredients', '')
        
        # Nutrition data
        calories = request.form.get('calories', type=float)
        protein = request.form.get('protein', type=float)
        carbs = request.form.get('carbs', type=float)
        fat = request.form.get('fat', type=float)
        fiber = request.form.get('fiber', type=float)
        sugar = request.form.get('sugar', type=float)
        sodium = request.form.get('sodium', type=float)
        
        if not name:
            flash('Food name is required.', 'error')
            return render_template('food/add_custom.html')
        
        # Create nutrition data dictionary
        nutrition_data = {
            'calories_per_100g': calories or 0,
            'protein_per_100g': protein or 0,
            'carbs_per_100g': carbs or 0,
            'fat_per_100g': fat or 0,
            'fiber_per_100g': fiber or 0,
            'sugar_per_100g': sugar or 0,
            'sodium_per_100g': sodium or 0
        }
        
        # Create new food item
        food = Food(
            name=name,
            brand=brand,
            ingredients=ingredients
        )
        food.set_nutrition_data(nutrition_data)
        
        try:
            db.session.add(food)
            db.session.commit()
            flash(f'Custom food "{name}" added successfully!', 'success')
            return redirect(url_for('food.log'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding custom food. Please try again.', 'error')
    
    return render_template('food/add_custom.html')

@food_bp.route('/history')
@requires_auth
def history():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get user's food logs with pagination
    current_user = get_current_user()
    food_logs = FoodLog.query.filter_by(user_id=current_user.id)\
        .order_by(FoodLog.logged_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('food/history.html', food_logs=food_logs)

@food_bp.route('/delete/<int:log_id>')
@requires_auth
def delete_log(log_id):
    food_log = FoodLog.query.get_or_404(log_id)
    
    # Check if the log belongs to the current user
    current_user = get_current_user()
    if food_log.user_id != current_user.id:
        flash('You can only delete your own food logs.', 'error')
        return redirect(url_for('food.history'))
    
    try:
        db.session.delete(food_log)
        db.session.commit()
        flash('Food log deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting food log. Please try again.', 'error')
    
    return redirect(url_for('food.history'))

@food_bp.route('/edit/<int:log_id>', methods=['GET', 'POST'])
@requires_auth
def edit_log(log_id):
    food_log = FoodLog.query.get_or_404(log_id)
    
    # Check if the log belongs to the current user
    current_user = get_current_user()
    if food_log.user_id != current_user.id:
        flash('You can only edit your own food logs.', 'error')
        return redirect(url_for('food.history'))
    
    if request.method == 'POST':
        quantity = request.form.get('quantity', type=float)
        meal_type = request.form.get('meal_type')
        notes = request.form.get('notes', '')
        
        if not quantity or quantity <= 0:
            flash('Quantity must be greater than 0.', 'error')
            return render_template('food/edit_log.html', food_log=food_log)
        
        if not meal_type:
            flash('Meal type is required.', 'error')
            return render_template('food/edit_log.html', food_log=food_log)
        
        # Update the food log
        food_log.quantity = quantity
        food_log.meal_type = meal_type
        food_log.notes = notes
        
        try:
            db.session.commit()
            flash('Food log updated successfully.', 'success')
            return redirect(url_for('food.history'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating food log. Please try again.', 'error')
    
    return render_template('food/edit_log.html', food_log=food_log)