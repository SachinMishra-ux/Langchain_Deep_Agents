"""Unit tests for agent compilation and tools."""

from locdata_code.agent import create_locdata_agent
from locdata_code.config import LocDataConfig


def test_agent_graph_compiles(tmp_path):
    cfg = LocDataConfig.load(project_root=tmp_path)
    # Ensure it compiles to a LangGraph CompiledStateGraph
    agent = create_locdata_agent(cfg)
    assert agent is not None
    assert "tools" in agent.nodes
    assert "model" in agent.nodes
