# LLM Comparison Tool

This application allows users to compare responses from different AI models, vote on the best responses, and download the evaluation results. It currently only supports models from OpenAI, Anthropic, and Google.

![](./llm-comparison-tool.gif)

## Features

- Generate responses from multiple AI models simultaneously
- Vote on the best response
- Reset votes and clear stored results
- Download results as a CSV file
- Easily configurable to add or modify models

## Prerequisites

- Python 3.7+
- pip (Python package installer)

## Installation

1. Clone this repository:
```
git clone https://github.com/vmehmeri/llm-model-comparison-tool.git
cd llm-model-comparison-tool
```
2. Create a virtual environment:
```
python -m venv venv
source venv/bin/activate  
```
3. Install the required packages:
```
pip install -r requirements.txt
```
4. Set up your API keys in environment variables:
```
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
GOOGLE_API_KEY=your_google_api_key
```

## Configuration

The application uses a `config.yaml` file to define the models. To add or modify models, edit this file. Here's an example configuration:

```yaml
models:
  - name: GPT-4o
    provider: openai
    api_model: gpt-4o-2024-05-13
    display_name: GPT-4o

  - name: Claude
    provider: anthropic
    api_model: claude-3-5-sonnet-20240620
    display_name: Claude 3.5 Sonnet

  - name: Gemini Pro
    provider: google
    api_model: gemini-1.5-pro
    display_name: Gemini 1.5 Pro

  - name: Gemini Flash
    provider: google
    api_model: gemini-1.5-flash
    display_name: Gemini 1.5 Flash
```

Note: Only OpenAI, Anthropic, and Google models are currently supported.

## Running the Application
1. Ensure you're in the project directory and your virtual environment is activated.
2. Run the Flask application:
```
flask run 
```
3. Open a web browser and navigate to http://127.0.0.1:5000/

## Usage
1. Enter a prompt in the text area.
2. Click **Generate Responses** to get responses from all configured models.
3. Vote for the best response by clicking the **Vote** button next to it. You can vote more than once.
3. Use the **Reset Votes** button to clear all votes and stored responses.
4. Download the results as a CSV file using the **Download Results** button.

## Adding New Models
To add a new model:

1. Open config.yaml
2. Add a new entry under the models key, following the existing format
3. Ensure the provider is one of: openai, anthropic, or google
4. Save the file and restart the Flask application

## Troubleshooting
If you encounter any issues:

* Ensure all required packages are installed
* Check that your API keys are correctly set in the .env file
* Verify that the config.yaml file is correctly formatted
* Check the console output for any error messages

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the MIT License - see the LICENSE file for details.
