from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent, AgentType
from dotenv import load_dotenv
import os

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

from orchestrator.cloud_analyzer import get_average_cpu_usage
from tools.metrics_tools import get_cpu_usage, get_instance_status
from tools.cost_tools import reduce_cost_recommendations, get_cost_summary
from tools.error_tools import get_current_errors, analyze_error_trend

@tool
def cpu_usage_tool(query: str) -> str:
    """Fetches the current CPU usage of the instance."""
    return str(get_average_cpu_usage())

@tool
def instance_status_tool(query: str) -> str:
    """Returns the running status of an EC2 instance."""
    return str(get_instance_status())

@tool
def cost_tool(query: str) -> str:
    """Provides cost optimization recommendations for the cloud environment."""
    return str(reduce_cost_recommendations())

@tool
def cost_summary_tool(query: str) -> str:
    """Displays the estimated monthly cost of AWS resources."""
    return str(get_cost_summary())

@tool
def error_tool(query: str) -> str:
    """Fetches the current cloud system errors from simulated logs."""
    return str(get_current_errors())

@tool
def error_trend_tool(query: str) -> str:
    """Analyzes and summarizes recent error trends."""
    return str(analyze_error_trend())

tools = [
    cpu_usage_tool,
    instance_status_tool,
    cost_tool,
    cost_summary_tool,
    error_tool,
    error_trend_tool,
]

def get_orchestrator_agent():
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-lite",
        google_api_key=GOOGLE_API_KEY
    )
    agent = initialize_agent(tools, llm, agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)
    return agent
