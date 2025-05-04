import streamlit as st
from openai import OpenAI
from datetime import datetime
import json

# Page configuration
st.set_page_config(
    page_title="Travel Itinerary Assistant",
    page_icon="✈️",
    layout="centered"
)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'conversation_state' not in st.session_state:
    st.session_state.conversation_state = "awaiting_api_key"
if 'travel_details' not in st.session_state:
    st.session_state.travel_details = {}
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0
if 'user_confirmed' not in st.session_state:
    st.session_state.user_confirmed = False
if 'client' not in st.session_state:
    st.session_state.client = None
if 'destination_suggestions' not in st.session_state:
    st.session_state.destination_suggestions = []
if 'selected_destination' not in st.session_state:
    st.session_state.selected_destination = ""

# Define the questions sequence
QUESTIONS = [
    "Where are you currently located? (This will help me plan your journey from home)",
    "What is your preferred mode of transport and how long are you willing to travel from your home to your first destination? (e.g., 'Flight, up to 8 hours' or 'Train, maximum 4 hours')",
    "Please give me five words that describe your ideal holiday and destination.",
    "What is your daily budget in USD?",
    "How many days would you like your holiday to be?"
]

# Main title
st.title("✈️ Travel Itinerary Assistant")

# Function to generate destination suggestions
def generate_destination_suggestions(travel_details):
    """Generate destination suggestions based on user preferences"""
    try:
        prompt = f"""
        Based on these travel preferences:
        - Starting Location: {travel_details.get('location', '')}
        - Preferred Transport and Travel Time Limit: {travel_details.get('transport_and_duration', '')}
        - Holiday Description (5 words): {travel_details.get('five_words', '')}
        - Daily Budget: ${travel_details.get('daily_budget', '')}
        - Duration: {travel_details.get('duration', '')} days
        
        Please suggest 3 different destinations that match these criteria. For each destination, provide:
        1. The destination name
        2. Why it matches the five descriptive words
        3. Travel time from the starting location
        4. Brief description (1-2 sentences)
        
        Format the response as a JSON array with 3 objects, each containing: name, reason, travel_time, description
        """
        
        response = st.session_state.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a travel planning expert. Provide destination suggestions in JSON format."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        # Parse the JSON response
        try:
            import json
            content = response.choices[0].message.content
            # Extract JSON from the response if it contains other text
            json_start = content.find('[')
            json_end = content.rfind(']') + 1
            if json_start != -1 and json_end != -1:
                json_str = content[json_start:json_end]
                suggestions = json.loads(json_str)
                return suggestions
            else:
                # Fallback to default suggestions
                return get_default_suggestions()
        except:
            return get_default_suggestions()
    except Exception as e:
        return get_default_suggestions()

def get_default_suggestions():
    """Return default suggestions if API fails"""
    return [
        {
            "name": "Bali, Indonesia",
            "reason": "Perfect mix of beach, culture, and relaxation",
            "travel_time": "Flight: 8-12 hours",
            "description": "Tropical paradise with stunning beaches, rich culture, and affordable luxury."
        },
        {
            "name": "Lisbon, Portugal",
            "reason": "Historic charm with coastal beauty",
            "travel_time": "Flight: 7-10 hours",
            "description": "Charming European city with beautiful architecture, great food, and nearby beaches."
        },
        {
            "name": "Costa Rica",
            "reason": "Nature, adventure, and eco-tourism",
            "travel_time": "Flight: 6-9 hours",
            "description": "Diverse landscapes offering rainforests, beaches, and abundant wildlife."
        }
    ]

