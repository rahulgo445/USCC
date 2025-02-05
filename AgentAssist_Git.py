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
    api_key="<ANTHROPIC API KEY"  # Replace with your secure API key management approach
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
    ("Agent", "Hello! I've reviewed your account details in our system regarding your Apple Watch connectivity issue. Based on the internal suggestion, I've checked the eSIM status and network provisioning for your device. Let me help you verify if everything is properly set up on our end. After checking your account, I can see your eSIM status and will confirm whether it's properly activated and if the network provisioning is complete. This will help us determine if there's any issue with the cellular connection for your Apple Watch. Would you mind giving me just a moment while I verify these specific details in our system?"),
    ("Customer", "I tried toggling the airplane mode as you suggested, but it's still not working."),
    ("Agent", "I understand you're still experiencing connectivity issues after toggling airplane mode. I've reviewed your account in our system, and based on the internal suggestion, I've specifically checked your Apple Watch's eSIM status and network provisioning details. Let me help verify if everything is properly activated on our end. After checking your account, I need to confirm if your eSIM is showing as fully activated and if the network provisioning has been completed. This will help us determine if there's a backend issue we need to address. Would you mind waiting a moment while I run a quick diagnostic on the network provisioning status? In the meantime, could you let me know if you're seeing any specific error messages on your Apple Watch?"),
    ("Customer", "Alright, let me try updating my watch's settings now."),
    ("Agent", "I've just reviewed your account in our system and checked your Apple Watch's eSIM status. Based on the internal suggestion, I need to confirm that your eSIM activation is fully complete before you proceed with any settings updates. Let me verify this for you... I see that your eSIM is active and the network provisioning has been completed. You can safely proceed with updating your watch's settings now. If you experience any issues during the process, please don't hesitate to reach back out for additional support."),
    ("Customer", "It looks like that did the trick; my watch is now connecting on its own!"),
    ("Agent", "I have reviewed your account in our system and can confirm that your Apple Watch's eSIM is now properly activated and provisioned on our network. Based on the internal verification I performed, I can see that your watch is successfully connected and receiving signal. I'm glad to hear it's now connecting independently as it should. Is there anything else you need assistance with regarding your Apple Watch service?"),
    ("Customer", "Great, thanks for your help."),
    ("Agent", "Thank you for reaching out to US Cellular support. Based on the internal suggestion, I have reviewed your account in our system, but I notice we haven't yet discussed a specific concern or issue you'd like me to address. I'm here to help—whether you're experiencing connectivity issues with a device, have questions about your service, or need assistance with any other account matters. Please let me know what specific help you need, and I'll be happy to assist you further.")
]

context_apple_watch = (
    "Supplemental Data: For Apple Watch connectivity issues, refer to our troubleshooting documents. "
    "When providing advice, use the following format:\n"
    "From CellSite\n"
    "[Document Name: Apple Watch Troubleshooting Guide]\n"
    "[Section: eSIM Activation Status]\n"
    "- Check account for active eSIM status under Watch device details\n"
    "- Verify network provisioning is complete in the billing system if eSIM is active\n\n"
    "Skip basic troubleshooting (e.g. restarting devices) and focus on reviewing the account information."
)

# --- Plan Change Transcript (Final Updated) ---
transcript_plan_change = [
    ("Customer", "I want to change my plan. It’s getting too expensive, and I need something cheaper."),
    ("Agent", "Thank you for sharing that. I've reviewed your account details and usage history. Based on our Product Catalogue, I recommend switching you to our UNLIMITED plan at $40/mo. This plan offers unlimited talk, text, and data with HD Video (720p), 15GB Hotspot, and 15GB Priority Data—saving you $15 per month while still meeting your needs."),
    ("Customer", "Honestly, I just need to bring my bill down. I don’t use a lot of data, and I feel like I’m paying for services I don't really use."),
    ("Agent", "I understand your concern. Considering your usage, I recommend switching to our UNLIMITED plan at $40/mo. It aligns more closely with your data needs and will help lower your monthly bill."),
    ("Customer", "I’ve been with you for years, but I feel like I’m paying way more than new customers."),
    ("Agent", "I truly appreciate your loyalty over the years. I can switch you to our UNLIMITED plan at $40/mo, which offers similar unlimited features at a lower cost—saving you $15 per month."),
    ("Customer", "That sounds great! I’m happy to switch to the UNLIMITED plan. Please go ahead and change my plan."),
    ("Agent", "Excellent! I've now updated your account to reflect the UNLIMITED plan at $40 per month. You can start enjoying your new plan right away, and the new rate will be reflected on your next billing cycle. This ensures you won’t see any unexpected changes on your current bill.")
]

