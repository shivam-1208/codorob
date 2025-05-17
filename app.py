from flask import Flask, render_template, request, jsonify
from chat_agent import agent  # Your existing LangChain agent

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("chat.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    prompt = data.get("prompt", "")

    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    try:
        response = agent.run(prompt)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
