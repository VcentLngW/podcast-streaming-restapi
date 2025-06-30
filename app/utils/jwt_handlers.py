from flask import jsonify

def register_jwt_handlers(jwt):
    @jwt.invalid_token_loader
    def invalid_token_callback(error_string):
        return jsonify({
            'message': f'Invalid token. Please log in again. Error: {error_string}'
        }), 401

    @jwt.unauthorized_loader
    def unauthorized_callback(error_string):
        return jsonify({
            'message': f'Missing Authorization Header. Error: {error_string}'
        }), 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'message': 'Token has expired'
        }), 401 