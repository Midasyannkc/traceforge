"""
Documents the real Amazon Bedrock Agent Runtime call shape
(`boto3 bedrock-agent-runtime invoke_agent`) behind a swappable client
interface, backed by a disclosed deterministic mock since no live AWS
credentials are reachable from this build sandbox (see
data/bronze/SOURCE.md). Consistent with this portfolio's established
pattern for LLM-backed components built without live API access
(AdvisorAgent, Undercurrent).
"""
from abc import ABC, abstractmethod


class AgentClient(ABC):
    @abstractmethod
    def invoke_agent(self, agent_id, session_id, input_text):
        """Mirrors boto3's bedrock-agent-runtime.invoke_agent(agentId=...,
        sessionId=..., inputText=...) response shape: a dict with
        'completion' (streamed text) and 'citations' (RAG/Knowledge Base
        grounding references)."""
        raise NotImplementedError


class DeterministicMockAgentClient(AgentClient):
    """
    Disclosed deterministic stand-in for live Bedrock access. Returns a
    fixed, documented response shape so downstream code (and the real
    OTel instrumentation wrapping it) exercises exactly the same
    structure a live `invoke_agent` call would return.
    """

    def invoke_agent(self, agent_id, session_id, input_text):
        return {
            "completion": f"[mock-agent:{agent_id}] handled: {input_text[:60]}",
            "citations": [
                {"source": "knowledge-base", "retrievedReferences": []}
            ],
            "sessionId": session_id,
        }


def real_boto3_call_shape_documentation():
    """Not executed against a live account; documents the real call this
    stands in for, for reviewers to compare against the mock above."""
    return """
    import boto3
    client = boto3.client("bedrock-agent-runtime", region_name="us-east-1")
    response = client.invoke_agent(
        agentId="AGENT_ID",
        agentAliasId="AGENT_ALIAS_ID",
        sessionId="SESSION_ID",
        inputText="customer question text",
    )
    # response["completion"] is an EventStream of chunks in the real API;
    # DeterministicMockAgentClient above returns the fully-assembled
    # text for test determinism.
    """
