import streamlit as st
import anthropic
import time
import pandas as pd
import json
import re
from textblob import TextBlob
import plotly.express as px

# -------------------------------------------------------------------
# 1) ANTHROPIC CONFIGURATION
# -------------------------------------------------------------------
client = anthropic.Anthropic(
    api_key="API_KEY"  # Replace with your secure API key management approach
)

# -------------------------------------------------------------------
# 2) SUPPLEMENTAL DATA & URLS
# -------------------------------------------------------------------
APPLE_WATCH_SUPPORT_URL = "https://www.uscellular.com/support/apple-watch-connectivity"
PLAN_CHANGE_URL = "https://www.uscellular.com/plans/change"
RETENTION_URL = "https://www.uscellular.com/retention"
DEVICE_UPGRADE_URL = "https://www.uscellular.com/upgrade-policy"
LOYALTY_URL = "https://www.uscellular.com/loyalty"

# -------------------------------------------------------------------
# 3) TRANSCRIPTS FOR THE 3 CALL SCENARIOS
# -------------------------------------------------------------------

# --- Apple Watch Connectivity Transcript ---
transcript_apple_watch = [
    ("Customer", "I'm calling because my Apple Watch isn't connecting properly."),
    ("Customer", "I use my watch when I run and it should work without my phone."),  # New utterance
    ("Agent", "Hello! I've reviewed your account details regarding your Apple Watch connectivity issue. I've checked the eSIM status and network provisioning for your device. Let me help you verify if everything is properly set up on our end."),
    ("Customer", "I tried toggling the airplane mode as you suggested, but it's still not working."),
    ("Agent", "I understand you're still experiencing issues. I've specifically checked your eSIM status and network provisioning details. Please hold on while I run a quick diagnostic."),
    ("Customer", "Alright, let me try updating my watch's settings now."),
    ("Agent", "I've verified that your eSIM is active and network provisioning is complete. You can safely proceed with updating your settings. If you need further help, please let me know."),
    ("Customer", "It looks like that did the trick; my watch is now connecting on its own!"),
    ("Agent", "Great! Your watch is now properly connected. Is there anything else I can help you with regarding your Apple Watch service?"),
    ("Customer", "Great, thanks for your help."),
    ("Agent", "Thank you for reaching out. I'm here to help if you need anything else.")
]

context_apple_watch = (
    "Supplemental Data: For Apple Watch connectivity issues, refer to our troubleshooting documents. "
    "Use the following format:\n"
    "From CellSite\n"
    "[Document Name: Apple Watch Troubleshooting Guide]\n"
    "[Section: eSIM Activation Status]\n"
    "- Check active eSIM status\n"
    "- Verify network provisioning\n"
    "Skip basic troubleshooting and focus on account review."
)

# --- Plan Upgrade (Plan Change) Transcript ---
transcript_plan_change = [
    ("Customer", "I want to change my plan. It’s getting too expensive, and I need something cheaper."),
    ("Agent", "Thank you for sharing that. Based on our Product Catalogue, I recommend switching you to our Ultimate Plus plan, which offers premium benefits such as enhanced data speeds, HD streaming, and extra perks."),
    ("Customer", "But I really want more savings than that."),
    ("Agent", "I understand your concern about cost. In that case, please allow me to connect you with our retention specialist who can provide you with more options and additional discounts."),
    ("Customer", "That sounds good. Thank you."),
    ("Agent", "I am transferring you to our retention specialist now. Thank you for your patience.")
]

context_plan_change = (
    "Supplemental Data: For plan changes, refer to our plan change options at "
    f"{PLAN_CHANGE_URL} and retention strategies at {RETENTION_URL}. "
    "Customer's current plan: UNLIMITED+ WITH MULTILINE DISCOUNTS at $55/mo. "
    "Recommended plan: Ultimate Plus plan (premium benefits) but if savings are required, connect to a retention specialist."
    " Note: If the customer expresses strong dissatisfaction (e.g. mentioning 'more savings'), flag 'Attention: Churn Risk'."
)

