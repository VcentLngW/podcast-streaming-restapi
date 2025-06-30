# Podcast REST API

A Flask-based REST API for a podcast application with user authentication, podcast management, and category system.

## Features

- **User Authentication**: JWT-based authentication with email verification
- **Podcast Management**: Create, read, update, delete podcasts
- **Category System**: Organize podcasts by categories
- **File Upload**: Audio and thumbnail file uploads
- **Comments System**: Add comments to podcasts
- **Like System**: Like/unlike podcasts
- **Audio Streaming**: HTTP Range request support for audio streaming
- **UUID Primary Keys**: All models use UUID primary keys for better scalability

## Tech Stack

- **Backend**: Flask, SQLAlchemy, Alembic
- **Database**: SQLite (development), PostgreSQL (production ready)
- **Authentication**: JWT (Flask-JWT-Extended)
- **File Handling**: Werkzeug, Mutagen (audio metadata)
- **Email**: SMTP for verification emails

## Project Structure

```
restAPI/
├── app/
│   ├── __init__.py
│   ├── config/
│   │   └── config.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── podcast.py
│   │   ├── category.py
│   │   ├── comment.py
│   │   └── podcast_listen.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── podcast.py
│   │   └── category.py
│   ├── uploads/
│   │   ├── audio/
│   │   └── thumbnails/
│   └── utils/
│       ├── __init__.py
│       ├── email.py
│       ├── file_handlers.py
│       ├── jwt_handlers.py
│       └── password.py
├── migrations/
├── requirements.txt
├── run.py
└── alembic.ini
```

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd restAPI
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Run setup script (optional but recommended)**
   ```bash
   python setup.py
   ```

6. **Initialize database**
   ```bash
   flask db upgrade
   ```

7. **Run the application**
   ```bash
   python run.py
   ```

## Quick Server Setup

For quick deployment on a server:

```bash
# Clone and setup
git clone <repository-url>
cd restAPI
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp env.example .env
# Edit .env with your server configuration

# Run setup and initialize
python setup.py
flask db upgrade

# Start the application
python run.py
```

## Environment Variables

Create a `.env` file with the following variables:

```env
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///instance/podcast.db
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Static File URL (for production)
STATIC_FILE_URL=http://localhost:5000
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/verify-email` - Email verification
- `POST /api/auth/forgot-password` - Password reset request
- `POST /api/auth/reset-password` - Password reset

### Categories
- `GET /api/categories` - Get all categories
- `GET /api/categories/<id>` - Get category by ID
- `POST /api/categories` - Create new category
- `DELETE /api/categories/<id>` - Delete category

### Podcasts
- `GET /api/podcasts` - Get all podcasts (with pagination)
- `GET /api/podcasts/<id>` - Get podcast by ID
- `POST /api/podcasts` - Create new podcast
- `DELETE /api/podcasts/<id>` - Delete podcast
- `GET /api/podcasts/discover` - Discover podcasts
- `POST /api/podcasts/<id>/like` - Like podcast
- `POST /api/podcasts/<id>/unlike` - Unlike podcast
- `GET /api/podcasts/<id>/check-like` - Check if liked
- `GET /api/podcasts/<id>/stream` - Stream audio file
- `POST /api/podcasts/<id>/track` - Track listening progress
- `GET /api/podcasts/<id>/last-position` - Get last position

### Comments
- `GET /api/podcasts/<id>/comments` - Get podcast comments
- `POST /api/podcasts/<id>/comments` - Add comment
- `DELETE /api/podcasts/<id>/comments/<comment_id>` - Delete comment

### File Serving
- `GET /api/uploads/thumbnails/<filename>` - Serve thumbnail images
- `GET /api/uploads/audio/<filename>` - Serve audio files

## Database Models

### User
- UUID primary key
- Email, username, password (hashed)
- Email verification status
- Profile information

### Category
- UUID primary key
- Name, description, slug
- Timestamps

### Podcast
- UUID primary key
- Title, description, duration
- Audio and thumbnail URLs
- Author relationship
- Categories (many-to-many)
- Likes (many-to-many)

### Comment
- UUID primary key
- Content, timestamps
- User and podcast relationships
- Parent comment for replies

### PodcastListen
- UUID primary key
- User and podcast relationships
- Position, duration, timestamps

## File Upload

The API supports file uploads for:
- **Audio files**: MP3, WAV, M4A, AAC
- **Thumbnail images**: JPG, PNG, GIF

Files are stored in the `uploads/` directory and served via dedicated endpoints.

## Authentication

JWT tokens are used for authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

## Development

### Running Tests
```bash
python -m pytest
```

### Database Migrations
```bash
# Create new migration
flask db migrate -m "Description"

# Apply migrations
flask db upgrade

# Rollback migration
flask db downgrade
```

### Code Formatting
```bash
black .
flake8 .
```

## Production Deployment

1. **Set up production database** (PostgreSQL recommended)
2. **Configure environment variables** for production
3. **Set up reverse proxy** (Nginx)
4. **Use WSGI server** (Gunicorn)
5. **Configure SSL certificates**
6. **Set up monitoring and logging**

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License. 