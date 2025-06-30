from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage
import os
import logging

from models import Category
from db_sync import SyncSessionLocal

logger = logging.getLogger(__name__)


class EmailCategorizer:
    def __init__(self):
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key="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",
            temperature=0.1,
            max_tokens=10000,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None,
        )

        self.system_prompt = """
        You are an email classification system. Your task is to categorize emails into exactly one of these three categories:

        1. "Customer Support" - Emails asking for help, reporting issues, requesting assistance, complaints, technical problems, or any support-related queries.

        2. "Marketing" - Promotional emails, newsletters, advertisements, product announcements, sales offers, or any marketing-related content.

        3. "Others" - Any email that doesn't clearly fit into Customer Support or Marketing categories, including personal messages, administrative emails, confirmations, etc.

        Instructions:
        - Respond with ONLY the category name: "Customer Support", "Marketing", or "Others"
        - Do not include any additional text, explanations, or formatting
        - Base your decision on the email subject and content
        - If uncertain, choose "Others"
        """

    def categorize_email(
        self, subject: str, body: str, sender: str, user_id: int, categories
    ) -> int:
        """
        Categorize an email using GrokGPT and return the category ID

        Args:
            subject: Email subject line
            body: Email body content
            sender: Email sender address
            user_id: User ID to fetch categories for

        Returns:
            Category ID (int): ID of the matching category, or default category ID if not found
        """
        try:
            with SyncSessionLocal() as session:
                # Fetch user's categories from database
                # user_categories = (
                #     session.query(Category).filter(Category.user_id == user_id).all()
                # )

                if not categories:
                    logger.warning(f"No categories found for user {user_id}")
                    return None  # or create a default category

                # Create a mapping of category names to IDs
                category_map = {cat.name: cat.id for cat in categories}
                valid_category_names = list(category_map.keys())

                # Prepare the email content for classification
                email_content = f"""
                From: {sender}
                Subject: {subject}
                
                Body:
                {body[:2000]}  # Limit body to first 2000 characters
                """

                # Update system prompt to include available categories
                dynamic_prompt = f"{self.system_prompt}\n\nAvailable categories: {', '.join(valid_category_names)}"

                messages = [
                    SystemMessage(content=dynamic_prompt),
                    HumanMessage(
                        content=f"Please categorize this email into one of these categories: {', '.join(valid_category_names)}\n\nEmail:\n{email_content}"
                    ),
                ]

                response = self.llm.invoke(messages)
                category_name = response.content.strip()

                # Validate the response and return category ID
                if category_name in category_map:
                    category_id = category_map[category_name]
                    logger.info(
                        f"Email categorized as: {category_name} (ID: {category_id})"
                    )
                    return category_id
                else:
                    logger.warning(f"Invalid category returned: {category_name}")
                    # Return the first available category as default, or handle as needed
                    default_category_id = list(category_map.values())[0]
                    logger.info(f"Defaulting to category ID: {default_category_id}")
                    return default_category_id

        except Exception as e:
            logger.error(f"Error categorizing email: {str(e)}")
            # Return a default category ID or None based on your requirements
            return None