# --- Device Upgrade Transcript (Final Updated in Sales Mode) ---
transcript_device_upgrade = [
    ("Customer", "I've been with you for 10 years, and I'm using an older model smartphone."), 
    ("Agent", "I appreciate your loyalty. As a valued customer with a 10-year tenure, you're eligible for exclusive loyalty benefits. Our new flagship smartphone features enhanced performance, a state-of-the-art camera, a vibrant high-resolution display, and all-day battery life. I've already applied your loyalty discount so you can enjoy these premium features at a reduced cost."),
    ("Customer", "Yes, I'd love to know more."),
    ("Agent", "This device offers a superior experience with a cutting-edge camera, fast performance, and extended battery life. With your exclusive discount, you're getting these advanced features at exceptional value."),
    ("Customer", "But I hear that new customers get even better upgrade options than loyal customers like me who have been with USCC for 10 years, and I'm really concerned about the cost."),
    ("Agent", "I understand your concern about cost. Your loyalty discount has been applied to ensure you receive the best possible value for your long-standing commitment."),
    ("Customer", "That sounds excellent."),
    ("Agent", "Thank you for confirming. I'm pleased to inform you that your upgrade has been finalized. Your new device—with enhanced performance, an exceptional camera, longer battery life, and a brilliant display—will be delivered to you shortly. The updated pricing will reflect on your account within a few days, ensuring a smooth transition without bill shock. I am now transferring you to our retention specialist to address any further questions regarding your upgrade options."),
    ("Customer", "No, that's all. I'm very satisfied with this upgrade. Thank you for your help!")
]

context_device_upgrade = (
    "Supplemental Data: For device upgrade issues, refer to guidelines at "
    f"{DEVICE_UPGRADE_URL} and loyalty benefits at {LOYALTY_URL}. "
    "Note: If the customer expresses strong dissatisfaction, flag 'Attention: Churn Risk'."
)

# -------------------------------------------------------------------
# 4) STREAMLIT UI & CUSTOM CSS
# -------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Custom styling for all buttons to be equal in size and aligned */
    .stButton > button {
        background-color: #4CAF50;
        border: none;
        color: white;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 8px;
        box-shadow: 3px 3px 6px rgba(0,0,0,0.2);
        height: 60px;
        width: 100%;
    }
    .analyze-btn > button {
        background-color: #FF5722;
        height: 60px;
        width: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("US Cellular – Agent Assist")

# Initialize/reset session state variables
if "call_finished" not in st.session_state:
    st.session_state["call_finished"] = False
if "final_transcript" not in st.session_state:
    st.session_state["final_transcript"] = ""
if "current_transcript" not in st.session_state:
    st.session_state["current_transcript"] = []

# -------------------------------------------------------------------
# 5) TOP-OF-PAGE CALL SIMULATION BUTTONS (3 SCENARIOS)
# -------------------------------------------------------------------
cols = st.columns(3)
with cols[0]:
    apple_watch_button = st.button("Apple Watch Connectivity", key="apple_watch")
with cols[1]:
    plan_change_button = st.button("Plan Change", key="plan_change")
with cols[2]:
    device_upgrade_button = st.button("Device Upgrade Issue", key="device_upgrade")

# -------------------------------------------------------------------
# 6) SUMMARIZE CALL BUTTON IN SIDEBAR (Always Active)
# -------------------------------------------------------------------
with st.sidebar:
    st.markdown("<div class='analyze-btn'>", unsafe_allow_html=True)
    analyze_call_button = st.button("Summarize Call", key="analyze_call")
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------------------------
# 7) HELPER FUNCTIONS
# -------------------------------------------------------------------

# Define get_intent (must be defined before use)
def get_intent(customer_text: str, context: str = "") -> str:
    intent_prompt = (
        "Identify the core intent of the following customer query in one or two words. "
        "Only output the intent in one or two words.\n\n"
        f"Customer query: {customer_text}"
    )
    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=20,
            temperature=0.0,
            messages=[{"role": "user", "content": intent_prompt}]
        )
        return message.content[0].text.strip()
    except Exception as e:
        return "Unknown"

def analyze_sentiment(text: str) -> float:
    return TextBlob(text).sentiment.polarity

def sentiment_label(polarity: float) -> str:
    if polarity > 0.1:
        return "Positive"
    elif polarity < -0.1:
        return "Negative"
    else:
        return "Neutral"

