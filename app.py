from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from gradio_client import Client, handle_file
import os
import base64
from io import BytesIO
from PIL import Image

app = Flask(__name__)
CORS(app)

# Initialize the client
client = Client("akhaliq/depth-pro")

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/styles.css')
def styles():
    return send_file('styles.css')

@app.route('/script.js')
def script():
    return send_file('script.js')

@app.route('/generate_depth_map', methods=['POST'])
def generate_depth_map():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    image_file = request.files['image']
    
    # Save the uploaded image temporarily
    temp_path = 'temp_input.png'
    image_file.save(temp_path)

    try:
        result = client.predict(
            input_image=handle_file(temp_path),
            api_name="/predict"
        )

        # Read the depth map image
        with open(result[0], 'rb') as f:
            depth_map_data = f.read()
        
        # Encode the depth map as base64
        depth_map_base64 = base64.b64encode(depth_map_data).decode('utf-8')

        # Get the focal length
        focal_length = result[1]

        # Clean up temporary files
        os.remove(temp_path)
        os.remove(result[0])

        return jsonify({
            'depth_map': depth_map_base64,
            'focal_length': focal_length
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)