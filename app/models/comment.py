from datetime import datetime
from app import db
import uuid

class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    content = db.Column(db.Text, nullable=False)
    podcast_id = db.Column(db.String(36), db.ForeignKey('podcasts.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    parent_id = db.Column(db.String(36), db.ForeignKey('comments.id'), nullable=True)  # For nested comments
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    podcast = db.relationship('Podcast', backref=db.backref('comments', lazy=True))
    user = db.relationship('User', backref=db.backref('comments', lazy=True))
    replies = db.relationship('Comment', 
                            backref=db.backref('parent', remote_side=[id]),
                            lazy='dynamic', cascade='all, delete-orphan')

    def __init__(self, content, podcast_id, user_id, parent_id=None):
        self.content = content
        self.podcast_id = podcast_id
        self.user_id = user_id
        self.parent_id = parent_id

    def __repr__(self):
        return f'<Comment {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'podcast_id': self.podcast_id,
            'user': {
                'id': self.user.id,
                'email': self.user.email
            } if self.user else None,
            'parent_id': self.parent_id,
            'replies_count': self.replies.count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 