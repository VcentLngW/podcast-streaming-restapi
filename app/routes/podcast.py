import os
from flask import Blueprint, request, jsonify, current_app, send_from_directory, send_file
from werkzeug.utils import secure_filename
from app import db
from app.models.podcast import Podcast
from app.models.category import Category
from app.models.comment import Comment
from mutagen import File as MutagenFile
from app.utils.file_handlers import (
    save_file, 
    ALLOWED_AUDIO_EXTENSIONS, 
    ALLOWED_IMAGE_EXTENSIONS
)
from app.routes.auth import token_required
from sqlalchemy import func
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.podcast_listen import PodcastListen
from sqlalchemy.exc import IntegrityError
from datetime import datetime

podcast_bp = Blueprint('podcast', __name__)

@podcast_bp.route('/podcasts/<podcast_id>/comments', methods=['POST'])
@token_required
def add_comment(current_user, podcast_id):
    podcast = Podcast.query.get_or_404(podcast_id)
    data = request.get_json()
    
    if not data or not data.get('content'):
        return jsonify({'message': 'Comment content is required'}), 400
    
    # Debug: Print request data
    print(f"Adding comment to podcast {podcast_id}")
    print(f"Request data: {data}")
    print(f"Current user: {current_user.id}")
    
    comment = Comment(
        content=data['content'],
        podcast_id=podcast_id,
        user_id=current_user.id,
        parent_id=data.get('parent_id')  # Optional parent comment ID for replies
    )
    
    db.session.add(comment)
    db.session.commit()
    
    # Debug: Print created comment
    print(f"Created comment: {comment.to_dict()}")
    
    return jsonify({
        'message': 'Comment added successfully',
        'comment': comment.to_dict()
    }), 201

@podcast_bp.route('/podcasts/<podcast_id>/comments', methods=['GET'])
def get_comments(podcast_id):
    # First, verify the podcast exists
    podcast = Podcast.query.get_or_404(podcast_id)
    print(f"\n=== Debug: Getting comments for podcast {podcast_id} ===")
    
    # Get all comments for this podcast without any filters first
    all_comments = Comment.query.filter_by(podcast_id=podcast_id).all()
    print(f"Raw comments found: {len(all_comments)}")
    for comment in all_comments:
        print(f"Comment ID: {comment.id}, Content: {comment.content}, User ID: {comment.user_id}")
    
    # Now try the paginated query
    try:
        comments = Comment.query.filter_by(podcast_id=podcast_id)\
            .order_by(Comment.created_at.desc())\
            .paginate(page=1, per_page=10)
        
        print(f"\nPaginated query results:")
        print(f"Total items: {comments.total}")
        print(f"Items on current page: {len(comments.items)}")
        print(f"Current page: {comments.page}")
        print(f"Total pages: {comments.pages}")
        
        # Convert comments to dict and print for debugging
        comments_list = [comment.to_dict() for comment in comments.items]
        print(f"\nComments being returned: {comments_list}")
        
        return jsonify({
            'comments': comments_list,
            'total': comments.total,
            'pages': comments.pages,
            'current_page': comments.page
        }), 200
        
    except Exception as e:
        print(f"\nError in pagination: {str(e)}")
        # Fallback to non-paginated response if pagination fails
        return jsonify({
            'comments': [comment.to_dict() for comment in all_comments],
            'total': len(all_comments),
            'pages': 1,
            'current_page': 1
        }), 200

@podcast_bp.route('/podcasts/<podcast_id>/comments/<comment_id>', methods=['DELETE'])
@token_required
def delete_comment(current_user, podcast_id, comment_id):
    comment = Comment.query.get_or_404(comment_id)
    
    # Check if the comment belongs to the podcast
    if comment.podcast_id != podcast_id:
        return jsonify({'message': 'Comment not found'}), 404
        
    # Check if the user is the comment author
    if comment.user_id != current_user.id:
        return jsonify({'message': 'You can only delete your own comments'}), 403
        
    db.session.delete(comment)
    db.session.commit()
    
    return jsonify({'message': 'Comment deleted successfully'}), 200

@podcast_bp.route('/test', methods=['GET'])
def test():
    return jsonify({'message': 'Podcast routes are working!'}), 200

