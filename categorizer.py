from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage
import os
import logging

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

    def categorize_email(self, subject: str, body: str, sender: str) -> str:
        """
        Categorize an email using GrokGPT

        Args:
            subject: Email subject line
            body: Email body content
            sender: Email sender address

        Returns:
            Category string: "Customer Support", "Marketing", or "Others"
        """
        try:
            # Prepare the email content for classification
            email_content = f"""
            From: {sender}
            Subject: {subject}
            
            Body:
            {body[:2000]}  # Limit body to first 2000 characters
            """

            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(
                    content=f"Please categorize this email:\n\n{email_content}"
                ),
            ]

            response = self.llm.invoke(messages)
            category = response.content.strip()

            # Validate the response
            valid_categories = ["Customer Support", "Marketing", "Others"]
            if category in valid_categories:
                logger.info(f"Email categorized as: {category}")
                return category
            else:
                logger.warning(
                    f"Invalid category returned: {category}, defaulting to 'Others'"
                )
                return "Others"

        except Exception as e:
            logger.error(f"Error categorizing email: {str(e)}")
            return "Others"  # Default category on error