# Modified run_conversation to display core intent (stable) above intent shifts.
def run_conversation(transcript, context, conversation_speed=0.05):
    st.session_state["final_transcript"] = ""
    st.session_state["current_transcript"] = []
    
    final_transcript_lines = []
    core_intent = None  # Core intent remains stable.
    for speaker, text in transcript:
        placeholder = st.empty()
        if speaker.lower() == "customer":
            displayed_text = ""
            for word in text.split():
                displayed_text += word + " "
                placeholder.markdown(f"**Customer:** {displayed_text}")
                time.sleep(conversation_speed)
            final_transcript_lines.append(f"Customer: {text}")
            
            # Show sentiment.
            pol = analyze_sentiment(text)
            s_label = sentiment_label(pol)
            face_emoji = "😊" if s_label == "Positive" else "😞" if s_label == "Negative" else "😐"
            st.write(f"Sentiment: {s_label} {face_emoji} ({pol:.2f})")
            
            # Get current intent.
            current_intent = get_intent(text, context)
            
            # Display churn risk flag if applicable for plan change or device upgrade.
            if ("plan" in context.lower() or "device upgrade" in context.lower()) and (
                pol < -0.5 or ("cost" in text.lower() and "new customer" in text.lower()) or ("more savings" in text.lower())
            ):
                st.markdown("<div style='color:orange'><strong>Attention: Churn Risk</strong></div>", unsafe_allow_html=True)
            
            if core_intent is None:
                core_intent = current_intent
            st.markdown(f"<div style='color:red'><strong>Core Intent: {core_intent}</strong></div>", unsafe_allow_html=True)
            if current_intent != core_intent:
                st.markdown(f"<div style='color:red'><strong>Sub Intent: {core_intent} --> {current_intent}</strong></div>", unsafe_allow_html=True)
            
            # Generate and display agent-assist suggestion.
            suggestion = get_assisting_suggestion(text, context=context)
            st.markdown(f"<div style='color:blue'><i>💡 {suggestion}</i></div>", unsafe_allow_html=True)
            final_transcript_lines.append(f"Agent Assist: {suggestion}")
            st.markdown("---")
        elif speaker.lower() == "agent":
            displayed_text = ""
            for word in text.split():
                displayed_text += word + " "
                placeholder.markdown(f"**Agent:** {displayed_text}")
                time.sleep(conversation_speed)
            final_transcript_lines.append(f"Agent: {text}")
            st.markdown("---")
        else:
            st.markdown(f"**{speaker}:** {text}")
            final_transcript_lines.append(f"{speaker}: {text}")
        time.sleep(conversation_speed * 10)
    
    st.session_state["current_transcript"] = transcript
    st.session_state["final_transcript"] = "\n".join(final_transcript_lines)
    st.session_state["call_finished"] = True
    if hasattr(st, "experimental_rerun"):
        st.experimental_rerun()

# Modified get_assisting_suggestion to include churn risk flag for plan change and device upgrade scenarios.
def get_assisting_suggestion(customer_text: str, context: str = "") -> str:
    sentiment_score = analyze_sentiment(customer_text)
    flag_text = ""
    if ("plan" in context.lower() or "device upgrade" in context.lower()) and (
        sentiment_score < -0.5 or ("cost" in customer_text.lower() and "new customer" in customer_text.lower()) or ("more savings" in customer_text.lower())
    ):
        flag_text = "Attention: Churn Risk. "
    
    if "plan" in context.lower() or "unlimited+" in context.lower():
        retention_text = "After evaluating the customer's concerns, please connect them with a retention specialist for plan upgrade options."
        system_prompt = (
            "You are an AI assistant providing internal suggestions to a US Cellular agent. "
            "When recommending a plan change, refer to the Product Catalogue for accurate plan details. "
            "Format your suggestion as follows (each on a new line):\n"
            "From Product Catalogue\n"
            "[Plan Details: Current vs. Recommended]\n"
            "- Compare the customer's current plan with the recommended Ultimate Plus plan\n"
            "- Emphasize premium benefits; if further savings are needed, connect to a retention specialist\n\n"
            f"{flag_text}{retention_text}\n\n"
            "Do not include any reference to CellSite. Keep the suggestion concise (one or two sentences).\n\n"
            f"Supplemental Context: {context}\n\n"
            "The user says:\n"
        )
    elif "device upgrade" in context.lower():
        system_prompt = (
            "You are an AI assistant providing internal suggestions to a US Cellular agent. "
            "Assume the customer's account has been verified and they are a loyal customer with a 10-year tenure. "
            "Format your suggestion as follows (each on a new line):\n"
            "From CellSite\n"
            "[Document Name: Device Upgrade Eligibility Guide]\n"
            "[Section: Loyalty Benefits]\n"
            "- Confirm that the customer is eligible for exclusive upgrade offers due to their 10-year loyalty\n\n"
            f"{flag_text}"
            "Keep the suggestion concise (one or two sentences).\n\n"
            f"Supplemental Context: {context}\n\n"
            "The user says:\n"
        )
    else:
        system_prompt = (
            "You are an AI assistant providing internal suggestions to a US Cellular agent. "
            "When providing troubleshooting advice, refer to the CellSite FAQs and troubleshooting documents. "
            "Format your suggestion as follows (each on a new line):\n"
            "From CellSite\n"
            "[Document Name: Apple Watch Troubleshooting Guide]\n"
            "[Section: eSIM Activation Status]\n"
            "- Check active eSIM status\n"
            "- Verify network provisioning\n\n"
            "Keep the suggestion concise (one or two sentences).\n\n"
            f"Supplemental Context: {context}\n\n"
            "The user says:\n"
        )
    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=120,
            temperature=0.7,
            messages=[{"role": "user", "content": f"{system_prompt}{customer_text}"}]
        )
        return message.content[0].text.strip()
    except Exception as e:
        return f"Error generating suggestion: {e}"