# Function to generate travel plan using OpenAI
def generate_travel_plan(travel_details, selected_destination):
    """Generate travel plan using OpenAI API"""
    try:
        prompt = f"""
        Create a detailed travel itinerary for:
        - Destination: {selected_destination}
        - Starting Location: {travel_details.get('location', '')}
        - Preferred Transport: {travel_details.get('transport_and_duration', '')}
        - Holiday Description: {travel_details.get('five_words', '')}
        - Daily Budget: ${travel_details.get('daily_budget', '')}
        - Duration: {travel_details.get('duration', '')} days
        
        Please provide:
        1. Day-by-day itinerary with specific activities and attractions
        2. For each location/attraction within the destination:
           - Multiple transportation options (e.g., taxi, public transport, walking)
           - Estimated travel times for each option
           - Approximate costs for each transport option
        3. Detailed journey from starting location to destination with options
        4. Time estimates for each activity
        5. Local tips and cultural insights
        
        Format the transportation details clearly, for example:
        "From Hotel to Museum:
        - Taxi: 15 minutes, $10-15
        - Metro: 25 minutes, $2
        - Walking: 40 minutes, free"
        
        Do not include hotel recommendations or booking information.
        """
        
        response = st.session_state.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a travel planning expert. Provide detailed itineraries with multiple transportation options and travel times between each location."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating travel plan: {str(e)}"

# Step 1: API Key Input
if st.session_state.conversation_state == "awaiting_api_key":
    st.markdown("### Please enter your OpenAI API key to begin")
    api_key = st.text_input("OpenAI API Key", type="password", key="api_key_input")
    
    if st.button("Submit API Key"):
        if api_key:
            st.session_state.api_key = api_key
            st.session_state.client = OpenAI(api_key=api_key)
            st.session_state.conversation_state = "greeting"
            st.rerun()
        else:
            st.error("Please enter a valid API key")

# Step 2: Greeting and start conversation
elif st.session_state.conversation_state == "greeting":
    st.markdown("### Hi! I am keen to help you plan your travel.")
    st.markdown("### Where are you currently located? (This will help me plan your journey from home)")
    st.session_state.conversation_state = "collecting_info"
    st.session_state.current_question = 0
    st.rerun()

# Step 3-6: Collect information through questions
elif st.session_state.conversation_state == "collecting_info":
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Display current question if not all questions answered
    if st.session_state.current_question < len(QUESTIONS):
        with st.chat_message("assistant"):
            st.markdown(QUESTIONS[st.session_state.current_question])
        
        # User input
        user_input = st.chat_input("Your answer...")
        
        if user_input:
            # Store the answer
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Save the answer to travel details
            if st.session_state.current_question == 0:
                st.session_state.travel_details['location'] = user_input
            elif st.session_state.current_question == 1:
                st.session_state.travel_details['transport_and_duration'] = user_input
            elif st.session_state.current_question == 2:
                st.session_state.travel_details['five_words'] = user_input
            elif st.session_state.current_question == 3:
                st.session_state.travel_details['daily_budget'] = user_input
            elif st.session_state.current_question == 4:
                st.session_state.travel_details['duration'] = user_input
            
            # Move to next question or summary
            st.session_state.current_question += 1
            
            if st.session_state.current_question < len(QUESTIONS):
                st.session_state.messages.append({"role": "assistant", "content": QUESTIONS[st.session_state.current_question]})
            else:
                st.session_state.conversation_state = "summary"
            
            st.rerun()

# Step 7: Show summary and get confirmation
elif st.session_state.conversation_state == "summary":
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Create and display summary
    with st.chat_message("assistant"):
        st.markdown("### Here's a summary of your holiday planning requirements:")
        st.markdown(f"""
        - **Current Location**: {st.session_state.travel_details.get('location', '')}
        - **Transport & Travel Time**: {st.session_state.travel_details.get('transport_and_duration', '')}
        - **Holiday Description**: {st.session_state.travel_details.get('five_words', '')}
        - **Daily Budget**: ${st.session_state.travel_details.get('daily_budget', '')}
        - **Duration**: {st.session_state.travel_details.get('duration', '')} days
        
        Is this correct?
        """)
    
    # Confirmation button
    if st.button("YES - Find Destinations", key="confirm_button"):
        st.session_state.user_confirmed = True
        st.session_state.conversation_state = "destination_selection"
        st.rerun()

