import google.generativeai as genai
import json
import pandas as pd
from dotenv import load_dotenv
import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
import re
from PIL import Image
import base64
import io

load_dotenv()

app = Flask(__name__)
UPLOAD_FOLDER = "static/uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
API_KEY = os.getenv("API_KEY")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

@app.route('/')  # Dashboard/home
def dashboard():
    return render_template('chat.html')

@app.route('/events.html')
def event():
    return render_template('Events.html')

@app.route('/Addprod.html')
def addprod():
    return render_template('Addprod.html')

@app.route('/chat.html')
def chat():
    return render_template('chat.html')

@app.route('/settings.html')
def setting():
    return render_template('Settings.html')

@app.route('/AI.html')
def ai_interface():
    return render_template('AI.html')

@app.route('/charts.html')
def history():
    return render_template('history.html')

# Fixed API endpoint for chat
@app.route('/api/chat', methods=['POST'])
def api_chat():
    try:
        data = request.get_json()
        message = data.get('message', '')
        image_data = data.get('image', None)
        
        if image_data:
            # Process base64 image data
            image_bytes = base64.b64decode(image_data.split(',')[1])
            answer = query_with_image(message, image_bytes=image_bytes)
        else:
            answer = query_with_image(message)
        
        return jsonify({
            'success': True,
            'response': answer
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/ai-chat', methods=['GET', 'POST'])
def ai_chat():
    answer = None
    img_url = None
    user_message = None
    if request.method == 'POST':
        user_message = request.form.get('question', '')
        image = request.files.get('image')
        if image and image.filename != '':
            img_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
            image.save(img_path)
            img_url = url_for('static', filename=f'uploads/{image.filename}')
            answer = query_with_image(user_message, img_path)
        else:
            answer = query_with_image(user_message)
    return render_template('AI.html', answer=answer, img_url=img_url, user_message=user_message)

def query_with_image(user_question, image_path=None, image_bytes=None):
    """
    Handle both text-only and image+text queries
    """
    prompt = f"""
    User will enter an image and will ask question related to that art image he/she shared,
    Suggest him according to the question asked related to image which is related more to
    naming it, describing it, market it, price of it according to the trend, platform guidance for Meesho, Amazon Karigar, Etsy (here suggest him some youtube tutorial for creation of seller account in those platforms & guide accordingly).
    If no image is been shared then answer the questions in general which is related to Art, handicrafts, handmade products, handlooms, pottery, etc.
    And don't answer anything else from that.
    Question: {user_question}
    Answer in a friendly and natural way:
    """

    try:
        if image_path is not None:
            # Handle file path
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            print(f"Analyzing image: {image_path}")
            response = model.generate_content([prompt, {"mime_type": "image/jpeg", "data": image_bytes}])
            return response.text
        elif image_bytes is not None:
            # Handle image bytes directly
            print("Analyzing uploaded image...")
            response = model.generate_content([prompt, {"mime_type": "image/jpeg", "data": image_bytes}])
            return response.text
        else:
            # Text-only query
            print("Processing text-only query...")
            response = model.generate_content(prompt)
            return response.text

    except Exception as e:
        return f"Error processing request: {str(e)}"

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)