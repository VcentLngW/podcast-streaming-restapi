from app import db
from datetime import datetime
import uuid

class PodcastListen(db.Model):
    __tablename__ = 'podcast_listens'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    podcast_id = db.Column(db.String(36), db.ForeignKey('podcasts.id'), nullable=False)
    time_listened = db.Column(db.Integer, nullable=False)
    tracked_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'podcast_id', name='_user_podcast_uc'),)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'podcast_id': self.podcast_id,
            'time_listened': self.time_listened,
            'tracked_at': self.tracked_at.isoformat() if self.tracked_at else None,
            'podcast': self.podcast.to_dict() if self.podcast else None
        } 