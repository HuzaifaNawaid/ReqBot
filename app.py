import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
import time
from typing import List, Dict

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="Requirement Engineering Chatbot",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'requirements' not in st.session_state:
    st.session_state.requirements = {
        'functional': [],
        'non_functional': [],
        'domain': [],
        'inverse': []
    }

# Configure Gemini API
def configure_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("Gemini API key not found. Please check your .env file.")
        st.stop()
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.5-flash')

# Initialize Gemini model
try:
    model = configure_gemini()
except Exception as e:
    st.error(f"Error configuring Gemini: {str(e)}")
    st.stop()

# Function to classify requirement
def classify_requirement(requirement_text: str) -> Dict:
    """
    Classify the requirement using Gemini API
    """
    prompt = f"""
    Analyze the following requirement and classify it into one of these categories:
    1. Functional Requirement
    2. Non-Functional Requirement
    3. Domain Requirement
    4. Inverse Requirement (what the system should NOT do)

    Requirement: "{requirement_text}"

    Respond in JSON format only with this structure:
    {{
        "classification": "category_name",
        "explanation": "brief explanation",
        "suggested_rewrite": "suggested rewritten requirement if needed, otherwise keep original"
    }}

    Rules:
    - Functional: Describes what the system should do (features, behaviors)
    - Non-Functional: Describes how the system should behave (performance, security, usability)
    - Domain: Specific to the business/industry domain
    - Inverse: Describes what the system should NOT do or restrictions
    """
    
    try:
        response = model.generate_content(prompt)
        # Extract JSON from response
        response_text = response.text
        # Remove markdown code blocks if present
        response_text = response_text.replace('```json', '').replace('```', '').strip()
        
        import json
        result = json.loads(response_text)
        return result
    except Exception as e:
        st.error(f"Error classifying requirement: {str(e)}")
        return {
            "classification": "Unknown",
            "explanation": "Failed to classify",
            "suggested_rewrite": requirement_text
        }

# Function to add requirement to session state
def add_requirement(original_text: str, classification_result: Dict):
    category = classification_result['classification'].lower().replace(' ', '_')
    if 'functional' in category:
        category_key = 'functional'
    elif 'non_functional' in category or 'non-functional' in category:
        category_key = 'non_functional'
    elif 'domain' in category:
        category_key = 'domain'
    elif 'inverse' in category:
        category_key = 'inverse'
    else:
        category_key = 'functional'  # default
    
    requirement_entry = {
        'original': original_text,
        'rewritten': classification_result['suggested_rewrite'],
        'explanation': classification_result['explanation'],
        'timestamp': time.time()
    }
    
    st.session_state.requirements[category_key].append(requirement_entry)

# Sidebar for requirements overview
with st.sidebar:
    st.title("📋 Requirements Summary")
    
    # Show counts
    st.metric("Functional", len(st.session_state.requirements['functional']))
    st.metric("Non-Functional", len(st.session_state.requirements['non_functional']))
    st.metric("Domain", len(st.session_state.requirements['domain']))
    st.metric("Inverse", len(st.session_state.requirements['inverse']))
    
    # Clear button
    if st.button("Clear All Requirements", type="secondary"):
        st.session_state.requirements = {
            'functional': [],
            'non_functional': [],
            'domain': [],
            'inverse': []
        }
        st.session_state.messages = []
        st.rerun()

# Main content area
st.title("🤖 Requirement Engineering Assistant")
st.markdown("""
Describe your system requirements, and I'll classify them into:
- **Functional Requirements**: What the system should do
- **Non-Functional Requirements**: How the system should behave
- **Domain Requirements**: Business/industry specific
- **Inverse Requirements**: What the system should NOT do
""")

# Chat interface
user_input = st.chat_input("Enter your requirement here...")

if user_input:
    # Add user message to chat
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "timestamp": time.time()
    })
    
    # Show typing indicator
    with st.spinner("Analyzing requirement..."):
        # Classify the requirement
        classification_result = classify_requirement(user_input)
        
        # Add to requirements list
        add_requirement(user_input, classification_result)
        
        # Prepare bot response
        category = classification_result['classification']
        explanation = classification_result['explanation']
        
        bot_response = f"""
        **Classification:** {category}
        
        **Explanation:** {explanation}
        
        **Suggested Rewrite:** {classification_result['suggested_rewrite']}
        """
        
        # Add bot message to chat
        st.session_state.messages.append({
            "role": "assistant",
            "content": bot_response,
            "category": category,
            "timestamp": time.time()
        })
    
    st.rerun()

# Display chat messages
for message in st.session_state.messages[-10:]:  # Show last 10 messages
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Clear button at bottom
if st.session_state.messages:
    if st.button("Clear Chat", type="secondary"):
        st.session_state.messages = []
        st.session_state.requirements = {
            'functional': [],
            'non_functional': [],
            'domain': [],
            'inverse': []
        }
        st.rerun()

# Footer
st.markdown("---")
st.caption("Requirement Engineering Chatbot powered by Gemini 2.5 Flash | Classify and manage your system requirements efficiently")