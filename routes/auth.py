from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_wtf.csrf import validate_csrf, ValidationError
from models import db, User
from services.auth0_service import (
    requires_auth, get_current_user, get_auth0_login_url, 
    get_auth0_logout_url, handle_auth0_callback, clear_session
)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login')
def login():
    # Check if user is already authenticated
    current_user = get_current_user()
    if current_user:
        return redirect(url_for('dashboard.main'))
    
    # Redirect to Auth0 login
    return get_auth0_login_url()

@auth_bp.route('/callback')
def callback():
    """Handle Auth0 callback"""
    user, is_new_user = handle_auth0_callback()
    
    if not user:
        flash('Authentication failed. Please try again.', 'error')
        return redirect(url_for('index'))
    
    # Check if user wants demo data (from Auth0 user metadata or query param)
    generate_demo_data = request.args.get('demo_data') == '1'
    
    if is_new_user and generate_demo_data:
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
                flash(f'🎉 Welcome! Created {demo_result["logs_created"]} demo food logs across {demo_result["unique_dates"]} days with {demo_result["avg_calories_per_day"]} avg calories/day. Explore your analytics!', 'success')
            else:
                error_details = demo_result.get('error', 'Unknown error')
                flash(f'⚠️ Welcome! Demo data generation failed: {error_details}. You can add food manually.', 'warning')
                
        except Exception as e:
            flash(f'⚠️ Welcome! Demo data generation encountered an error: {str(e)}. You can add food manually.', 'warning')
    else:
        welcome_message = f'Welcome back, {user.name}!' if not is_new_user else f'Welcome to Food Planner, {user.name}!'
        flash(welcome_message, 'success')
    
    return redirect(url_for('dashboard.main'))

@auth_bp.route('/logout')
def logout():
    """Logout user from Auth0 and clear session"""
    clear_session()
    return redirect(get_auth0_logout_url())

@auth_bp.route('/profile')
@requires_auth
def profile():
    from datetime import date
    
    current_user = get_current_user()
    # Calculate days active
    days_active = (date.today() - current_user.created_at.date()).days + 1
    
    return render_template('auth/profile.html', user=current_user, days_active=days_active)

@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@requires_auth
def edit_profile():
    current_user = get_current_user()
    
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

@auth_bp.route('/register')
def register():
    """Redirect to Auth0 signup with demo data option"""
    # Check if user is already authenticated
    current_user = get_current_user()
    if current_user:
        return redirect(url_for('dashboard.main'))
    
    # Show registration page with Auth0 signup option
    return render_template('auth/register.html')