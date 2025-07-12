from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from flask_wtf.csrf import validate_csrf, ValidationError
from werkzeug.utils import secure_filename
from models import db, Food, FoodLog
from services.ai_service import extract_barcode_from_image
from services.nutrition_api import get_food_by_barcode
import os
import uuid
from datetime import datetime

barcode_bp = Blueprint('barcode', __name__)

UPLOAD_FOLDER = 'temp_uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_upload_folder():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

@barcode_bp.route('/scan', methods=['GET', 'POST'])
@login_required
def scan():
    if request.method == 'POST':
        # Validate CSRF token
        try:
            validate_csrf(request.form.get('csrf_token'))
        except ValidationError:
            return jsonify({'error': 'CSRF token validation failed'}), 400
            
        if 'photo' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['photo']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            try:
                # Ensure upload folder exists
                ensure_upload_folder()
                
                # Generate unique filename
                filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                
                # Save uploaded file temporarily
                file.save(filepath)
                
                # Extract barcode using AI
                barcode = extract_barcode_from_image(filepath)
                
                # Clean up temporary file
                if os.path.exists(filepath):
                    os.remove(filepath)
                
                if not barcode:
                    return jsonify({'error': 'No barcode detected in image'}), 400
                
                # Get nutrition data from Open Food Facts
                food_data = get_food_by_barcode(barcode)
                
                if not food_data:
                    return jsonify({'error': 'Food not found in database'}), 404
                
                # Check if food already exists in our database
                existing_food = Food.query.filter_by(upc_code=barcode).first()
                
                if not existing_food:
                    # Create new food entry
                    food = Food(
                        upc_code=barcode,
                        name=food_data['name'],
                        brand=food_data.get('brand', ''),
                        ingredients=food_data.get('ingredients', '')
                    )
                    food.set_nutrition_data(food_data['nutrition'])
                    
                    db.session.add(food)
                    db.session.commit()
                    food_id = food.id
                else:
                    food_id = existing_food.id
                
                return jsonify({
                    'success': True,
                    'barcode': barcode,
                    'food': {
                        'id': food_id,
                        'name': food_data['name'],
                        'brand': food_data.get('brand', ''),
                        'nutrition': food_data['nutrition']
                    }
                })
                
            except Exception as e:
                # Clean up temporary file if it exists
                if 'filepath' in locals() and os.path.exists(filepath):
                    os.remove(filepath)
                
                return jsonify({'error': f'Error processing image: {str(e)}'}), 500
        
        return jsonify({'error': 'Invalid file type'}), 400
    
    return render_template('food/barcode_scan.html')

@barcode_bp.route('/log-scanned', methods=['POST'])
@login_required
def log_scanned():
    food_id = request.form.get('food_id', type=int)
    quantity = request.form.get('quantity', type=float)
    meal_type = request.form.get('meal_type')
    notes = request.form.get('notes', '')
    
    if not all([food_id, quantity, meal_type]):
        flash('Please fill in all required fields.', 'error')
        return redirect(url_for('barcode.scan'))
    
    if quantity <= 0:
        flash('Quantity must be greater than 0.', 'error')
        return redirect(url_for('barcode.scan'))
    
    # Get the food item
    food = Food.query.get(food_id)
    if not food:
        flash('Food item not found.', 'error')
        return redirect(url_for('barcode.scan'))
    
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
        flash(f'Successfully logged {quantity}g of {food.name} from barcode scan!', 'success')
        return redirect(url_for('dashboard.main'))
    except Exception as e:
        db.session.rollback()
        flash('Error logging food. Please try again.', 'error')
        return redirect(url_for('barcode.scan'))