def get_agent_response(suggestion: str, customer_query: str) -> str:
    agent_prompt = (
        "You are a US Cellular support agent with access to the customer's account information. "
        "Based on the internal AI suggestion provided below and the customer's query, craft your response by explicitly stating that you have reviewed the account. "
        "Your answer should confirm the necessary actions without revealing internal risk assessments. "
        "Do not mention churn risk or any internal flags.\n\n"
        "Internal Suggestion: " + suggestion + "\n"
        "Customer Query: " + customer_query + "\n\n"
        "Your Response:"
    )
    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=350,
            temperature=0.7,
            messages=[{"role": "user", "content": agent_prompt}]
        )
        return message.content[0].text.strip()
    except Exception as e:
        return f"Error generating agent response: {e}"

# -------------------------------------------------------------------
# Updated analyze_call_overview with a fixed JSON structure for Adherence to Suggestion
# -------------------------------------------------------------------
def analyze_call_overview(transcript_text: str) -> dict:
    prompt = (
        "Given the following transcript of a call between a customer and a support agent, provide a detailed analysis in JSON format with the following keys:\n"
        "\"Summary of Discussion\": A brief summary of the discussion.\n"
        "\"Topics Discussed\": List the main topics covered in the call.\n"
        "\"Required Actions\": List any actions that need to be taken or were taken as a result of the call.\n"
        "\"Adherence to Suggestion\": Evaluate if the agent's response adhered to the internal suggestion. "
        "Return this value as a JSON object with exactly two keys: \"Rating\" and \"Commentary\". The Rating should be a number from 1 to 10, and the Commentary should briefly explain your evaluation.\n"
        "\"Overall Output/Result\": What was the overall result of the call?\n\n"
        "Transcript:\n" + transcript_text + "\n\n"
        "Return a valid JSON object."
    )
    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=400,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )
        analysis_text = message.content[0].text
        cleaned_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', analysis_text)
        return json.loads(cleaned_text)
    except Exception as e:
        return {"error": f"Error generating call analysis: {e}"}

