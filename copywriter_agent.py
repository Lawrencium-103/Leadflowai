from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

def generate_email_content(lead_row: dict, openrouter_api_key: str = None, user_offer: str = ""):
    """
    Generates personalized email components using Llama 4 (405B) via OpenRouter.
    """
    api_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
    llm = ChatOpenAI(
        model="meta-llama/llama-3.1-405b-instruct", 
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://leadflow-ai.streamlit.app",
            "X-Title": "LeadFlow AI"
        }
    )
    
    enriched_data = lead_row.get('Enriched Data', 'No specific context found.')
    founder_name = lead_row.get('Founder Name', 'there')
    position = lead_row.get('Position', 'Founder')
    domain = lead_row.get('Domain', 'your company')
    location = lead_row.get('Location', 'your area')

    # Default offer if empty
    my_offer = user_offer if user_offer else "I help scaling companies automate their B2B systems and lead generation."

    prompt = f"""
    You are Lawrence Oladeji, a high-level AI and Automation Workflow Developer.
    MISSION: Write a high-impact, value-driven note to {founder_name} ({position}) at {domain}.
    
    GUIDELINES:
    - BE BRIEF. Brevity is respect.
    - If you must write more than 3-4 sentences, you MUST provide an "Instant Win" (e.g., a specific automation idea or a data insight).
    - TONE: Professional peer, technical yet accessible. NO corporate fluff.
    - The "{my_offer}" should feel like a relief to their current pain.
    - Mention their context in {location} to anchor the relationship.

    STRUCTURE (Internal):
    1. Recognition: Sharp observation about {domain} or a specific trigger.
    2. Value/Win: Offer a specific insight related to your role as an AI developer.
    3. Proposal: Reframed logic: "If [Trigger] then [Pain]... I built [Solution] for [Outcome]."
    4. CTA (REPLY-FIRST): Ask a very simple, low-pressure "No-oriented" question that is easy to reply to (e.g., "Is this completely irrelevant to your priorities right now?" or "Would it be a waste of time to explore this?"). Getting a reply is our #1 priority for sender reputation.

    Format your response EXACTLY as follows:
    [SUBJECT]: ...
    [MESSAGE]: ...
    """

    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content
    
    # New fluid parsing
    try:
        def extract(marker):
            if marker in content:
                parts = content.split(marker)
                if len(parts) > 1:
                    val = parts[1].split('[')[0].strip()
                    return val.replace(':', '').strip()
            return ""

        subject = extract('[SUBJECT]')
        full_message = extract('[MESSAGE]')
        
        # Split full message into Opener/Body/Closing for the UI
        lines = full_message.split('\n\n')
        opener = lines[0] if len(lines) > 0 else "Hi there,"
        body = "\n\n".join(lines[1:-1]) if len(lines) > 2 else ""
        closing = lines[-1] if len(lines) > 1 else "Best,"
        
        if not subject or not full_message:
            raise ValueError("Incomplete generation")
            
        return subject, opener, body, closing
    except Exception as e:
        # Ultra-human fallback
        subject = f"question about {domain}"
        opener = f"Hi {founder_name}, was just looking into {domain} and noticed your team's expansion in {location}."
        body = f"Usually, a move like that makes the lead gen side a bit messy. {my_offer.lower()}"
        closing = "Is this completely irrelevant to your priorities right now?\n\nBest,"
        return subject, opener, body, closing
