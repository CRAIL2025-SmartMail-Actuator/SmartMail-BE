import os
import logging
from typing import Dict, List, Any, TypedDict
from dataclasses import dataclass
import json

from langchain_groq import ChatGroq
from langchain.schema import HumanMessage
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
import numpy as np

from langgraph.graph import StateGraph, END
from langgraph.graph.message import MessagesState

from langgraph.graph import StateGraph, END
from langgraph.graph.message import MessagesState
from typing import Optional




logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GROQ_API_KEY = "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"
GROQ_MODEL = "llama-3.3-70b-versatile"
QDRANT_HOST = "192.168.0.135"
QDRANT_PORT = int(6334)
COLLECTION_NAME = "Crail_data"


@dataclass
class CurrentUser:
    """User information structure"""

    user_id: int
    name: str
    email: str


class EmailResponseState(TypedDict):
    """State structure for the LangGraph flow"""

    user_email: str
    current_user: CurrentUser
    email_summary: str
    search_results: List[Dict[str, Any]]
    response_email: Optional[Dict[str, str]]
    validation_score: int
    error: str


class EmailResponseFlow:
    """Main class for handling email response generation flow"""

    def __init__(self):
        """Initialize the email response flow components"""
        self.llm = self._init_llm()
        self.qdrant_client = self._init_qdrant()
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
        self.graph = self._build_graph()

    def _init_llm(self) -> ChatGroq:
        """Initialize ChatGroq LLM"""
        return ChatGroq(
            model=GROQ_MODEL,
            api_key=GROQ_API_KEY,
            temperature=0.5,
            max_tokens=5000,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None,
        )

    def _init_qdrant(self) -> QdrantClient:
        """Initialize Qdrant client"""
        try:
            client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
            logger.info(f"Connected to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}")
            return client
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        graph = StateGraph(EmailResponseState)

        # Add nodes
        graph.add_node("summarize_email", self.summarize_email_intent)
        graph.add_node("search_qdrant", self.search_knowledge_base)
        graph.add_node("generate_response", self.generate_email_response)
        graph.add_node("validate_response", self.validate_email_response)

        # Define edges
        graph.set_entry_point("summarize_email")
        graph.add_edge("summarize_email", "search_qdrant")
        graph.add_edge("search_qdrant", "generate_response")
        graph.add_edge("generate_response", "validate_response")
        graph.add_edge("validate_response", END)

        return graph.compile()

    def summarize_email_intent(self, state: EmailResponseState) -> EmailResponseState:
        """Step 1: Summarize the main intent of the incoming email"""
        logger.info("Step 1: Summarizing email intent")

        try:
            prompt = f"""
            Analyze the following email and extract the main question, request, or intent.
            Provide a clear, concise summary that captures what the sender is asking for or needs help with.
            
            Email content:
            {state["user_email"]}
            
            Please provide only the summary of the main intent, without any additional commentary.
            """

            response = self.llm.invoke([HumanMessage(content=prompt)])
            email_summary = response.content.strip()

            logger.info(f"Email summary: {email_summary}")

            return {**state, "email_summary": email_summary}

        except Exception as e:
            logger.error(f"Error in summarize_email_intent: {e}")
            return {**state, "error": f"Failed to summarize email: {str(e)}"}

    def search_knowledge_base(self, state: EmailResponseState) -> EmailResponseState:
        """Step 2: Search Qdrant for relevant documents"""
        logger.info("Step 2: Searching knowledge base")

        try:
            # Create embedding for the email summary
            query_embedding = self.encoder.encode(state["email_summary"]).tolist()

            user_filter = Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(
                            value=state["current_user"].user_id,
                        ),
                    )
                ]
            )

            # Search Qdrant
            search_results = self.qdrant_client.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_embedding,
                query_filter=user_filter,
                limit=5,
                with_payload=True,
                with_vectors=False,
            )

            # Format results
            formatted_results = []
            for result in search_results:
                formatted_results.append(
                    {
                        "score": result.score,
                        "data": result.payload.get("data", ""),
                        "metadata": result.payload.get("metadata", {}),
                    }
                )

            logger.info(f"Found {len(formatted_results)} relevant documents")

            return {**state, "search_results": formatted_results}

        except Exception as e:
            logger.error(f"Error in search_knowledge_base: {e}")
            return {
                **state,
                "search_results": [],
                "error": f"Failed to search knowledge base: {str(e)}",
            }

    def generate_email_response(self, state: EmailResponseState) -> EmailResponseState:
        """Step 3: Generate response email using LLM"""
        logger.info("Step 3: Generating email response")

        try:
            # Prepare context from search results
            context = ""
            if state["search_results"]:
                context = "\n\nRelevant information from knowledge base:\n"
                for i, result in enumerate(state["search_results"], 1):
                    context += f"{i}. {result['data']}\n"

            user = state["current_user"]

            prompt = f"""
            You are {user.name} responding to an email inquiry.

            Original email:
            {state["user_email"]}

            Email intent summary:
            {state["email_summary"]}
            {context}

            Please generate a professional, helpful email response in JSON format that:
            1. Addresses the sender's specific question or request
            2. Uses the relevant information from the knowledge base if available
            3. Maintains a professional and friendly tone
            4. Includes appropriate email formatting (greeting, body, closing)
            5. Signs off with {user.name}

            Return your response in this exact JSON format:
            {{
            "response_email_subject": "Subject line here...",
            "response_email_body": "Full email body here, including greeting, content, and sign-off with {user.name}."
            }}

            Only return valid JSON. Do not include any explanations or text outside the JSON.
            """

            response = self.llm.invoke([HumanMessage(content=prompt)])
            response_json = json.loads(response.content)

            logger.info("Structured email response generated successfully")

            return {**state, "response_email": response_json}

        except Exception as e:
            logger.error(f"Error in generate_email_response: {e}")
            return {**state, "error": f"Failed to generate response: {str(e)}"}

    def validate_email_response(self, state: EmailResponseState) -> EmailResponseState:
        """Step 4: Validate how well the response addresses the original email"""
        logger.info("Step 4: Validating email response")

        try:
            prompt = f"""
            Evaluate how well the following email response addresses the original inquiry.
            
            Original Email:
            {state["user_email"]}
            
            Generated Response:
            {state["response_email"]}
            
            Please rate the response on a scale of 1-10 based on:
            - How well it addresses the original question/request
            - Relevance and accuracy of information provided
            - Professional tone and clarity
            - Completeness of the response
            
            Provide only a single number between 1 and 10 as your response.
            """

            response = self.llm.invoke([HumanMessage(content=prompt)])

            # Extract numeric score
            try:
                validation_score = int(response.content.strip())
                if validation_score < 1 or validation_score > 10:
                    validation_score = 5  # Default to middle score if invalid
            except ValueError:
                validation_score = 5  # Default score if parsing fails

            logger.info(f"Validation score: {validation_score}/10")

            return {**state, "validation_score": validation_score}

        except Exception as e:
            logger.error(f"Error in validate_email_response: {e}")
            return {
                **state,
                "validation_score": 0,
                "error": f"Failed to validate response: {str(e)}",
            }

    def process_email(
        self, user_email: str, current_user: CurrentUser
    ) -> EmailResponseState:
        """Main method to process an email through the entire flow"""
        logger.info("Starting email response generation flow")

        initial_state = EmailResponseState(
            user_email=user_email,
            current_user=current_user,
            email_summary="",
            search_results=[],
            response_email={"response_email_subject": "", "response_email_body": ""},
            validation_score=0,
            error="",
        )

        try:
            final_state = self.graph.invoke(initial_state)
            logger.info("Email response flow completed successfully")
            return final_state
        except Exception as e:
            logger.error(f"Error in email processing flow: {e}")
            return {**initial_state, "error": f"Flow execution failed: {str(e)}"}


