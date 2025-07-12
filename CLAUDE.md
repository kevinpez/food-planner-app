# BellySattva - AI-Powered Nutrition Tracking

## Overview
This is an AI-powered web application for food intake tracking, UPC barcode scanning, and personalized meal recommendations. Built with Flask and integrating with multiple APIs including Anthropic Claude AI for intelligent recommendations.

## Technology Stack
- **Backend**: Flask, SQLAlchemy, Flask-Migrate, Flask-WTF
- **Database**: SQLite (development), PostgreSQL (production)
- **Authentication**: Auth0 with OAuth2/JWT
- **APIs**: Anthropic Claude AI, OpenAI, Open Food Facts, Edamam
- **Frontend**: Bootstrap 5, JavaScript, Plotly for visualizations
- **Security**: CSRF protection, secure headers, input sanitization

## Key Features
- UPC barcode scanning for food product lookup
- AI-powered meal recommendations using Claude API
- Nutritional tracking and analytics dashboard
- Daily meal planning with goal tracking
- User authentication via Auth0
- Security-first design with comprehensive validation

## Development Setup

### Prerequisites
```bash
python 3.8+
pip
```

### Installation
```bash
# Clone and navigate to project
git clone [repository]
cd bellysattva

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (copy .env.example to .env and configure)
cp .env.example .env
```

### Environment Variables
Create a `.env` file with:
```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///bellysattva.db
ANTHROPIC_API_KEY=your-anthropic-api-key
OPENAI_API_KEY=your-openai-api-key
AUTH0_DOMAIN=your-auth0-domain
AUTH0_CLIENT_ID=your-auth0-client-id
AUTH0_CLIENT_SECRET=your-auth0-client-secret
AUTH0_AUDIENCE=your-auth0-audience
FLASK_ENV=development
```

### Database Setup
```bash
# Initialize database
python -c "from app import app; from models import db; app.app_context().push(); db.create_all()"

# Or use Flask-Migrate for production
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### Running the Application
```bash
# Development server
python app.py

# Production deployment
gunicorn app:app --bind 0.0.0.0:8000
```

## Project Structure
```
bellysattva/
├── app.py                 # Main application factory
├── config.py             # Configuration settings
├── models.py             # Database models
├── utils.py              # Utility functions
├── routes/               # Blueprint routes
│   ├── auth.py          # Authentication routes
│   ├── food.py          # Food logging routes
│   ├── api.py           # API endpoints
│   ├── dashboard.py     # Dashboard routes
│   └── barcode.py       # Barcode scanning routes
├── services/            # Business logic services
│   ├── ai_service.py    # AI recommendation service
│   ├── auth0_service.py # Auth0 integration
│   └── nutrition_api.py # Nutrition API service
├── templates/           # Jinja2 templates
├── static/              # CSS, JS, images
└── migrations/          # Database migrations
```

## Database Models
- **User**: Auth0 user profiles with preferences
- **Food**: Product database with UPC codes and nutrition
- **FoodLog**: User food intake records
- **DailyPlan**: Meal planning and nutritional goals
- **AIRecommendation**: AI-generated meal suggestions

## API Endpoints
- `GET /` - Landing page
- `GET /auth/login` - Auth0 login
- `GET /auth/logout` - Auth0 logout
- `POST /food/log` - Log food intake
- `GET /api/food/search-upc/<upc>` - Search by UPC
- `GET /api/food/search-name?q=<query>` - Search by name
- `POST /api/ai/recommend` - Get AI recommendations
- `GET /dashboard/` - Main dashboard
- `GET /dashboard/nutrition` - Nutrition analytics

## Common Tasks

### Running Tests
```bash
# No test framework currently configured
# Recommend adding pytest for testing
pip install pytest pytest-flask
pytest tests/
```

### Code Quality
```bash
# No linting tools currently configured
# Recommend adding these tools:
pip install black flake8 mypy
black .
flake8 .
mypy .
```

### Database Migrations
```bash
# Create new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Rollback migration
flask db downgrade
```

### Adding New Features
1. Create new routes in appropriate blueprint
2. Add models if needed with migrations
3. Update templates and static files
4. Add API endpoints if needed
5. Update documentation

## Security Considerations
- All routes use CSRF protection
- Input validation and sanitization
- Secure headers configured
- Auth0 JWT token validation
- SQL injection prevention via SQLAlchemy
- XSS protection with template escaping

## Production Deployment
- Set FLASK_ENV=production
- Use PostgreSQL database
- Configure proper secret keys
- Set up SSL/TLS
- Use reverse proxy (nginx)
- Monitor application logs

### Auth0 Firewall Configuration
When deploying behind a firewall, ensure these Auth0 IP addresses are allowed for inbound connections:
- 18.218.158.118
- 52.14.149.14
- 3.20.16.23
- 54.245.93.221
- 44.246.144.93
- 52.33.36.223
- 44.224.190.45

These IPs are required for Auth0 callbacks and webhook functionality.

### Auth0 Callback URLs
Configure these callback URLs in your Auth0 application settings:

**Development Environment:**
- `http://localhost:5000/auth/callback`
- `http://localhost:5000/` (logout return URL)

**Production Environment:**
- `https://bellysattva.com/auth/callback`
- `https://bellysattva.com/` (logout return URL)

## API Keys Required
- **Anthropic API**: AI meal recommendations
- **OpenAI API**: Alternative AI service
- **Auth0**: User authentication
- **Open Food Facts**: Free food database (no key required)

## Troubleshooting
- Check `.env` file configuration
- Verify database migrations are applied
- Ensure all API keys are valid
- Check Flask logs for errors
- Verify Auth0 configuration

## Development Notes
- Application uses factory pattern for Flask app creation
- Database models use JSON fields for flexible data storage
- AI service is abstracted for easy provider switching
- Security headers are automatically applied
- Error handling includes custom error pages

## Contributing
1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request
5. Follow code style conventions