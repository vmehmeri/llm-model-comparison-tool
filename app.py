from flask import Flask, render_template, request, jsonify
import os
from openai import OpenAI
from anthropic import Anthropic
import google.generativeai as genai
import markdown2
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///votes.db'
db = SQLAlchemy(app)

# Set up API clients
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

class Votes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(20), nullable=False)
    votes = db.Column(db.Integer, default=0)

with app.app_context():
    db.create_all()
    for model in ['gpt4', 'claude', 'gemini']:
        if not Votes.query.filter_by(model=model).first():
            db.session.add(Votes(model=model))
    db.session.commit()

@app.route('/')
def index():
    votes = {vote.model: vote.votes for vote in Votes.query.all()}
    return render_template('index.html', votes=votes)

@app.route('/generate', methods=['POST'])
def generate():
    prompt = request.json['prompt']

    # Generate responses from all three models
    print("--> Prompting GPT4o")
    gpt4_response = generate_gpt4(prompt)
    print("<-- Got response", gpt4_response)
    print("Prompting Gemini")
    gemini_response = generate_gemini(prompt)
    print("<-- Got response", gemini_response)
    print("--> Prompting Claude")
    claude_response = generate_claude(prompt)
    print("<-- Got response", claude_response)

    return jsonify({
        'gpt4': gpt4_response,
        'claude': claude_response,
        'gemini': gemini_response
    })

@app.route('/vote', methods=['POST'])
def vote():
    model = request.json['model']
    vote = Votes.query.filter_by(model=model).first()
    vote.votes += 1
    db.session.commit()
    
    votes = {vote.model: vote.votes for vote in Votes.query.all()}
    return jsonify(votes)

@app.route('/reset-votes', methods=['POST'])
def reset_votes():
    try:
        Votes.query.update({Votes.votes: 0})
        db.session.commit()
        votes = {vote.model: vote.votes for vote in Votes.query.all()}
        return jsonify(votes)
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def generate_gpt4(prompt):
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-2024-05-13",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as gpt_excp:
        print(gpt_excp)
        return "Failed to generate response."


def generate_claude(prompt):
    try:
        message = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            max_tokens=1024
        )
        return message.content[0].text
    except Exception as claude_excp:
        print(claude_excp)
        return "Failed to generate response"

def generate_gemini(prompt):
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(prompt)
        markdown_text = response.text
        html_content = markdown2.markdown(markdown_text)  # Convert Markdown to HTML
        return html_content
    except Exception as gemini_excp:
        print(gemini_excp)
        return "Failed to generate response."


if __name__ == '__main__':
    app.run(debug=True)