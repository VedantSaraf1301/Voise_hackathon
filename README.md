# Voise_hackathon

#Smart Diet Analyzer
Smart Diet Analyzer is an AI-powered application that analyzes food images to provide nutritional information and calorie estimates. The application uses advanced image analysis capabilities to identify food items and estimate their calorie content.

Features
Upload food images for analysis
AI-powered food identification and calorie estimation
Generate and download a PDF report of the nutritional analysis
User-friendly interface with Streamlit
Installation
Clone the repository:

git clone https://github.com/VedantSaraf1301/Voise_hackathon
cd Smart-Diet-Analyzer
Create and activate a virtual environment:

python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
Install the required dependencies:

pip install -r requirements.txt
Create a .env file in the project root directory and add your Groq API key:

GROQ_API_KEY=your_api_key_here
Usage
Run the Streamlit application:

streamlit run app.py
Open your web browser and navigate to http://localhost:8501.

Upload a food image using the sidebar and click "Analyze Meal 🍽️" to get the nutritional analysis.

Download the generated PDF report or clear the analysis to start over.

Project Structure
app.py: Main application file containing the Streamlit interface and utility functions.
requirements.txt: List of dependencies required for the project.
.env: Environment file to store sensitive information like API keys.