context_plan_change = (
    "Supplemental Data: For plan changes, refer to the plan change options at "
    f"{PLAN_CHANGE_URL} and retention strategies at {RETENTION_URL}. "
    "Customer's current plan: UNLIMITED+ WITH MULTILINE DISCOUNTS at $55/mo. (Unlimited Talk, Text and Data, HD Video (1080p), 35GB Hotspot, 35GB Priority Data). "
    "Recommended plan: UNLIMITED WITH MULTILINE DISCOUNTS at $40/mo. (Unlimited Talk, Text and Data, HD Video (720p), 15GB Hotspot, 15GB Priority Data). "
    "Note: For agent assist recommendations, identify intent and detect churn risk. For early signs of churn, recommend proactive retention strategies; for escalated churn risk, suggest transferring the call to the retention team."
)

# --- Device Upgrade Transcript (Final Updated in Sales Mode) ---
transcript_device_upgrade = [
    ("Customer", "I've been with you for 10 years, and I'm using an older model smartphone."),
    ("Agent", "I appreciate your loyalty. As a valued long-term customer, you're eligible for an exclusive upgrade offer. I'm excited to share that we've secured a special offer just for you. Our new flagship smartphone features enhanced performance, a state-of-the-art camera, a vibrant high-resolution display, and a battery that lasts all day. Plus, I've already applied your loyalty discount so you can enjoy these premium features at a greatly reduced cost."),
    ("Customer", "Yes, I'd love to know more."),
    ("Agent", "This new device offers a truly superior experience. It boasts a cutting-edge camera system for stunning photos, a powerful processor for fast performance, and extended battery life to keep you connected longer. With your exclusive discount, you're getting all these advanced features at an exceptional value."),
    ("Customer", "Cost is definitely my main concern, though enhanced features would be a bonus."),
    ("Agent", "I completely understand. That’s why I’ve structured this offer to deliver significant savings while upgrading you to a superior device. Your loyalty discount has already been applied, reducing the overall cost considerably. You’re getting top-tier features and performance without compromising on value."),
    ("Customer", "That sounds excellent."),
    ("Agent", "Thank you for confirming. I'm pleased to inform you that your upgrade has been finalized. Your new device—featuring enhanced performance, an exceptional camera, longer battery life, and a brilliant display—will be delivered to you shortly. The updated pricing will reflect on your account within a few days, ensuring a smooth transition without any bill shock. Is there anything else I can help you with today?"),
    ("Customer", "No, that's all. I'm very satisfied with this upgrade. Thank you for your help!")
]

context_device_upgrade = (
    "Supplemental Data: For device upgrade issues, check eligibility guidelines at "
    f"{DEVICE_UPGRADE_URL} and loyalty benefits at {LOYALTY_URL}. Emphasize exclusive loyalty benefits for long-term customers and consider escalation if churn risk is high."
)

# -------------------------------------------------------------------
# 4) STREAMLIT UI & CUSTOM CSS
# -------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Custom styling for all buttons */
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
    /* Custom styling for the Summarize Call button (different color) */
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

# Initialize/reset session state variables when switching calls
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
def analyze_sentiment(text: str) -> float:
    return TextBlob(text).sentiment.polarity

def sentiment_label(polarity: float) -> str:
    if polarity > 0.1:
        return "Positive"
    elif polarity < -0.1:
        return "Negative"
    else:
        return "Neutral"

