import os
from flask import Flask, render_template, redirect, url_for, flash
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import Config
from models import db, User, Food, FoodLog, DailyPlan, AIRecommendation
from routes.auth import auth_bp
from routes.food import food_bp
from routes.api import api_bp
from routes.dashboard import dashboard_bp
from routes.barcode import barcode_bp
from services.auth0_service import init_auth0, get_current_user

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    csrf = CSRFProtect(app)
    
    # Initialize Auth0
    init_auth0(app)
    
    # Security headers
    @app.after_request
    def security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response
    
    # Make current_user available in templates
    @app.context_processor
    def inject_user():
        return dict(current_user=get_current_user())
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(food_bp, url_prefix='/food')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(barcode_bp, url_prefix='/barcode')
    
    # Main routes
    @app.route('/')
    def index():
        current_user = get_current_user()
        if current_user:
            return redirect(url_for('dashboard.main'))
        return render_template('index.html')
    
    @app.route('/about')
    def about():
        return render_template('about.html')
    
    @app.route('/support')
    def support():
        return render_template('support.html')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500
    
    return app

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)