def perform_analysis():
    if not st.session_state.get("final_transcript"):
        st.error("No call data available for analysis. Please simulate a call first.")
        return

    customer_factor = 0.2  # seconds per word for customer
    agent_factor = 0.2      # seconds per word for agent
    customer_time_sec = sum(len(text.split()) * customer_factor 
                            for (speaker, text) in st.session_state["current_transcript"] if speaker.lower() == "customer")
    agent_time_sec = sum(len(text.split()) * agent_factor 
                         for (speaker, text) in st.session_state["current_transcript"] if speaker.lower() == "agent")
    silence_time_sec = (len(st.session_state["current_transcript"]) - 1) * 0.5
    total_time_sec = customer_time_sec + agent_time_sec + silence_time_sec

    customer_time_min = customer_time_sec / 30
    agent_time_min = agent_time_sec / 30
    silence_time_min = silence_time_sec / 30
    total_time_min = total_time_sec / 30

    with st.sidebar:
        st.subheader("Summarize Call")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Call Duration (AHT)", f"{total_time_min:.2f} min")
        col2.metric("Customer Talk Time", f"{customer_time_min:.2f} min")
        col3.metric("Agent Talk Time", f"{agent_time_min:.2f} min")
        st.markdown("---")
        
        sentiments = []
        x_axis = []
        for i, (speaker, text) in enumerate(st.session_state["current_transcript"]):
            if speaker.lower() == "customer":
                sentiments.append(analyze_sentiment(text))
                x_axis.append(i)
        if sentiments:
            sentiment_df = pd.DataFrame({"Turn": x_axis, "Sentiment": sentiments})
            fig_sentiment = px.line(sentiment_df, x="Turn", y="Sentiment", 
                                     title="Customer Sentiment Trend", line_shape="spline")
            st.plotly_chart(fig_sentiment)
        else:
            st.write("No customer sentiment data available.")
        st.markdown("---")
        
        time_distribution = pd.DataFrame({
            "Segment": ["Customer", "Agent", "Silence"],
            "Time (min)": [customer_time_min, agent_time_min, silence_time_min]
        })
        fig_doughnut = px.pie(time_distribution, names="Segment", values="Time (min)", hole=0.4,
                              title="Talk Time Distribution")
        st.plotly_chart(fig_doughnut)
        st.markdown("---")
        
        st.markdown("#### Summary of Discussion")
        analysis_json = analyze_call_overview(st.session_state["final_transcript"])
        if "error" in analysis_json:
            st.error(analysis_json["error"])
        else:
            st.markdown(analysis_json.get("Summary of Discussion", "N/A"))
            st.markdown("---")
            
            st.markdown("#### Topics Discussed")
            topics = analysis_json.get("Topics Discussed", "N/A")
            if isinstance(topics, list):
                st.markdown("\n".join([f"- {topic}" for topic in topics]))
            else:
                st.markdown(topics)
            st.markdown("---")
            
            st.markdown("#### Required Actions")
            required_actions = analysis_json.get("Required Actions", "N/A")
            if isinstance(required_actions, list):
                st.markdown("\n".join([f"- {action}" for action in required_actions]))
            else:
                st.markdown(required_actions)
            st.markdown("---")
            
            st.markdown("#### Adherence to Suggestion")
            adherence = analysis_json.get("Adherence to Suggestion", "N/A")
            # Attempt to parse adherence if it's a string that might be JSON.
            try:
                if isinstance(adherence, str):
                    parsed = json.loads(adherence)
                else:
                    parsed = adherence
                if isinstance(parsed, dict):
                    rating = parsed.get("Rating", "N/A")
                    commentary = parsed.get("Commentary", "N/A")
                    st.markdown(f"**Rating:** {rating}\n\n**Commentary:** {commentary}")
                else:
                    st.markdown(adherence)
            except Exception:
                st.markdown(adherence)
            st.markdown("---")
            
            st.markdown("#### Overall Output/Result")
            overall_output = analysis_json.get("Overall Output/Result", "N/A")
            if isinstance(overall_output, dict):
                formatted_output = ""
                for key, value in overall_output.items():
                    formatted_output += f"**{key}:** {value}\n\n"
                st.markdown(formatted_output)
            else:
                st.markdown(overall_output)
            st.markdown("---")

with st.sidebar:
    st.subheader("Call Analysis")

# -------------------------------------------------------------------
# 8) RUN LOGIC BASED ON BUTTON CLICKS
# -------------------------------------------------------------------
if apple_watch_button:
    st.session_state["call_finished"] = False
    st.session_state["final_transcript"] = ""
    st.session_state["current_transcript"] = []
    st.empty()  # Clear previous conversation
    st.subheader("Live Call Assist – Apple Watch Connectivity Issue")
    run_conversation(transcript_apple_watch, context=context_apple_watch, conversation_speed=0.05)

if plan_change_button:
    st.session_state["call_finished"] = False
    st.session_state["final_transcript"] = ""
    st.session_state["current_transcript"] = []
    st.empty()
    st.subheader("Live Call Assist – Plan Change")
    run_conversation(transcript_plan_change, context=context_plan_change, conversation_speed=0.05)

if device_upgrade_button:
    st.session_state["call_finished"] = False
    st.session_state["final_transcript"] = ""
    st.session_state["current_transcript"] = []
    st.empty()
    st.subheader("Live Call Assist – Device Upgrade Issue")
    run_conversation(transcript_device_upgrade, context=context_device_upgrade, conversation_speed=0.05)

if analyze_call_button:
    st.subheader("Summarize Call (Results are shown in the sidebar)")
    perform_analysis()
