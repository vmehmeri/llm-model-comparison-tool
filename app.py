from flask import Flask, render_template, request, jsonify, send_file
import os
import yaml
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
import google.generativeai as genai
from flask_sqlalchemy import SQLAlchemy
import csv
from io import BytesIO, StringIO
from datetime import datetime
import asyncio
import aiohttp

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///votes.db'
db = SQLAlchemy(app)

# Load configuration
with open('config.yaml', 'r') as config_file:
    config = yaml.safe_load(config_file)

# Set up API clients
openai_client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
anthropic_client = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

class Votes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(20), nullable=False)
    votes = db.Column(db.Integer, default=0)

class Response(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prompt = db.Column(db.Text, nullable=False)
    responses = db.Column(db.JSON, nullable=False)
    winner = db.Column(db.String(50), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()
    for model in config['models']:
        vote = Votes.query.filter_by(model=model['name']).first()
        if vote is None:
            db.session.add(Votes(model=model['name']))
    db.session.commit()

@app.route('/')
def index():
    votes = {vote.model: vote.votes for vote in Votes.query.all()}
    print(f"Initial votes: {votes}")  # Debug print
    return render_template('index.html', models=config['models'], votes=votes)

@app.route('/generate', methods=['POST'])
async def generate():
    prompt = request.json['prompt']
    responses = await generate_responses(prompt)

    # Store the responses in the database
    new_response = Response(prompt=prompt, responses=responses)
    db.session.add(new_response)
    db.session.commit()

    return jsonify(responses)

async def generate_responses(prompt):
    tasks = []
    for model in config['models']:
        if model['provider'] == 'openai':
            tasks.append(generate_openai(prompt, model['api_model']))
        elif model['provider'] == 'anthropic':
            tasks.append(generate_anthropic(prompt, model['api_model']))
        elif model['provider'] == 'google':
            tasks.append(generate_google(prompt, model['api_model']))

    responses = await asyncio.gather(*tasks)
    return {model['name']: response for model, response in zip(config['models'], responses)}

@app.route('/vote', methods=['POST'])
def vote():
    model = request.json['model']
    vote = Votes.query.filter_by(model=model).first()
    
    if vote is None:
        vote = Votes(model=model, votes=1)
        db.session.add(vote)
    else:
        vote.votes += 1
    
    db.session.commit()

    # Update the winner in the most recent Response
    latest_response = Response.query.order_by(Response.id.desc()).first()
    if latest_response:
        latest_response.winner = model
        db.session.commit()
    
    # Fetch all votes and return as a dictionary
    all_votes = Votes.query.all()
    votes = {vote.model: vote.votes for vote in all_votes}
    return jsonify(votes)

@app.route('/reset-votes', methods=['POST'])
def reset_votes():
    try:
        Votes.query.update({Votes.votes: 0})
        Response.query.delete()
        db.session.commit()
        votes = {vote.model: vote.votes for vote in Votes.query.all()}
        return jsonify(votes)
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/download-results', methods=['GET'])
def download_results():
    si = StringIO()
    cw = csv.writer(si)
    
    header = ['Prompt', 'Winner', 'Timestamp']
    for model in config['models']:
        header.append(f"{model['display_name']} Response")
    cw.writerow(header)
    
    responses = Response.query.all()
    for response in responses:
        row = [response.prompt, response.winner, response.timestamp]
        for model in config['models']:
            row.append(response.responses.get(model['name'], ''))
        cw.writerow(row)
    
    output = si.getvalue().encode('utf-8')
    si.close()

    buffer = BytesIO()
    buffer.write(output)
    buffer.seek(0)

    return send_file(buffer,
                     mimetype='text/csv',
                     as_attachment=True,
                     download_name='ai_responses.csv')

async def generate_openai(prompt, model):
    try:
        response = await openai_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )

        html_content = f"<md-block>{response.choices[0].message.content}</md-block>"   
        return html_content
    except Exception as gpt_excp:
        print(gpt_excp)
        return "Failed to generate response."


async def generate_anthropic(prompt, model):
    try:
        message = await anthropic_client.messages.create(
            model=model,
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
        html_content = f"<md-block>{message.content[0].text}</md-block>"  
        
        return html_content
   
    except Exception as claude_excp:
        print(claude_excp)
        return "Failed to generate response"

async def generate_google(prompt, model):
    # Google's API doesn't support async calls directly, so we'll run it in a separate thread
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: generate_google_sync(prompt, model))
    
def generate_google_sync(prompt, model):    
    try:
        model = genai.GenerativeModel(model)
        response = model.generate_content(prompt)
        html_content =  f"<md-block>{response.text}</md-block>"  
        return html_content
    except Exception as gemini_excp:
        print(gemini_excp)
        return "Failed to generate response."


if __name__ == '__main__':
    app.run(debug=True)