from flask import Flask, request, jsonify, abort, send_file
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

products = {}
UPLOAD_FOLDER = 'images'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
next_id = 1

@app.route('/product', methods=['POST'])
def create_product():
    global next_id
    
    if not request.json or 'name' not in request.json:
        abort(400, description="Name is required")
    
    product = {
        'id': next_id,
        'name': request.json['name'],
        'description': request.json.get('description', ''),
        'icon': None
    }
    
    products[next_id] = product
    next_id += 1
    
    return jsonify(product), 201

@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = products.get(product_id)
    if product is None:
        abort(404, description="Product not found")
    return jsonify(product)

@app.route('/product/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    product = products.get(product_id)
    if product is None:
        abort(404, description="Product not found")
        
    if not request.json:
        abort(400, description="Request body must be JSON")
        
    update_data = request.json
    if 'name' in update_data:
        product['name'] = update_data['name']
    if 'description' in update_data:
        product['description'] = update_data['description']
    
    return jsonify(product)

@app.route('/product/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    product = products.get(product_id)
    if product is None:
        abort(404, description="Product not found")
    
    del products[product_id]
    return jsonify(product)

@app.route('/products', methods=['GET'])
def get_all_products():
    return jsonify(list(products.values()))


@app.route('/product/<int:product_id>/image', methods=['POST'])
def upload_icon(product_id):
    product = products.get(product_id)
    if product is None:
        abort(404, description="Product not found")
    
    if 'icon' not in request.files:
        abort(400, description="No 'icon' part in request")
    
    file = request.files['icon']
    if file.filename == '':
        abort(400, description="No selected file")
        
    if file:
        filename = secure_filename(f"product_{product_id}.png")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        product['icon'] = filepath
        return jsonify({'message': 'Icon uploaded successfully'}), 200

@app.route('/product/<int:product_id>/image', methods=['GET'])
def get_icon(product_id):
    product = products.get(product_id)
    if product is None or product['icon'] is None:
        abort(404, description="Product or icon not found")
    return send_file(product['icon'], mimetype='image/png')
    
@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': str(error.description)}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': str(error.description)}), 404

if __name__ == '__main__':
    app.run(debug=True)