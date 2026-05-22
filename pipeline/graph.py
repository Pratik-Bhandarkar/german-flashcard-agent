# graph.py
# Defines the LangGraph pipeline that wires all four agents together.
# This is the single entry point for the entire flashcard generation pipeline.
# Each node in the graph corresponds to one agent.

from typing import TypedDict
from langgraph.graph import StateGraph, END

from pipeline.agents import (
    parser_agent,
    enrichment_agent,
    validator_agent,
    storage_agent
)


# --- Pipeline State ---
# This is the shared state object that flows through every node.
# TypedDict gives us type hints so VS Code can autocomplete field names.
class FlashcardPipelineState(TypedDict):
    # Input fields — set before the pipeline starts
    input_type: str        # "text", "image", or "pdf"
    input_data: str        # raw text or file path
    source: str            # where the words came from
    tags: list[str]        # labels to apply to all cards in this batch

    # Output fields — filled in by each agent as the pipeline runs
    words: list[str]                # filled by parser agent
    enrichment_result: dict         # filled by enrichment agent
    validation_result: dict         # filled by validator agent
    storage_result: dict            # filled by storage agent


# --- Node Functions ---
# Each node receives the full state, does its work,
# and returns a dictionary of fields to update in the state.
# LangGraph merges the returned dict back into the state automatically.

def parser_node(state: FlashcardPipelineState) -> dict:
    """Extracts raw German words from the input."""
    print("\n[1/4] Parser Agent running...")

    words = parser_agent.run(
        input_type=state["input_type"],
        input_data=state["input_data"]
    )

    print(f"      Extracted {len(words)} words: {words}")
    return {"words": words}


def enrichment_node(state: FlashcardPipelineState) -> dict:
    """Enriches each word with DeepL translation and LLM data."""
    print("\n[2/4] Enrichment Agent running...")

    enrichment_result = enrichment_agent.run(
        words=state["words"],
        source=state["source"],
        tags=state["tags"]
    )

    return {"enrichment_result": enrichment_result}


def validator_node(state: FlashcardPipelineState) -> dict:
    """Validates every enriched flashcard before storage."""
    print("\n[3/4] Validator Agent running...")

    validation_result = validator_agent.run(
        enrichment_result=state["enrichment_result"]
    )

    return {"validation_result": validation_result}


def storage_node(state: FlashcardPipelineState) -> dict:
    """Saves all valid flashcards to the database."""
    print("\n[4/4] Storage Agent running...")

    storage_result = storage_agent.run(
        validation_result=state["validation_result"]
    )

    return {"storage_result": storage_result}


# --- Graph Definition ---
def build_pipeline() -> StateGraph:
    """
    Assembles the LangGraph pipeline by connecting all four nodes.
    Returns a compiled graph ready to run.
    """
    # Initialise the graph with our state schema
    graph = StateGraph(FlashcardPipelineState)

    # Add each agent as a node
    graph.add_node("parser", parser_node)
    graph.add_node("enrichment", enrichment_node)
    graph.add_node("validator", validator_node)
    graph.add_node("storage", storage_node)

    # Define the edges — the order agents run in
    graph.set_entry_point("parser")
    graph.add_edge("parser", "enrichment")
    graph.add_edge("enrichment", "validator")
    graph.add_edge("validator", "storage")
    graph.add_edge("storage", END)

    return graph.compile()


# --- Public Entry Point ---
def run_pipeline(
    input_type: str,
    input_data: str,
    source: str = "unknown",
    tags: list[str] = None
) -> dict:
    """
    Main entry point for the flashcard generation pipeline.
    Call this function to process any input through the full pipeline.

    Args:
        input_type: "text", "image", or "pdf"
        input_data: raw text string or file path
        source: description of where the words came from
        tags: optional labels to apply to all cards in this batch

    Returns:
        Final pipeline state containing all agent outputs
    """
    if tags is None:
        tags = []

    pipeline = build_pipeline()

    # Define the initial state before the pipeline starts
    initial_state = {
        "input_type": input_type,
        "input_data": input_data,
        "source": source,
        "tags": tags,
        "words": [],
        "enrichment_result": {},
        "validation_result": {},
        "storage_result": {}
    }

    print("=" * 50)
    print("Starting Flashcard Generation Pipeline")
    print(f"Input type: {input_type}")
    print(f"Source:     {source}")
    print(f"Tags:       {tags}")
    print("=" * 50)

    final_state = pipeline.invoke(initial_state)

    print("\n" + "=" * 50)
    print("Pipeline Complete!")
    print(f"Words extracted:  {len(final_state['words'])}")
    print(f"Cards saved:      {final_state['storage_result']['saved']}")
    print(f"Cards skipped:    {final_state['storage_result']['skipped']}")
    print(f"Total failures:   {len(final_state['storage_result']['failures'])}")
    print("=" * 50)

    return final_state