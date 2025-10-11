from prefect import flow, task
from orchestrator.orchestrator_agent import get_orchestrator_agent

@task
def analyze_prompt(prompt: str):
    agent = get_orchestrator_agent()
    return agent.run(prompt)

@flow
def orchestrator_flow(prompt: str):
    print("🧠 Analyzing prompt:", prompt)
    response = analyze_prompt(prompt)
    print("✅ Agent Response:", response)
    return response

if __name__ == "__main__":
    orchestrator_flow("What is my CPU usage right now?")