def ai_reponse(
    user_id, user_name, user_email, customer_subject, customer_email
):

    # Initialize the flow
    email_flow = EmailResponseFlow()

    # Example user
    current_user = CurrentUser(
        user_id=user_id,
        name=user_name,
        email=user_email,
    )

    # Example incoming email
    result = email_flow.process_email(customer_subject + customer_email, current_user)
    return {
        "subject": result["response_email"]["response_email_subject"],
        "email_body": result["response_email"]["response_email_body"],
        "confidence_score": result["validation_score"],
    }

    # Process the email
    # result = email_flow.process_email(user_email, current_user)

    # # Display results
    # print("=" * 60)
    # print("EMAIL RESPONSE GENERATION RESULTS")
    # print("=" * 60)

    # if result.get("error"):
    #     print(f"❌ Error: {result['error']}")
    #     return

    # print(f"📧 Original Email Summary:")
    # print(f"   {result['email_summary']}")
    # print()

    # print(f"🔍 Search Results Found: {len(result['search_results'])}")
    # for i, result_item in enumerate(result['search_results'], 1):
    #     print(f"   {i}. Score: {result_item['score']:.3f}")
    #     print(f"      data: {result_item['data'][:100]}...")
    # print()

    # print(f"✉️ Generated Response:")
    # print(f"   Subject: {result['response_email']['response_email_subject']}")
    # print(f"   Body:")
    # print(result['response_email']["response_email_body"])
    # print()

    # print(f"⭐ Validation Score: {result['validation_score']}/10")
    # print("=" * 60)
