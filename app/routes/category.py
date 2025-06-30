from flask import Blueprint, request, jsonify
from app import db
from app.models.category import Category

category_bp = Blueprint('category', __name__)

@category_bp.route('/categories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    return jsonify({
        'categories': [category.to_dict() for category in categories]
    }), 200

@category_bp.route('/categories/<category_id>', methods=['GET'])
def get_category(category_id):
    category = Category.query.get(category_id)
    if not category:
        return jsonify({'message': 'Category not found'}), 404
    return jsonify(category.to_dict()), 200

@category_bp.route('/categories', methods=['POST'])
def create_category():
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    if not name:
        return jsonify({'message': 'Category name is required'}), 400
    if Category.query.filter_by(name=name).first():
        return jsonify({'message': 'Category already exists'}), 400
    category = Category(name=name, description=description)
    db.session.add(category)
    db.session.commit()
    return jsonify({'message': 'Category created', 'category': category.to_dict()}), 201

@category_bp.route('/categories/<category_id>', methods=['DELETE'])
def delete_category(category_id):
    category = Category.query.get(category_id)
    if not category:
        return jsonify({'message': 'Category not found'}), 404
    db.session.delete(category)
    db.session.commit()
    return jsonify({'message': 'Category deleted'}), 200 