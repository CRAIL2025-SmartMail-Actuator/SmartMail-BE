from flask import Blueprint, jsonify, request, current_app
from app.models import Email
from app.email_service import EmailService
from app import db
import logging

logger = logging.getLogger(__name__)

main = Blueprint("main", __name__)

# Global email service instance
email_service = None


def get_email_service():
    global email_service
    if email_service is None:
        email_service = EmailService()
    return email_service


@main.route("/")
def index():
    """Health check endpoint"""
    return jsonify({"status": "running", "message": "Email Categorizer API is running"})


@main.route("/api/emails", methods=["GET"])
def get_all_emails():
    """Get all stored emails with optional filtering"""
    try:
        # Get query parameters
        category = request.args.get("category")
        sender = request.args.get("sender")
        limit = request.args.get("limit", type=int)
        offset = request.args.get("offset", type=int, default=0)

        # Build query
        query = Email.query

        if category:
            query = query.filter(Email.category == category)

        if sender:
            query = query.filter(Email.sender.ilike(f"%{sender}%"))

        # Order by received_at descending
        query = query.order_by(Email.received_at.desc())

        # Apply pagination
        if limit:
            query = query.limit(limit).offset(offset)

        emails = query.all()

        # Convert to dict
        emails_data = [email.to_dict() for email in emails]

        # Get total count for pagination
        total_count = Email.query.count()
        if category:
            total_count = Email.query.filter(Email.category == category).count()
        if sender:
            total_count = Email.query.filter(Email.sender.ilike(f"%{sender}%")).count()

        return jsonify(
            {
                "emails": emails_data,
                "total_count": total_count,
                "count": len(emails_data),
            }
        )

    except Exception as e:
        logger.error(f"Error retrieving emails: {str(e)}")
        return jsonify({"error": f"Failed to retrieve emails  {str(e)}"}), 500


@main.route("/api/emails/<int:email_id>", methods=["GET"])
def get_email(email_id):
    """Get a specific email by ID"""
    try:
        email = Email.query.get_or_404(email_id)
        return jsonify(email.to_dict())
    except Exception as e:
        logger.error(f"Error retrieving email {email_id}: {str(e)}")
        return jsonify({"error": "Email not found"}), 404


@main.route("/api/stats", methods=["GET"])
def get_stats():
    """Get email statistics"""
    try:
        total_emails = Email.query.count()
        customer_support = Email.query.filter_by(category="Customer Support").count()
        marketing = Email.query.filter_by(category="Marketing").count()
        others = Email.query.filter_by(category="Others").count()

        return jsonify(
            {
                "total_emails": total_emails,
                "categories": {
                    "Customer Support": customer_support,
                    "Marketing": marketing,
                    "Others": others,
                },
            }
        )

    except Exception as e:
        logger.error(f"Error retrieving stats: {str(e)}")
        return jsonify({"error": "Failed to retrieve statistics"}), 500


@main.route("/api/fetch-emails", methods=["POST"])
def fetch_emails():
    """Manually trigger fetching all emails"""
    try:
        service = get_email_service()

        # Run in background thread to avoid timeout
        import threading

        thread = threading.Thread(target=service.fetch_all_emails)
        thread.daemon = True
        thread.start()

        return jsonify({"message": "Email fetching started in background"})

    except Exception as e:
        logger.error(f"Error starting email fetch: {str(e)}")
        return jsonify({"error": "Failed to start email fetching"}), 500


@main.route("/api/start-monitoring", methods=["POST"])
def start_monitoring():
    """Start email monitoring"""
    try:
        service = get_email_service()
        service.start_monitoring()
        return jsonify({"message": "Email monitoring started"})

    except Exception as e:
        logger.error(f"Error starting monitoring: {str(e)}")
        return jsonify({"error": "Failed to start monitoring"}), 500


@main.route("/api/stop-monitoring", methods=["POST"])
def stop_monitoring():
    """Stop email monitoring"""
    try:
        service = get_email_service()
        service.stop_monitoring()
        return jsonify({"message": "Email monitoring stopped"})

    except Exception as e:
        logger.error(f"Error stopping monitoring: {str(e)}")
        return jsonify({"error": "Failed to stop monitoring"}), 500


@main.route("/api/categories", methods=["GET"])
def get_categories():
    """Get available email categories"""
    return jsonify({"categories": ["Customer Support", "Marketing", "Others"]})
