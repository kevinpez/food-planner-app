from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf.csrf import validate_csrf, ValidationError
from models import db, User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.main'))
    
    if request.method == 'POST':
        # Validate CSRF token
        try:
            validate_csrf(request.form.get('csrf_token'))
        except ValidationError:
            flash('Security token validation failed. Please try again.', 'error')
            return redirect(url_for('auth.login'))
        
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please enter both username and password.', 'error')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=request.form.get('remember'))
            flash(f'Welcome back, {user.username}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard.main'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.main'))
    
    if request.method == 'POST':
        # Validate CSRF token
        try:
            validate_csrf(request.form.get('csrf_token'))
        except ValidationError:
            flash('Security token validation failed. Please try again.', 'error')
            return redirect(url_for('auth.register'))
        
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not all([username, email, password, confirm_password]):
            flash('Please fill in all fields.', 'error')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('auth/register.html')
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('auth/register.html')
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        
        # Set default preferences
        daily_calorie_goal = request.form.get('daily_calorie_goal', 2000, type=int)
        user.daily_calorie_goal = daily_calorie_goal
        
        # Check if user wants demo data
        generate_demo_data = request.form.get('generate_demo_data') == '1'
        
        try:
            db.session.add(user)
            db.session.commit()
            
            # Generate demo data if requested
            if generate_demo_data:
                try:
                    # Wait a moment for the database transaction to complete
                    import time
                    time.sleep(0.1)
                    
                    
                    # Get the actual database path from Flask-SQLAlchemy
                    from flask import current_app
                    import os
                    
                    # Use Flask's database engine to get the real database path
                    engine = db.engine
                    db_path = engine.url.database
                    
                    # If it's still a relative path, use Flask's instance folder
                    if not os.path.isabs(db_path):
                        db_path = os.path.join(current_app.instance_path, db_path)
                    
                    
                    from services.simple_demo_generator import create_demo_data_with_path
                    demo_result = create_demo_data_with_path(user.id, db_path, months=6)
                    
                    
                    if demo_result['success']:
                        flash(f'🎉 Registration successful! Created {demo_result["logs_created"]} demo food logs across {demo_result["unique_dates"]} days with {demo_result["avg_calories_per_day"]} avg calories/day. Please log in to explore your analytics!', 'success')
                    else:
                        error_details = demo_result.get('error', 'Unknown error')
                        flash(f'⚠️ Registration successful, but demo data generation failed: {error_details}. Please log in and add food manually.', 'warning')
                        
                        
                except Exception as e:
                    flash(f'⚠️ Registration successful, but demo data generation encountered an error: {str(e)}. Please log in and add food manually.', 'warning')
                    
            else:
                flash('Registration successful! Please log in.', 'success')
                
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
            return render_template('auth/register.html')
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/profile')
@login_required
def profile():
    from datetime import date
    
    # Calculate days active
    days_active = (date.today() - current_user.created_at.date()).days + 1
    
    return render_template('auth/profile.html', user=current_user, days_active=days_active)

@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        # Validate CSRF token
        try:
            validate_csrf(request.form.get('csrf_token'))
        except ValidationError:
            flash('Security token validation failed. Please try again.', 'error')
            return redirect(url_for('auth.edit_profile'))
        
        current_user.daily_calorie_goal = request.form.get('daily_calorie_goal', 2000, type=int)
        current_user.preferred_cuisine = request.form.get('preferred_cuisine', '')
        
        # Handle dietary restrictions
        dietary_restrictions = request.form.getlist('dietary_restrictions')
        current_user.set_dietary_restrictions(dietary_restrictions)
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('auth.profile'))
        except Exception as e:
            db.session.rollback()
            flash('Failed to update profile. Please try again.', 'error')
    
    return render_template('auth/edit_profile.html', user=current_user)