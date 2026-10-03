from src.bedrock_agent import DeterministicMockAgentClient


def test_mock_agent_client_matches_real_invoke_agent_response_shape():
    client = DeterministicMockAgentClient()
    resp = client.invoke_agent("agent-1", "session-1", "What is the claim status?")
    assert "completion" in resp
    assert "citations" in resp
    assert resp["sessionId"] == "session-1"
