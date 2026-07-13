"""Two-node LangGraph for synthetic retrieval and provider-backed generation."""

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agents.chat.provider import LLMGenerationRequest, LLMProvider
from app.agents.chat.retrieval import Retriever
from app.agents.chat.state import ChatGraphState


class ChatGraphRunner:
    """Compile and run a minimal, bounded chat graph."""

    def __init__(self, *, retriever: Retriever, provider: LLMProvider) -> None:
        self._retriever = retriever
        self._provider = provider
        builder = StateGraph(ChatGraphState)
        builder.add_node("retrieve", self._retrieve)
        builder.add_node("generate", self._generate)
        builder.add_edge(START, "retrieve")
        builder.add_edge("retrieve", "generate")
        builder.add_edge("generate", END)
        self._graph: CompiledStateGraph[
            ChatGraphState, None, ChatGraphState, ChatGraphState
        ] = builder.compile()

    async def _retrieve(self, state: ChatGraphState) -> dict[str, object]:
        focused_query = " ".join(
            part
            for part in (state.user_message, state.business_context.retrieval_text())
            if part
        )
        evidence = await self._retriever.retrieve(focused_query)
        return {"evidence": evidence}

    async def _generate(self, state: ChatGraphState) -> dict[str, object]:
        response = await self._provider.generate(
            LLMGenerationRequest(
                user_message=state.user_message,
                business_context=state.business_context,
                conversation=state.conversation,
                evidence=state.evidence,
                prompt_version=state.prompt_version,
            )
        )
        return {"answer": response.text}

    async def run(self, state: ChatGraphState) -> ChatGraphState:
        """Run the graph and revalidate all node output at the application boundary."""
        raw_output = await self._graph.ainvoke(state, version="v2")
        return ChatGraphState.model_validate(raw_output.value)
