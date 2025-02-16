import os
import uuid  # Generate unique session IDs
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from flask_cors import CORS  # ✅ Import CORS

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("❌ GEMINI_API_KEY is missing! Set it in .env or environment variables.")
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-pro")

# ✅ Initialize Flask app
app = Flask(__name__)
CORS(app)

SESSIONS = {}

def call_gemini_chat(session_id, user_input):
    """Calls Google Gemini API with conversation history and user input."""
    
    # Get or initialize conversation context
    context = SESSIONS.get(session_id, [])

    # Append new user message
    messages = context + [{"role": "user", "parts": [{"text": user_input}]}]

    # Call Gemini API
    response = model.generate_content(messages)

    # Extract AI's response
    bot_response = response.text if response.text else "I'm not sure how to respond."

    # Update session with AI response
    context.append({"role": "user", "parts": [{"text": user_input}]})
    context.append({"role": "model", "parts": [{"text": bot_response}]})

    # Store updated conversation
    SESSIONS[session_id] = context

    return bot_response

@app.route("/")
def home():
    """Render the HTML page."""
    return render_template("index.html")

@app.route("/new_session", methods=["POST"])
def new_session():
    """Creates a new chat session and returns the session ID."""
    session_id = str(uuid.uuid4())  # ✅ Generate a unique session ID
    SESSIONS[session_id] = []  # ✅ Initialize an empty chat session
    return jsonify({"sessionId": session_id, "message": "New session created."})

@app.route("/chat", methods=["POST"])
def chat():
    """Handles chat requests via API."""
    data = request.get_json()
    
    user_input = data.get("userMessage")
    session_id = data.get("sessionId")

    if not user_input:
        return jsonify({"error": "Missing userMessage"}), 400
    if not session_id:
        return jsonify({"error": "Missing sessionId"}), 400
    if session_id not in SESSIONS:
        return jsonify({"error": "Session ID not found. Please create a new session first."}), 404

    bot_response = call_gemini_chat(session_id, user_input)

    return jsonify({
        "sessionId": session_id,
        "response": bot_response
    })

@app.route("/end_session", methods=["POST"])
def end_session():
    """Clears the chat session from memory."""
    data = request.get_json()
    session_id = data.get("sessionId")

    if not session_id:
        return jsonify({"error": "Missing sessionId"}), 400
    if session_id in SESSIONS:
        del SESSIONS[session_id]  # ✅ Remove session data
        return jsonify({"message": f"Session {session_id} ended successfully."})
    else:
        return jsonify({"error": "Session not found."}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
