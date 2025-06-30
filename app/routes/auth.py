from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from app import db
from app.models.user import User
from app.models.podcast_listen import PodcastListen
from app.utils.email import send_verification_email, send_reset_password_email, send_welcome_email
from app.utils.password import hash_password, verify_password, is_password_strong
from datetime import datetime, UTC, timedelta
import jwt
import os
from functools import wraps
from sqlalchemy import func
from app.models.podcast import Podcast

auth_bp = Blueprint('auth', __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Invalid token format'}), 401

        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            data = jwt.decode(token, os.getenv('JWT_SECRET_KEY', 'jwt-secret-key'), algorithms=["HS256"])
            current_user = User.query.get(data['sub'])  # data['sub'] is now a UUID string
            if not current_user:
                return jsonify({'message': 'User not found'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401

        return f(current_user, *args, **kwargs)
    return decorated

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    
    # Validate required fields
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400
    
    # Check if email already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    # Validate password strength
    is_strong, error_message = is_password_strong(data['password'])
    if not is_strong:
        return jsonify({'error': error_message}), 400
    
    # Hash password and create user
    user = User(
        email=data['email'],
        password=hash_password(data['password'])
    )
    db.session.add(user)
    db.session.commit()
    
    send_verification_email(user)
    return jsonify({'message': 'Registration successful. Please check your email to verify your account.'}), 201

@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    try:
        data = request.get_json()
        email = data.get('email')
        otp = data.get('otp')
    except:
        return jsonify({'error': 'Invalid request body'}), 400
    
    if not email or not otp:
        return jsonify({'error': 'Email and OTP are required'}), 400
    
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if not user.otp or not user.otp_expiry:
        return jsonify({'error': 'No OTP found or OTP expired'}), 400
    
    current_time = datetime.now(UTC)
    if user.otp_expiry < current_time:
        return jsonify({'error': 'OTP has expired'}), 400
    
    if user.otp != otp:
        return jsonify({'error': 'Invalid OTP'}), 400
    
    user.is_verified = True
    user.otp = None
    user.otp_expiry = None
    db.session.commit()
    
    send_welcome_email(user)
    return jsonify({'message': 'Email verified successfully'}), 200

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing required fields'}), 400
        
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not verify_password(data['password'], user.password):
        return jsonify({'message': 'Invalid credentials'}), 401
        
    # Create token payload
    payload = {
        'sub': str(user.id),
        'exp': datetime.utcnow() + timedelta(days=1)
    }
    
    # Encode token
    token = jwt.encode(
        payload,
        os.getenv('JWT_SECRET_KEY', 'jwt-secret-key'),
        algorithm='HS256'
    )
    
    # Convert token to string if it's bytes
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    
    return jsonify({
        'message': 'Login successful',
        'token': token,
        'user': user.to_dict()
    }), 200

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    
    if not user:
        return jsonify({'error': 'Email not found'}), 404
    
    send_reset_password_email(user)
    return jsonify({'message': 'Password reset instructions sent to your email'}), 200

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    
    # Validate required fields
    if not data or not data.get('token') or not data.get('new_password'):
        return jsonify({'error': 'Token and new password are required'}), 400
    
    user = User.query.filter_by(reset_token=data['token']).first()
    
    current_time = datetime.now(UTC)
    if not user or not user.reset_token_expiry or user.reset_token_expiry < current_time:
        return jsonify({'error': 'Invalid or expired reset token'}), 400
    
    # Validate password strength
    is_strong, error_message = is_password_strong(data['new_password'])
    if not is_strong:
        return jsonify({'error': error_message}), 400
    
    # Hash and update password
    user.password = hash_password(data['new_password'])
    user.reset_token = None
    user.reset_token_expiry = None
    db.session.commit()
    
    return jsonify({'message': 'Password reset successfully'}), 200

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        current_user_id = get_jwt_identity()
        # current_user_id is now a UUID string
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        return jsonify({
            'email': user.email,
            'is_verified': user.is_verified
        }), 200
    except Exception as e:
        return jsonify({'message': f'Error accessing profile: {str(e)}'}), 401 

@auth_bp.route('/profile/podcasts', methods=['GET'])
@jwt_required()
def get_user_podcasts():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
        # Get podcasts authored by this user
        podcasts = user.podcasts  # Backref from Podcast model
        return jsonify({
            'podcasts': [podcast.to_dict() for podcast in podcasts]
        }), 200
    except Exception as e:
        return jsonify({'message': f'Error retrieving user podcasts: {str(e)}'}), 401

@auth_bp.route('/profile/liked-podcasts', methods=['GET'])
@jwt_required()
def get_liked_podcasts():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
        # Get podcasts liked by this user
        liked_podcasts = user.liked_podcasts  # Backref from Podcast model
        return jsonify({
            'podcasts': [podcast.to_dict() for podcast in liked_podcasts]
        }), 200
    except Exception as e:
        return jsonify({'message': f'Error retrieving liked podcasts: {str(e)}'}), 401

@auth_bp.route('/profile/details', methods=['GET'])
@jwt_required()
def get_profile_details():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
        # Efficiently gather profile stats
        podcasts_count = len(user.podcasts)
        liked_podcasts_count = len(user.liked_podcasts)
        followers_count = 0  # Placeholder, implement if follower model exists
        following_count = 0  # Placeholder, implement if following model exists
        
        # Calculate total listens across all podcasts authored by the user
        total_listens_count = db.session.query(func.sum(PodcastListen.time_listened)) \
            .join(Podcast, PodcastListen.podcast_id == Podcast.id) \
            .filter(Podcast.author_id == user.id).scalar() or 0
        
        return jsonify({
            'email': user.email,
            'is_verified': user.is_verified,
            'podcasts_count': podcasts_count,
            'liked_podcasts_count': liked_podcasts_count,
            'followers_count': followers_count,
            'following_count': following_count,
            'total_listens_count': total_listens_count,
        }), 200
    except Exception as e:
        return jsonify({'message': f'Error retrieving profile details: {str(e)}'}), 401

@auth_bp.route('/profile/listen-history', methods=['GET'])
@jwt_required()
def get_listen_history():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Get query parameters for pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Query PodcastListen directly with pagination
        listen_history = PodcastListen.query.filter_by(user_id=user.id)\
            .order_by(PodcastListen.tracked_at.desc())\
            .paginate(
                page=page, 
                per_page=per_page, 
                error_out=False
            )
        
        return jsonify({
            'listen_history': [listen.to_dict() for listen in listen_history.items],
            'total': listen_history.total,
            'pages': listen_history.pages,
            'current_page': listen_history.page,
            'per_page': per_page
        }), 200
    except Exception as e:
        return jsonify({'message': f'Error retrieving listen history: {str(e)}'}), 401 