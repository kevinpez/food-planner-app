# AI-Powered Food Planner

A comprehensive web application for tracking food intake, scanning UPC codes for nutritional information, and receiving AI-powered meal recommendations.

## Features

### Core Functionality
- **UPC Code Scanning**: Look up food products by barcode to get ingredients and nutritional data
- **Food Intake Logging**: Track daily meals, snacks, and beverages with detailed nutritional information
- **AI Meal Recommendations**: Get personalized healthy meal suggestions based on food history and preferences
- **Daily Planning**: Plan meals in advance with nutritional goal tracking
- **Nutritional Dashboard**: View calories, macros, and micronutrients with interactive visualizations

### AI-Powered Features
- Personalized meal recommendations using Anthropic's Claude AI
- Health insights based on eating patterns
- Food alternatives suggestions
- Daily nutrition analysis and feedback

### Data Sources
- **Open Food Facts API**: Comprehensive database of food products and nutritional information
- **Edamam Food Database**: Premium nutrition data (backup/enhancement)
- **User-generated content**: Custom food entries and preferences

## Technology Stack

### Backend
- **Flask**: Python web framework
- **SQLAlchemy**: Database ORM
- **Flask-Login**: User authentication
- **Flask-Migrate**: Database migrations
- **SQLite**: Database (development)

### Frontend
- **Bootstrap 5**: CSS framework
- **Font Awesome**: Icons
- **JavaScript**: Interactive features
- **Chart.js/Plotly**: Data visualization

### APIs & Services
- **Anthropic Claude API**: AI-powered recommendations
- **Open Food Facts API**: Food database
- **Edamam Food Database API**: Nutritional data

## Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Virtual environment (recommended)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/kevinpez/food-planner-app.git
   cd food-planner-app
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize the database**
   ```bash
   python -c "from app import app; from models import db; app.app_context().push(); db.create_all()"
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

The application will be available at `http://localhost:5000`

## Configuration

### Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///food_planner.db
ANTHROPIC_API_KEY=your-anthropic-api-key-here
FLASK_ENV=development
FLASK_DEBUG=True
```

### API Keys

- **Anthropic API Key**: Required for AI-powered recommendations. Get your key at [Anthropic Console](https://console.anthropic.com/)
- **Open Food Facts**: No API key required (free and open)
- **Edamam API**: Optional, for enhanced nutritional data

## Usage

### Getting Started

1. **Create an Account**: Register with your email and set your daily calorie goal
2. **Set Preferences**: Configure dietary restrictions and preferred cuisine
3. **Log Your First Meal**: Use UPC scanning or search by name to log foods
4. **Get AI Recommendations**: Ask for personalized meal suggestions based on your history
5. **Track Progress**: Monitor your nutrition with the dashboard and analytics

### Key Features

#### Food Logging
- Scan UPC codes for instant food recognition
- Search by food name from extensive database
- Add custom foods with nutritional information
- Track quantity and meal type (breakfast, lunch, dinner, snack)

#### AI Recommendations
- Personalized meal suggestions based on your food history
- Considers dietary restrictions and preferences
- Nutritional balance recommendations
- Healthier food alternatives

#### Analytics & Insights
- Daily nutrition dashboard
- Weekly and monthly tracking
- Macro and micronutrient analysis
- Progress toward calorie goals

## API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/logout` - User logout

### Food Management
- `GET /api/food/search-upc/<upc>` - Search food by UPC code
- `GET /api/food/search-name?q=<query>` - Search food by name
- `POST /api/food/log` - Log food intake

### AI Services
- `POST /api/ai/recommend` - Get AI meal recommendation
- `GET /api/nutrition/summary` - Get nutrition summary

## Database Schema

### User
- id, username, email, password_hash
- daily_calorie_goal, dietary_restrictions, preferred_cuisine
- created_at

### Food
- id, upc_code, name, brand, ingredients
- nutrition_data (JSON), created_at

### FoodLog
- id, user_id, food_id, quantity, meal_type
- logged_at, notes

### DailyPlan
- id, user_id, date, meals_planned (JSON)
- nutritional_goals (JSON), created_at

### AIRecommendation
- id, user_id, recommendation_type, recommendation_text
- context_data (JSON), created_at, is_used

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Open Food Facts](https://world.openfoodfacts.org/) for providing free access to food data
- [Anthropic](https://www.anthropic.com/) for AI-powered recommendations
- [Bootstrap](https://getbootstrap.com/) for UI components
- [Font Awesome](https://fontawesome.com/) for icons

## Support

For support, please open an issue on GitHub or contact the maintainers.

---

**Note**: This application is for educational and personal use. Always consult with healthcare professionals for medical advice regarding nutrition and diet.