import os
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_community.tools import TavilySearchResults
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

# Define the state for the research graph
class AgentState(TypedDict):
    query: str
    search_results: list
    summary: str

def create_research_graph(openrouter_api_key: str = None, tavily_api_key: str = None):
    """
    Creates a LangGraph for lead research using OpenRouter, Tavily, and DuckDuckGo.
    """
    # Prefer arguments, fallback to env vars
    tavily_api_key = tavily_api_key or os.getenv("TAVILY_API_KEY")
    openrouter_api_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
    
    if tavily_api_key:
        os.environ["TAVILY_API_KEY"] = tavily_api_key
    
    # Initialize tools and model (OpenRouter)
    tavily_tool = TavilySearchResults(max_results=3)
    llm = ChatOpenAI(
        model="meta-llama/llama-3.1-405b-instruct", 
        openai_api_key=openrouter_api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://leadflow-ai.streamlit.app", # Optional, but good practice
            "X-Title": "LeadFlow AI"
        }
    )

    def search_node(state: AgentState):
        query = state['query']
        import feedparser
        from duckduckgo_search import DDGS
        # Combine results from multiple tools for 100% reliability
        results = []
        
        # 1. Tavily Search
        try:
            t_results = tavily_tool.invoke({"query": query})
            results.append(f"--- Tavily Results ---\n{t_results}")
        except Exception as e:
            results.append(f"Tavily Search Failed: {e}")
            
        # 2. DuckDuckGo (Free & Reliable - Direct Library Use)
        try:
            with DDGS() as ddgs:
                ddg_results = [r for r in ddgs.text(query, max_results=5)]
            results.append(f"--- DuckDuckGo Results ---\n{ddg_results}")
        except Exception as e:
            results.append(f"DuckDuckGo Search Failed: {e}")

        # 3. Dynamic RSS Check (Optional but powerful)
        try:
            # Try to find common RSS feeds if domain is in query
            domain_parts = [p for p in query.split() if '.' in p and 'http' not in p]
            if domain_parts:
                domain = domain_parts[0]
                rss_url = f"https://{domain}/feed"
                feed = feedparser.parse(rss_url)
                if feed.entries:
                    latest = [e.title for e in feed.entries[:3]]
                    results.append(f"--- RSS News ({domain}) ---\n{latest}")
        except:
            pass
            
        return {"search_results": results}

    def summarize_node(state: AgentState):
        results = state['search_results']
        prompt = f"""
        You are a Deep Research Agent specializing in the "H.E.A.T." System (Hot, Engaged, Able, Targetable).
        Based on the following search results, identify the "Trigger Events" or "Digital Signals" that make this lead a prime target.
        
        Look for:
        1. Growth Triggers: Funding, new hires, office expansion, new launches.
        2. Problem Triggers: Bad reviews, failed launches, outdated tech, recent departures.
        3. Change Triggers: Rebrands, new platforms, speaking at events.
        
        Apply the SLAM Filter:
        - Specific Need: What pain is visible?
        - Attribute: Does it look like they have money/budget (funding, paid ads)?

        Search Results:
        {results}

        Format your summary as:
        RELIABILITY_SCORE: [1-10] (Based on strength of trigger events)
        SCORE_REASON: [Short justification for the score]
        TRIGGER: [Specific Event/Change]
        PAIN: [Likely business pain following the trigger]
        SIGNAL: [Summary of SLAM/HEAT findings]
        """
        response = llm.invoke([HumanMessage(content=prompt)])
        return {"summary": response.content}

    # Build the graph
    workflow = StateGraph(AgentState)
    workflow.add_node("search", search_node)
    workflow.add_node("summarize", summarize_node)

    workflow.set_entry_point("search")
    workflow.add_edge("search", "summarize")
    workflow.add_edge("summarize", END)

    return workflow.compile()

def enrich_lead(lead_row: dict, groq_api_key: str, tavily_api_key: str):
    """
    Enriches a single lead row.
    """
    location = lead_row.get('Location', '')
    query = f"{lead_row['Founder Name']} {lead_row['Domain']} {lead_row['Position']} {location} recent news funding achievements"
    graph = create_research_graph(groq_api_key, tavily_api_key)
    
    result = graph.invoke({"query": query})
    return result.get('summary', 'No summary generated.')
