from langgraph.graph import END, START, StateGraph

from aipilot.agent.nodes import AgentNodes
from aipilot.agent.state import AgentState


def needs_plan(state: AgentState) -> str:
    return "plan" if state["kind"] == "complex" else "agent"


def wants_tools(state: AgentState) -> str:
    return "tools" if state["messages"][-1].get("tool_calls") else "end"


def build_graph(nodes: AgentNodes, checkpointer=None):
    graph = StateGraph(AgentState)
    graph.add_node("understand", nodes.understand)
    graph.add_node("knowledge", nodes.load_knowledge)
    graph.add_node("plan", nodes.plan)
    graph.add_node("agent", nodes.agent)
    graph.add_node("tools", nodes.tools)
    graph.add_edge(START, "understand")
    graph.add_edge("understand", "knowledge")
    graph.add_conditional_edges("knowledge", needs_plan, {"plan": "plan", "agent": "agent"})
    graph.add_edge("plan", "agent")
    graph.add_conditional_edges("agent", wants_tools, {"tools": "tools", "end": END})
    graph.add_edge("tools", "agent")
    return graph.compile(checkpointer=checkpointer)
