from flask import Flask, request, send_from_directory, jsonify
from flask_cors import CORS
from gradio_client import Client, handle_file
import os
from werkzeug.utils import secure_filename
import shutil

app = Flask(__name__, static_folder='.')
CORS(app)  # Enable CORS for all routes

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/upload', methods=['POST', 'OPTIONS'])  # Added OPTIONS method
def upload_file():
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    file = request.files['audio']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Secure the filename and save temporarily
    filename = secure_filename(file.filename)
    temp_path = os.path.join('temp', filename)
    
    # Create temp directory if it doesn't exist
    os.makedirs('temp', exist_ok=True)
    os.makedirs('audio_outputs', exist_ok=True)
    
    file.save(temp_path)

    try:
        # Process the audio using the existing function
        output_path, text_response = predict_and_save_audio(temp_path)
        
        # Get just the filename from the output path
        output_filename = os.path.basename(output_path)
        
        # Clean up temp file
        os.remove(temp_path)
        
        return jsonify({
            'success': True,
            'text': text_response,
            'audioUrl': f'/audio_outputs/{output_filename}'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/audio_outputs/<filename>')
def serve_audio(filename):
    return send_from_directory('audio_outputs', filename)

def predict_and_save_audio(input_file, output_dir='audio_outputs'):
    # Initialize client
    client = Client("adnaan05/VoiceToVoice_ChatBot")
    
    # Get prediction
    result = client.predict(
        file_path=handle_file(input_file),
        api_name="/predict"
    )
    
    # Extract the audio file path from the result tuple
    text_response, temp_path = result
    
    # Generate output filename
    output_filename = f"response_{os.path.basename(input_file)}"
    output_path = os.path.join(output_dir, output_filename)
    
    # Copy the file from temp location to desired location
    if os.path.exists(temp_path):
        shutil.copy2(temp_path, output_path)
    else:
        raise Exception("Generated audio file not found")
    
    return output_path, text_response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))