# Step 8: Show destination options
elif st.session_state.conversation_state == "destination_selection":
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Generate destination suggestions if not already done
    if not st.session_state.destination_suggestions:
        with st.chat_message("assistant"):
            with st.spinner("Finding perfect destinations for you..."):
                st.session_state.destination_suggestions = generate_destination_suggestions(st.session_state.travel_details)
    
    # Display destination options
    with st.chat_message("assistant"):
        st.markdown("### Based on your preferences, here are 3 destination suggestions:")
        
        for i, destination in enumerate(st.session_state.destination_suggestions, 1):
            st.markdown(f"""
            **{i}. {destination['name']}**
            - *Why it matches:* {destination['reason']}
            - *Travel time:* {destination['travel_time']}
            - *Description:* {destination['description']}
            """)
            st.markdown("---")
        
        st.markdown("Please select your preferred destination:")
    
    # Create destination selection buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button(f"1. {st.session_state.destination_suggestions[0]['name']}", key="dest_1"):
            st.session_state.selected_destination = st.session_state.destination_suggestions[0]['name']
            st.session_state.conversation_state = "generating_plan"
            st.rerun()
    
    with col2:
        if st.button(f"2. {st.session_state.destination_suggestions[1]['name']}", key="dest_2"):
            st.session_state.selected_destination = st.session_state.destination_suggestions[1]['name']
            st.session_state.conversation_state = "generating_plan"
            st.rerun()
    
    with col3:
        if st.button(f"3. {st.session_state.destination_suggestions[2]['name']}", key="dest_3"):
            st.session_state.selected_destination = st.session_state.destination_suggestions[2]['name']
            st.session_state.conversation_state = "generating_plan"
            st.rerun()

# Step 9: Generate and display travel plan
elif st.session_state.conversation_state == "generating_plan":
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Generate travel plan
    with st.chat_message("assistant"):
        with st.spinner(f"Creating your personalized itinerary for {st.session_state.selected_destination}..."):
            travel_plan = generate_travel_plan(st.session_state.travel_details, st.session_state.selected_destination)
            st.markdown(f"### Your Travel Itinerary for {st.session_state.selected_destination}")
            st.markdown(travel_plan)
            
            # Save the plan to messages
            st.session_state.messages.append({"role": "assistant", "content": travel_plan})
    
    # Option to restart
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Plan Another Trip"):
            # Reset state
            st.session_state.messages = []
            st.session_state.conversation_state = "greeting"
            st.session_state.travel_details = {}
            st.session_state.current_question = 0
            st.session_state.user_confirmed = False
            st.session_state.destination_suggestions = []
            st.session_state.selected_destination = ""
            st.rerun()
    
    with col2:
        if st.button("Choose Different Destination"):
            st.session_state.conversation_state = "destination_selection"
            st.rerun()

# Export functionality (always available if there are messages)
if st.session_state.messages:
    st.markdown("---")
    if st.button("📥 Export Travel Plan"):
        chat_text = "Travel Itinerary Plan\n\n"
        chat_text += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        
        # Add travel details
        chat_text += "Travel Details:\n"
        for key, value in st.session_state.travel_details.items():
            chat_text += f"- {key.replace('_', ' ').title()}: {value}\n"
        chat_text += "\n---\n\n"
        
        # Add conversation
        for message in st.session_state.messages:
            if message['role'] == 'assistant' and len(message['content']) > 100:  # Likely the travel plan
                chat_text += "Travel Itinerary:\n\n"
                chat_text += message['content']
        
        st.download_button(
            label="Download Travel Plan",
            data=chat_text,
            file_name=f"travel_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )

# Footer
st.markdown("---")
st.markdown("Travel Itinerary Assistant | Powered by OpenAI")