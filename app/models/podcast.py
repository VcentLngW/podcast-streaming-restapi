from datetime import datetime
from app import db
from flask import current_app
import uuid

# Association table for many-to-many relationship between Podcast and Category
podcast_categories = db.Table('podcast_categories',
    db.Column('podcast_id', db.String(36), db.ForeignKey('podcasts.id'), primary_key=True),
    db.Column('category_id', db.String(36), db.ForeignKey('categories.id'), primary_key=True)
)

# Association table for likes
podcast_likes = db.Table('podcast_likes',
    db.Column('podcast_id', db.String(36), db.ForeignKey('podcasts.id'), primary_key=True),
    db.Column('user_id', db.String(36), db.ForeignKey('users.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

class Podcast(db.Model):
    __tablename__ = 'podcasts'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    thumbnail_url = db.Column(db.String(500), nullable=False)
    audio_url = db.Column(db.String(500), nullable=False)
    duration = db.Column(db.Integer, nullable=True)  # Duration in seconds
    author_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    slug = db.Column(db.String(200), nullable=False, unique=True)
    published = db.Column(db.Boolean, default=False)
    published_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    author = db.relationship('User', backref=db.backref('podcasts', lazy=True))
    categories = db.relationship('Category', 
                               secondary=podcast_categories,
                               lazy='subquery',
                               backref=db.backref('podcasts', lazy=True))
    likes = db.relationship('User',
                          secondary=podcast_likes,
                          lazy='subquery',
                          backref=db.backref('liked_podcasts', lazy=True))
    listen_records = db.relationship('PodcastListen', backref='podcast', lazy=True)

    def __init__(self, title, thumbnail_url, audio_url, author_id, description=None, duration=None):
        self.title = title
        self.thumbnail_url = thumbnail_url
        self.audio_url = audio_url
        self.author_id = author_id
        self.description = description
        self.duration = duration
        self.slug = title.lower().replace(' ', '-')

    def __repr__(self):
        return f'<Podcast {self.title}>'

    def to_dict(self):
        # Get the static file URL from config
        static_url = current_app.config.get('STATIC_FILE_URL', 'http://localhost:5000')

        # Construct full URLs for media files
        thumbnail_url = f"{static_url}/uploads/{self.thumbnail_url}" if self.thumbnail_url else None
        audio_url = f"{static_url}/uploads/{self.audio_url}" if self.audio_url else None
        
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'thumbnail_url': thumbnail_url,
            'audio_url': audio_url,
            'duration': self.duration,
            'author': {
                'id': self.author.id,
                'email': self.author.email
            } if self.author else None,
            'categories': [category.to_dict() for category in self.categories],
            'likes_count': len(self.likes),
            'slug': self.slug,
            'published': self.published,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 