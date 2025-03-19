# AI Knowledge Manager

AI Knowledge Manager is an intelligent system for extracting, organizing, and retrieving insights from your ChatGPT conversations and other knowledge sources.

## Features

- **Automatic Organization**: AI-powered categorization and tagging of conversations
- **Semantic Search**: Find related content based on meaning, not just keywords
- **Topic Visualization**: See how different topics and ideas are connected
- **Conversation Analysis**: Extract key topics, entities, and insights
- **Writing Assistant**: Get suggestions from past conversations when writing

## Requirements

- Python 3.8+ 
- MongoDB (local or cloud instance)
- OpenAI API key

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/chatgpt-knowledge-manager.git
   cd chatgpt-knowledge-manager
   ```

2. Create and activate a virtual environment:
   ```
   # For Windows
   python -m venv venv
   venv\Scripts\activate
   
   # For macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Download NLTK data:
   ```
   python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
   ```

5. Create a `.env` file in the root directory:
   ```
   cp .env.template .env
   ```

6. Edit the `.env` file with your configuration:
   ```
   # API Keys
   OPENAI_API_KEY=your-openai-api-key-here
   
   # Database
   MONGODB_URI=+srv://tfoster:JywSUqQG826_3@knowledgemanagerdb.gho68.mongodb.net/?retryWrites=true&w=majority&appName=KnowledgeManagerDB
   MONGODB_DB_NAME=knowledge_manager
   
   # Application
   DEBUG=False
   SECRET_KEY=replace-with-a-strong-secret-key
   ```

7. Set up the application directory structure:
   ```
   python -m app.utils.dir_setup
   ```

## Running the Application

1. Start the Streamlit app:
   ```
   streamlit run app.py
   ```

2. Open your browser and navigate to the URL shown in the terminal (typically http://localhost:8501)

3. Register a new account and log in to start using the application

## Usage

### Importing ChatGPT Conversations

1. Export your ChatGPT data from https://chat.openai.com/ (Account Settings > Data Controls > Export Data)
2. Wait for the export email from OpenAI and download the ZIP file
3. Extract the conversations.json file
4. In the AI Knowledge Manager, go to Settings > Import/Export
5. Upload the conversations.json file
6. Follow the instructions to import your conversations

### Searching and Exploring

- Use the Search page to find conversations using AI-powered semantic search
- Explore the Topic Map to see how different topics are related
- Browse all conversations with filtering options

### Writing with AI Assistance

- Open the Writing Projects section to create content with AI assistance
- The system will suggest relevant past conversations and insights as you write

## Development

### Project Structure

- `app.py`: Main application entry point
- `app/backend/`: Business logic and AI services
- `app/database/`: Data access layer
- `app/frontend/`: Streamlit UI components
- `app/models/`: Data models and schemas
- `app/utils/`: Utility functions and helpers
- `app/config/`: Configuration settings

### Testing

Run tests with pytest:

```
pytest
```

## Deployment

For deployment to a production environment, consider:

1. Setting up a proper MongoDB instance with authentication
2. Using a reverse proxy like Nginx
3. Running Streamlit with an authentication proxy or behind SSO

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- This project uses OpenAI's GPT and embedding models
- Built with Streamlit, MongoDB, and various Python libraries
# chatgpt-knowledge-manager