def get_intent(customer_text: str, context: str = "") -> str:
    intent_prompt = (
        "Identify the intent of the following customer query in one or two words. "
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

def get_assisting_suggestion(customer_text: str, context: str = "") -> str:
    # Use a Product Catalogue based prompt for plan changes.
    if "plan" in context.lower() or "unlimited+" in context.lower():
        system_prompt = (
            "You are an AI assistant providing internal suggestions to a US Cellular agent. "
            "When recommending a plan change, refer to the Product Catalogue for accurate plan details. "
            "Format your suggestion as follows (each on a new line):\n"
            "From Product Catalogue\n"
            "[Plan Details: Current vs. Recommended]\n"
            "- Compare the customer's current plan with the recommended plan\n"
            "- Emphasize cost savings and matching features to the customer's usage\n\n"
            "Do not include any reference to CellSite. Keep the suggestion concise (one or two sentences) and focused on recommending a cheaper plan that fits the customer's needs.\n\n"
            f"Supplemental Context: {context}\n\n"
            "The user says:\n"
        )
    else:
        system_prompt = (
            "You are an AI assistant providing internal suggestions to a US Cellular agent. "
            "When providing troubleshooting advice, refer to the CellSite FAQs, Methods and Procedures, and troubleshooting documents. "
            "Format your suggestion as follows (each on a new line):\n"
            "From CellSite\n"
            "[Document Name: Apple Watch Troubleshooting Guide]\n"
            "[Section: eSIM Activation Status]\n"
            "- Check account for active eSIM status under Watch device details\n"
            "- Verify network provisioning is complete in the billing system if eSIM is active\n\n"
            "Do not include any reference to NumberSync. Keep the suggestion concise (one or two sentences) and focused on checking the customer's account for an active eSIM status and verifying network provisioning.\n\n"
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
    # This function is used for dynamic agent responses.
    agent_prompt = (
        "You are a US Cellular support agent with access to the customer's account information. "
        "Based on the internal AI suggestion provided below and the customer's query, craft your response by explicitly stating that you have reviewed the account. "
        "Do not ask the customer for any account details; instead, mention that you have checked the system. "
        "Your answer should clearly reference the internal suggestion and focus on confirming whether the necessary plan changes are appropriate. "
        "Please do not include any extraneous bracketed notes or meta commentary—only provide a clear, customer-facing answer.\n\n"
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

def run_conversation(transcript, context, conversation_speed=0.05):
    """
    Display the conversation while streaming each message.
    For customer turns, display sentiment, extract intent, and show an internal suggestion.
    For agent turns, simply stream the provided text.
    """
    st.session_state["final_transcript"] = ""
    st.session_state["current_transcript"] = []
    
    final_transcript_lines = []
    previous_intent = None
    for speaker, text in transcript:
        placeholder = st.empty()
        if speaker.lower() == "customer":
            # Stream the customer's message word by word.
            displayed_text = ""
            for word in text.split():
                displayed_text += word + " "
                placeholder.markdown(f"**Customer:** {displayed_text}")
                time.sleep(conversation_speed)
            final_transcript_lines.append(f"Customer: {text}")
            
            # Display sentiment.
            pol = analyze_sentiment(text)
            s_label = sentiment_label(pol)
            face_emoji = "😊" if s_label == "Positive" else "😞" if s_label == "Negative" else "😐"
            st.write(f"Sentiment: {s_label} {face_emoji} ({pol:.2f})")
            
            # Process customer message for intent.
            current_intent = get_intent(text, context)
            st.markdown(f"<div style='color:red'><strong>Intent: {current_intent}</strong></div>", unsafe_allow_html=True)
            if previous_intent and current_intent != previous_intent:
                st.markdown(f"<div style='color:red'><strong>Intent Shift: {previous_intent} --> {current_intent}</strong></div>", unsafe_allow_html=True)
            previous_intent = current_intent
            
            # Generate and display agent-assist suggestion.
            suggestion = get_assisting_suggestion(text, context=context)
            st.markdown(f"<div style='color:blue'><i>💡 {suggestion}</i></div>", unsafe_allow_html=True)
            final_transcript_lines.append(f"Agent Assist: {suggestion}")
            st.markdown("---")
        elif speaker.lower() == "agent":
            # Stream the agent's pre-scripted response word by word.
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
    
    # Save transcripts in session state and mark call as finished.
    st.session_state["current_transcript"] = transcript
    st.session_state["final_transcript"] = "\n".join(final_transcript_lines)
    st.session_state["call_finished"] = True
    if hasattr(st, "experimental_rerun"):
        st.experimental_rerun()

def analyze_call_overview(transcript_text: str) -> dict:
    """
    Request a detailed analysis in JSON format with the following keys:
      - "Summary of Discussion"
      - "Topics Discussed"
      - "Required Actions"
      - "Adherence to Suggestion"
      - "Overall Output/Result"
    """
    prompt = (
        "Given the following transcript of a call between a customer and a support agent, provide a detailed analysis in JSON format with the following keys:\n"
        "\"Summary of Discussion\": A brief summary of the discussion.\n"
        "\"Topics Discussed\": List the main topics covered in the call.\n"
        "\"Required Actions\": List any actions that need to be taken or were taken as a result of the call.\n"
        "\"Adherence to Suggestion\": Evaluate if the agent's response adhered to the internal suggestion and provide commentary.\n"
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

    # Compute time KPIs using different factors for customer and agent
    customer_factor = 0.5  # seconds per word for customer
    agent_factor = 0.5      # seconds per word for agent
    customer_time_sec = sum(len(text.split()) * customer_factor 
                            for (speaker, text) in st.session_state["current_transcript"] 
                            if speaker.lower() == "customer")
    agent_time_sec = sum(len(text.split()) * agent_factor 
                         for (speaker, text) in st.session_state["current_transcript"] 
                         if speaker.lower() == "agent")
    # Estimate silence time (using 0.5 seconds per turn gap)
    silence_time_sec = (len(st.session_state["current_transcript"]) - 1) * 0.5

    total_time_sec = customer_time_sec + agent_time_sec + silence_time_sec

    # Convert seconds to minutes
    customer_time_min = customer_time_sec / 60
    agent_time_min = agent_time_sec / 60
    silence_time_min = silence_time_sec / 60
    total_time_min = total_time_sec / 60

    with st.sidebar:
        st.subheader("Summarize Call")
        # KPI Tiles
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Call Duration (AHT)", f"{total_time_min:.2f} min")
        col2.metric("Customer Talk Time", f"{customer_time_min:.2f} min")
        col3.metric("Agent Talk Time", f"{agent_time_min:.2f} min")
        
        st.markdown("---")
        
        # Smooth Line Chart for Customer Sentiment Trend using Plotly
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
        
        # Doughnut Chart for Talk Time Distribution using Plotly
        time_distribution = pd.DataFrame({
            "Segment": ["Customer", "Agent", "Silence"],
            "Time (min)": [customer_time_min, agent_time_min, silence_time_min]
        })
        fig_doughnut = px.pie(time_distribution, names="Segment", values="Time (min)", hole=0.4,
                              title="Talk Time Distribution")
        st.plotly_chart(fig_doughnut)
        
        st.markdown("---")
        
        # Detailed Call Analysis with Overall Output/Result moved to the end.
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
            if isinstance(adherence, dict):
                rating = adherence.get("Rating", "N/A")
                commentary = adherence.get("Commentary", "N/A")
                st.markdown(f"**Rating:** {rating}\n\n**Commentary:** {commentary}")
            else:
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

# -------------------------------------------------------------------
# 8) RUN LOGIC BASED ON BUTTON CLICKS
# -------------------------------------------------------------------
if apple_watch_button:
    st.session_state["call_finished"] = False
    st.session_state["final_transcript"] = ""
    st.session_state["current_transcript"] = []
    st.empty()  # Clear any previous conversation
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
    st.subheader("Live Call Assist – Device Upgrade Issue (Churn Risk)")
    run_conversation(transcript_device_upgrade, context=context_device_upgrade, conversation_speed=0.05)

if analyze_call_button:
    st.subheader("Summarize Call (Results are shown in the sidebar)")
    perform_analysis()