@podcast_bp.route('/podcasts/<podcast_id>/like', methods=['POST'])
@token_required
def like_podcast(current_user, podcast_id):
    podcast = Podcast.query.get_or_404(podcast_id)
    
    if current_user in podcast.likes:
        return jsonify({'message': 'You have already liked this podcast'}), 400
        
    podcast.likes.append(current_user)
    db.session.commit()
    
    return jsonify({
        'message': 'Podcast liked successfully',
        'likes_count': len(podcast.likes)
    }), 200

@podcast_bp.route('/podcasts/<podcast_id>/unlike', methods=['POST'])
@token_required
def unlike_podcast(current_user, podcast_id):
    podcast = Podcast.query.get_or_404(podcast_id)
    
    if current_user not in podcast.likes:
        return jsonify({'message': 'You have not liked this podcast'}), 400
        
    podcast.likes.remove(current_user)
    db.session.commit()
    
    return jsonify({
        'message': 'Podcast unliked successfully',
        'likes_count': len(podcast.likes)
    }), 200



#create a new podcast
@podcast_bp.route('/podcasts', methods=['POST'])
@token_required
def create_podcast(current_user):
    try:
        print("\n=== DEBUG: PODCAST CREATION START ===")
        print(f"Current user: {current_user.id}")
        
        # Print all incoming form data
        print("\n--- INCOMING FORM DATA ---")
        for key, value in request.form.items():
            print(f"Form field '{key}': {value}")
        
        # Print all incoming files
        print("\n--- INCOMING FILES ---")
        for key, file in request.files.items():
            print(f"File '{key}': {file.filename} ({file.content_type})")
        
        # Get form data
        title = request.form.get('title')
        description = request.form.get('description')
        
        print(f"\n--- EXTRACTED BASIC DATA ---")
        print(f"Title: {title}")
        print(f"Description: {description}")
        
        # Handle categories - support both categories[] and categories format
        category_ids = []
        print("\n--- CATEGORY PROCESSING ---")
        print("All form keys:", list(request.form.keys()))
        
        for key in request.form:
            if key == 'categories[]' or key == 'categories':
                values = request.form.getlist(key)
                print(f"Found category key '{key}' with values: {values}")
                category_ids.extend(values)
        
        print(f"Raw category_ids before processing: {category_ids}")
        
        # Convert category IDs to strings and remove duplicates
        # Since we're using UUIDs now, we don't need to convert to int
        category_ids = list(set(category_ids))
        print(f"Processed category_ids (unique): {category_ids}")
        
        # Validate required fields
        if not title:
            print("ERROR: Title is missing")
            return jsonify({'message': 'Title is required'}), 400
            
        # Handle file uploads
        audio_file = request.files.get('audio')
        thumbnail_file = request.files.get('thumbnail')
        
        print(f"\n--- FILE VALIDATION ---")
        print(f"Audio file present: {audio_file is not None}")
        print(f"Thumbnail file present: {thumbnail_file is not None}")
        
        if not audio_file:
            print("ERROR: Audio file is missing")
            return jsonify({'message': 'Audio file is required'}), 400
        if not thumbnail_file:
            print("ERROR: Thumbnail file is missing")
            return jsonify({'message': 'Thumbnail file is required'}), 400
            
        # Save files
        print("\n--- FILE SAVING ---")
        audio_path = save_file(
            audio_file, 
            os.path.join(current_app.config['UPLOAD_FOLDER'], 'audio'),
            ALLOWED_AUDIO_EXTENSIONS
        )
        print(f"Audio saved to: {audio_path}")

        try:
            audio_file_mutagen = MutagenFile(audio_path)
            audio_duration = audio_file_mutagen.info.length
            seconds = round(audio_duration)
            print(f"Audio duration: {audio_duration} seconds")
        except Exception as e:
            print(f"Error getting audio duration: {str(e)}")
            return jsonify({'message': 'Error getting audio duration'}), 500

        
        thumbnail_path = save_file(
            thumbnail_file, 
            os.path.join(current_app.config['UPLOAD_FOLDER'], 'thumbnails'),
            ALLOWED_IMAGE_EXTENSIONS
        )
        print(f"Thumbnail saved to: {thumbnail_path}")
        
        if not audio_path or not thumbnail_path:
            print("ERROR: Invalid file type")
            return jsonify({'message': 'Invalid file type'}), 400
        
        print("\n--- PODCAST CREATION ---")
        # Create podcast with relative paths
        podcast = Podcast(
            title=title,
            description=description,
            audio_url=os.path.relpath(audio_path, current_app.config['UPLOAD_FOLDER']),
            thumbnail_url=os.path.relpath(thumbnail_path, current_app.config['UPLOAD_FOLDER']),
            author_id=current_user.id,
            duration=seconds
        )
        print(f"Podcast object created with ID: {podcast.id}")
        
        # Add categories
        print(f"\n--- CATEGORY ASSOCIATION ---")
        print(f"Attempting to associate {len(category_ids)} categories")
        if category_ids:
            print(f"Looking for categories with IDs: {category_ids}")
            categories = Category.query.filter(Category.id.in_(category_ids)).all()
            print(f"Found {len(categories)} categories in database")
            for cat in categories:
                print(f"  - Category: {cat.name} (ID: {cat.id})")
            
            podcast.categories.extend(categories)
            print(f"Categories associated with podcast")
        else:
            print("No categories to associate")
        
        print("\n--- DATABASE COMMIT ---")
        db.session.add(podcast)
        db.session.commit()
        print(f"Podcast saved to database with ID: {podcast.id}")
        
        print("\n--- RESPONSE ---")
        podcast_dict = podcast.to_dict()
        print(f"Returning podcast data: {podcast_dict}")
        
        print("=== DEBUG: PODCAST CREATION END ===\n")
        
        return jsonify({
            'message': 'Podcast created successfully',
            'podcast': podcast_dict
        }), 201
        
    except Exception as e:
        print(f"\n=== ERROR IN PODCAST CREATION ===")
        print(f"Error: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        print("=== ERROR END ===\n")
        db.session.rollback()
        return jsonify({'message': str(e)}), 500


# get the podcast by id
@podcast_bp.route('/podcasts/<podcast_id>', methods=['GET'])
def get_podcast(podcast_id):
    podcast = Podcast.query.get_or_404(podcast_id)
    return jsonify(podcast.to_dict()), 200


# Check if podcast is liked by user
@podcast_bp.route('/podcasts/<podcast_id>/check-like', methods=['GET'])
@token_required
def check_podcast_like(current_user, podcast_id):
    podcast = Podcast.query.get_or_404(podcast_id)
    is_liked = current_user in podcast.likes
    
    return jsonify({
        'is_liked': is_liked,
        'likes_count': len(podcast.likes)
    }), 200


# Delete podcast route
@podcast_bp.route('/podcasts/<podcast_id>', methods=['DELETE'])
@token_required
def delete_podcast(current_user, podcast_id):
    podcast = Podcast.query.get_or_404(podcast_id)

    # Authorization: Only the author can delete
    if podcast.author_id != current_user.id:
        return jsonify({'message': 'You are not authorized to delete this podcast'}), 403

    try:
        # Remove likes manually from association table
        podcast.likes.clear()

        # Remove category associations
        podcast.categories.clear()

        # Manually delete comments (if cascade isn't set)
        Comment.query.filter_by(podcast_id=podcast_id).delete()

        # Optionally delete associated files from disk
        upload_folder = current_app.config['UPLOAD_FOLDER']
        thumbnail_path = os.path.join(upload_folder, podcast.thumbnail_url)
        audio_path = os.path.join(upload_folder, podcast.audio_url)
        for file_path in [thumbnail_path, audio_path]:
            if os.path.exists(file_path):
                os.remove(file_path)

        db.session.delete(podcast)
        db.session.commit()

        return jsonify({'message': 'Podcast deleted successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error deleting podcast: {str(e)}'}), 500


@podcast_bp.route('/podcasts', methods=['GET'])
def get_podcasts():
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    category_id = request.args.get('category_id')  # Now a string UUID
    search = request.args.get('search', '')
    
    # Build query
    query = Podcast.query
    
    # Apply filters
    if category_id:
        query = query.filter(Podcast.categories.any(id=category_id))
    if search:
        query = query.filter(Podcast.title.ilike(f'%{search}%'))
    
    # Get paginated results
    podcasts = query.order_by(Podcast.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return jsonify({
        'podcasts': [podcast.to_dict() for podcast in podcasts.items],
        'total': podcasts.total,
        'pages': podcasts.pages,
        'current_page': podcasts.page
    }), 200 


@podcast_bp.route('/podcasts/discover', methods=['GET'])
def discover_podcasts():
    """
    Discover podcasts, always sorted by total engagement (likes + comments), descending.
    Query params:
      - page: int (default 1)
      - per_page: int (default 10)
      - category_id: str (optional, UUID)
      - search: str (optional)
    """
    from sqlalchemy import func
    from app.models.comment import Comment
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    category_id = request.args.get('category_id')  # Now a string UUID
    search = request.args.get('search', '')

    query = Podcast.query

    if category_id:
        query = query.filter(Podcast.categories.any(id=category_id))
    if search:
        query = query.filter(Podcast.title.ilike(f'%{search}%'))

    # Subquery for comment count
    comment_count_subq = db.session.query(
        Comment.podcast_id,
        func.count(Comment.id).label('comments_count')
    ).group_by(Comment.podcast_id).subquery()
    # Join likes and comments count, order by (likes + comments)
    query = query \
        .outerjoin(Podcast.likes) \
        .outerjoin(comment_count_subq, Podcast.id == comment_count_subq.c.podcast_id) \
        .group_by(Podcast.id) \
        .order_by((func.count().label('likes_count') + func.coalesce(comment_count_subq.c.comments_count, 0)).desc(), Podcast.created_at.desc())

    podcasts = query.paginate(page=page, per_page=per_page)

    return jsonify({
        'podcasts': [podcast.to_dict() for podcast in podcasts.items],
        'total': podcasts.total,
        'pages': podcasts.pages,
        'current_page': podcasts.page
    }), 200

@podcast_bp.route('/uploads/thumbnails/<path:filename>')
def serve_thumbnail(filename):
    return send_from_directory('uploads/thumbnails', filename)

@podcast_bp.route('/uploads/audio/<path:filename>')
def serve_audio(filename):
    return send_from_directory('uploads/audio', filename)

@podcast_bp.route('/podcasts/<podcast_id>/stream', methods=['GET'])
def stream_podcast_audio(podcast_id):
    """
    Stream audio file for a specific podcast by ID.
    Supports HTTP Range headers for proper audio streaming.
    Returns last listened position if user has listened before.
    """
    try:
        # Get the podcast
        podcast = Podcast.query.get_or_404(podcast_id)
        
        # Debug: Print podcast info
        print(f"Podcast ID: {podcast_id}")
        print(f"Audio URL from DB: {podcast.audio_url}")
        
        # Check for user's listen record if authenticated
        last_position = None
        try:
            from flask_jwt_extended import get_jwt_identity
            user_id = get_jwt_identity()
            if user_id:
                listen_record = PodcastListen.query.filter_by(
                    user_id=user_id,
                    podcast_id=podcast_id
                ).first()
                if listen_record:
                    last_position = listen_record.time_listened
                    print(f"Found listen record for user {user_id}: {last_position} seconds")
        except Exception as e:
            print(f"Error checking listen record: {e}")
        
        # Construct the full path to the audio file
        upload_folder = current_app.config['UPLOAD_FOLDER']
        print(f"Upload folder: {upload_folder}")
        
        # The audio_url is stored as a relative path like 'audio/filename.mp3'
        audio_path = os.path.join(upload_folder, podcast.audio_url)
        print(f"Constructed audio path: {audio_path}")
        
        # Check if the audio file exists
        if not os.path.exists(audio_path):
            print(f"Audio file not found at: {audio_path}")
            return jsonify({'message': 'Audio file not found'}), 404
        
        print(f"Audio file found, size: {os.path.getsize(audio_path)} bytes")
        
        # Get file info for proper headers
        file_size = os.path.getsize(audio_path)
        file_name = os.path.basename(audio_path)
        
        # Set up response headers for audio streaming
        headers = {
            'Accept-Ranges': 'bytes',
            'Content-Length': str(file_size),
            'Content-Type': 'audio/mpeg',  # Adjust based on your audio format
            'Cache-Control': 'public, max-age=31536000',  # Cache for 1 year
        }
        
        # Add last position header if available
        if last_position is not None:
            headers['X-Last-Position'] = str(last_position)
        
        # Handle Range requests for streaming
        range_header = request.headers.get('Range', None)
        
        if range_header:
            # Parse range header (e.g., "bytes=0-1023")
            try:
                range_str = range_header.replace('bytes=', '')
                start, end = range_str.split('-')
                start = int(start)
                end = int(end) if end else file_size - 1
                
                # Validate range
                if start >= file_size or end >= file_size or start > end:
                    return jsonify({'message': 'Invalid range'}), 416
                
                # Calculate content length for this range
                content_length = end - start + 1
                
                # Update headers for partial content
                headers.update({
                    'Content-Length': str(content_length),
                    'Content-Range': f'bytes {start}-{end}/{file_size}',
                })
                
                # Return partial content
                response = send_file(
                    audio_path,
                    mimetype='audio/mpeg',
                    as_attachment=False,
                    download_name=file_name,
                    conditional=True,
                    etag=True,
                    max_age=31536000
                )
                
                # Add our custom headers
                for key, value in headers.items():
                    response.headers[key] = value
                
                return response, 206
                
            except (ValueError, IndexError):
                return jsonify({'message': 'Invalid range format'}), 416
        
        # Return full file for non-range requests
        response = send_file(
            audio_path,
            mimetype='audio/mpeg',
            as_attachment=False,
            download_name=file_name,
            conditional=True,
            etag=True,
            max_age=31536000
        )
        
        # Add our custom headers
        for key, value in headers.items():
            response.headers[key] = value
        
        return response
        
    except Exception as e:
        print(f"Error streaming podcast {podcast_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': 'Error streaming audio file'}), 500

@podcast_bp.route('/podcasts/<podcast_id>/track', methods=['POST'])
@jwt_required()
def track_podcast_listen(podcast_id):
    from flask import request
    data = request.get_json()
    time_listened = data.get('time_listened')
    user_id = get_jwt_identity()

    if not isinstance(time_listened, (int, float)) or time_listened < 0:
        return jsonify({'message': 'Invalid time_listened value.'}), 400

    try:
        # Attempt to create a new listen record
        listen = PodcastListen(
            user_id=user_id,
            podcast_id=podcast_id,
            time_listened=int(time_listened),
            tracked_at=datetime.utcnow()
        )
        db.session.add(listen)
        db.session.commit()
        return jsonify({'message': 'Listen tracked successfully (new record).'}), 201

    except IntegrityError:
        # This block executes if the (user_id, podcast_id) pair already exists
        db.session.rollback()  # Rollback the failed insert

        # Find the existing record
        listen = PodcastListen.query.filter_by(
            user_id=user_id,
            podcast_id=podcast_id
        ).first()

        # Update it only if the new time is greater
        if listen and time_listened > listen.time_listened:
            listen.time_listened = int(time_listened)
            listen.tracked_at = datetime.utcnow()  # Update the timestamp
            db.session.commit()
            return jsonify({'message': 'Listen tracked successfully (updated).'}), 200
        else:
            # The existing record has a longer or equal listen time, so do nothing.
            return jsonify({'message': 'Existing listen time is longer or equal, no update needed.'}), 200

@podcast_bp.route('/podcasts/<podcast_id>/last-position', methods=['GET'])
@jwt_required()
def get_last_listened_position(podcast_id):
    """
    Get the last listened position for a specific podcast.
    Returns the time in seconds where the user last stopped listening.
    """
    try:
        user_id = get_jwt_identity()
        
        # Check if podcast exists
        podcast = Podcast.query.get_or_404(podcast_id)
        
        # Get the user's listen record for this podcast
        listen_record = PodcastListen.query.filter_by(
            user_id=user_id,
            podcast_id=podcast_id
        ).first()
        
        if listen_record:
            return jsonify({
                'last_position': listen_record.time_listened,
                'tracked_at': listen_record.tracked_at.isoformat() if listen_record.tracked_at else None,
                'has_listened': True
            }), 200
        else:
            return jsonify({
                'last_position': 0,
                'tracked_at': None,
                'has_listened': False
            }), 200
            
    except Exception as e:
        return jsonify({'message': f'Error getting last position: {str(e)}'}), 500