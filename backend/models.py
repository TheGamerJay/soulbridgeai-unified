"""
Database models for SoulBridge AI user data management
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Union
import uuid

# SQLAlchemy imports for new PostgreSQL models
from sqlalchemy import Column, Integer, String, DateTime, func
from .db import Base


# New PostgreSQL User model using SQLAlchemy (updated to match existing schema)
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    user_plan = Column(String, nullable=False, default="free")  # Match existing schema
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DatabaseManager:
    def __init__(self, db_file: str = "soulbridge_data.json"):
        self.db_file = db_file
        self.data = self._load_data()

    def _load_data(self) -> Dict:
        """Load data from JSON file or create empty structure"""
        print(f"🔍 Loading database from: {self.db_file}")
        print(f"📁 Database file exists: {os.path.exists(self.db_file)}")

        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                print(
                    f"✅ Database loaded successfully. Users: {len(data.get('users', []))}"
                )
                return data
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"❌ Database file corrupted: {e}")
        else:
            print("📝 Creating new database structure")

        # Default structure
        default_data = {
            "users": [],
            "support_tickets": [],
            "invoices": [],
            "knowledge_base": [],
            "chat_sessions": [],
            "metadata": {
                "version": "1.0",
                "created": datetime.utcnow().isoformat() + "Z",
                "lastUpdated": datetime.utcnow().isoformat() + "Z",
            },
        }

        # Save the default structure immediately
        try:
            with open(self.db_file, "w", encoding="utf-8") as f:
                json.dump(default_data, f, indent=2, ensure_ascii=False)
            print(f"💾 New database file created at: {self.db_file}")
        except Exception as e:
            print(f"❌ Failed to create database file: {e}")

        return default_data

    def _save_data(self):
        """Save data to JSON file"""
        self.data["metadata"]["lastUpdated"] = datetime.utcnow().isoformat() + "Z"

        try:
            # Create directory if it doesn't exist
            os.makedirs(
                os.path.dirname(self.db_file) if os.path.dirname(self.db_file) else ".",
                exist_ok=True,
            )

            # Write to temp file first, then move to prevent corruption
            temp_file = self.db_file + ".tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)

            # Move temp file to actual file (atomic operation)
            if os.path.exists(temp_file):
                if os.path.exists(self.db_file):
                    os.remove(self.db_file)
                os.rename(temp_file, self.db_file)

            print(f"💾 Database saved successfully to {self.db_file}")
            print(f"📊 Total users in database: {len(self.data.get('users', []))}")

        except Exception as e:
            print(f"❌ Failed to save database: {e}")
            # Try to clean up temp file
            temp_file = self.db_file + ".tmp"
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass


class User:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create_user(self, email: str, companion: str = "Blayzo") -> Dict:
        """Create a new user"""
        user_id = f"uid{uuid.uuid4().hex[:8]}"

        # Check if user already exists
        if self.get_user_by_email(email):
            raise ValueError("User with this email already exists")

        new_user = {
            "userID": user_id,
            "email": email,
            "subscriptionStatus": "free",
            "companion": companion,
            "chatHistory": [],
            "settings": {
                "colorPalette": self._get_companion_color(companion),
                "voiceEnabled": True,
                "historySaving": True,
            },
            "createdDate": datetime.utcnow().isoformat() + "Z",
        }

        self.db.data["users"].append(new_user)
        self.db._save_data()

        return new_user

    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by userID"""
        for user in self.db.data["users"]:
            if user["userID"] == user_id:
                return user
        return None

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email (case-insensitive)"""
        for user in self.db.data["users"]:
            if user["email"].lower() == email.lower():
                return user
        return None

    def update_user(self, user_id: str, updates: Dict) -> bool:
        """Update user data"""
        for i, user in enumerate(self.db.data["users"]):
            if user["userID"] == user_id:
                # Merge updates
                for key, value in updates.items():
                    user[key] = value  # Allow adding new keys like 'password'

                self.db._save_data()
                return True
        return False

    def delete_user(self, user_id: str) -> bool:
        """Delete user"""
        for i, user in enumerate(self.db.data["users"]):
            if user["userID"] == user_id:
                del self.db.data["users"][i]
                self.db._save_data()
                return True
        return False

    def update_subscription(self, user_id: str, subscription_status: str) -> bool:
        """Update user subscription status"""
        valid_statuses = ["free", "plus", "galaxy"]
        if subscription_status not in valid_statuses:
            raise ValueError(
                f"Invalid subscription status. Must be one of: {valid_statuses}"
            )

        return self.update_user(user_id, {"subscriptionStatus": subscription_status})

    def change_companion(self, user_id: str, companion: str) -> bool:
        """Change user's companion"""
        valid_companions = [
            "Blayzo",
            "Blayzion",
            "Crimson",
            "Blayzica",
            "Blayzia",
            "Violet",
        ]
        if companion not in valid_companions:
            raise ValueError(f"Invalid companion. Must be one of: {valid_companions}")

        # Update companion and color palette
        updates = {"companion": companion, "settings": {}}

        user = self.get_user_by_id(user_id)
        if user:
            updates["settings"] = user["settings"].copy()
            updates["settings"]["colorPalette"] = self._get_companion_color(companion)

        return self.update_user(user_id, updates)

    def _get_companion_color(self, companion: str) -> str:
        """Get default color palette for companion"""
        companion_colors = {
            "Blayzo": "cyan",
            "Blayzion": "galaxy",
            "Crimson": "blood-orange",
            "Blayzica": "red",
            "Blayzia": "galaxy",
            "Violet": "violet",
        }
        return companion_colors.get(companion, "cyan")


class ChatHistory:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def add_message(self, user_id: str, user_message: str, ai_response: str) -> Dict:
        """Add a new chat message"""
        message_id = f"msg{uuid.uuid4().hex[:8]}"
        timestamp = datetime.utcnow().isoformat() + "Z"

        new_message = {
            "messageID": message_id,
            "timestamp": timestamp,
            "userMessage": user_message,
            "aiResponse": ai_response,
        }

        # Find user and add message
        for user in self.db.data["users"]:
            if user["userID"] == user_id:
                user["chatHistory"].append(new_message)
                self.db._save_data()
                return new_message

        raise ValueError("User not found")

    def get_chat_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get user's chat history"""
        user = None
        for u in self.db.data["users"]:
            if u["userID"] == user_id:
                user = u
                break

        if not user:
            return []

        # Return most recent messages first
        history = user["chatHistory"]
        return history[-limit:] if limit else history

    def clear_chat_history(self, user_id: str) -> bool:
        """Clear user's chat history"""
        for user in self.db.data["users"]:
            if user["userID"] == user_id:
                user["chatHistory"] = []
                self.db._save_data()
                return True
        return False

    def delete_message(self, user_id: str, message_id: str) -> bool:
        """Delete a specific message"""
        for user in self.db.data["users"]:
            if user["userID"] == user_id:
                for i, message in enumerate(user["chatHistory"]):
                    if message["messageID"] == message_id:
                        del user["chatHistory"][i]
                        self.db._save_data()
                        return True
        return False


class UserSettings:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def update_settings(self, user_id: str, settings: Dict) -> bool:
        """Update user settings"""
        for user in self.db.data["users"]:
            if user["userID"] == user_id:
                # Merge with existing settings
                if "settings" not in user:
                    user["settings"] = {}

                for key, value in settings.items():
                    user["settings"][key] = value

                self.db._save_data()
                return True
        return False

    def get_settings(self, user_id: str) -> Dict:
        """Get user settings"""
        for user in self.db.data["users"]:
            if user["userID"] == user_id:
                return user.get("settings", {})
        return {}

    def update_color_palette(self, user_id: str, color_palette: str) -> bool:
        """Update user's color palette"""
        return self.update_settings(user_id, {"colorPalette": color_palette})

    def toggle_voice(self, user_id: str) -> bool:
        """Toggle voice enabled setting"""
        settings = self.get_settings(user_id)
        current_voice = settings.get("voiceEnabled", True)
        return self.update_settings(user_id, {"voiceEnabled": not current_voice})

    def toggle_history_saving(self, user_id: str) -> bool:
        """Toggle history saving setting"""
        settings = self.get_settings(user_id)
        current_saving = settings.get("historySaving", True)
        return self.update_settings(user_id, {"historySaving": not current_saving})


class SupportTicket:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create_ticket(
        self,
        user_email: str,
        subject: str,
        description: str,
        priority: str = "medium",
        category: str = "general",
    ) -> Dict:
        """Create a new support ticket"""
        ticket_id = f"ticket_{uuid.uuid4().hex[:8]}"

        ticket = {
            "ticketID": ticket_id,
            "userEmail": user_email,
            "subject": subject,
            "description": description,
            "priority": priority,  # low, medium, high, urgent
            "category": category,  # general, billing, technical, bug_report, feature_request
            "status": "open",  # open, in_progress, pending, resolved, closed
            "assignedTo": None,  # Admin/support agent assigned
            "createdAt": datetime.utcnow().isoformat() + "Z",
            "updatedAt": datetime.utcnow().isoformat() + "Z",
            "responses": [],  # List of responses from support team
        }

        self.db.data["support_tickets"].append(ticket)
        self.db._save_data()

        return ticket

    def get_ticket(self, ticket_id: str) -> Optional[Dict]:
        """Get a specific support ticket"""
        for ticket in self.db.data["support_tickets"]:
            if ticket["ticketID"] == ticket_id:
                return ticket
        return None

    def get_user_tickets(self, user_email: str) -> List[Dict]:
        """Get all tickets for a specific user"""
        return [
            ticket
            for ticket in self.db.data["support_tickets"]
            if ticket["userEmail"] == user_email
        ]

    def get_all_tickets(self, status: str = None, priority: str = None) -> List[Dict]:
        """Get all tickets, optionally filtered by status or priority"""
        tickets = self.db.data["support_tickets"]

        if status:
            tickets = [t for t in tickets if t["status"] == status]

        if priority:
            tickets = [t for t in tickets if t["priority"] == priority]

        # Sort by creation date (newest first)
        tickets.sort(key=lambda x: x["createdAt"], reverse=True)
        return tickets

    def update_ticket_status(
        self, ticket_id: str, status: str, assigned_to: str = None
    ) -> bool:
        """Update ticket status and optionally assign to someone"""
        for ticket in self.db.data["support_tickets"]:
            if ticket["ticketID"] == ticket_id:
                ticket["status"] = status
                ticket["updatedAt"] = datetime.utcnow().isoformat() + "Z"

                if assigned_to:
                    ticket["assignedTo"] = assigned_to

                self.db._save_data()
                return True
        return False

    def add_response(
        self,
        ticket_id: str,
        response_text: str,
        responder_email: str,
        is_internal: bool = False,
    ) -> bool:
        """Add a response to a support ticket"""
        for ticket in self.db.data["support_tickets"]:
            if ticket["ticketID"] == ticket_id:
                response = {
                    "responseID": f"resp_{uuid.uuid4().hex[:8]}",
                    "text": response_text,
                    "responderEmail": responder_email,
                    "isInternal": is_internal,  # Internal notes vs public responses
                    "createdAt": datetime.utcnow().isoformat() + "Z",
                }

                ticket["responses"].append(response)
                ticket["updatedAt"] = datetime.utcnow().isoformat() + "Z"

                # Auto-update status if it was resolved
                if not is_internal and ticket["status"] == "open":
                    ticket["status"] = "in_progress"

                self.db._save_data()
                return True
        return False

    def search_tickets(self, query: str) -> List[Dict]:
        """Search tickets by subject, description, or user email"""
        query_lower = query.lower()
        results = []

        for ticket in self.db.data["support_tickets"]:
            if (
                query_lower in ticket["subject"].lower()
                or query_lower in ticket["description"].lower()
                or query_lower in ticket["userEmail"].lower()
            ):
                results.append(ticket)

        return results

    def get_ticket_stats(self) -> Dict:
        """Get support ticket statistics"""
        tickets = self.db.data["support_tickets"]
        total_tickets = len(tickets)

        status_counts = {
            "open": 0,
            "in_progress": 0,
            "pending": 0,
            "resolved": 0,
            "closed": 0,
        }
        priority_counts = {"low": 0, "medium": 0, "high": 0, "urgent": 0}
        category_counts = {}

        for ticket in tickets:
            status_counts[ticket["status"]] += 1
            priority_counts[ticket["priority"]] += 1
            category = ticket.get("category", "general")
            category_counts[category] = category_counts.get(category, 0) + 1

        return {
            "totalTickets": total_tickets,
            "statusCounts": status_counts,
            "priorityCounts": priority_counts,
            "categoryCounts": category_counts,
        }


class BillingManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create_invoice(
        self,
        user_email: str,
        amount: float,
        plan_type: str,
        stripe_invoice_id: str = None,
        stripe_customer_id: str = None,
    ) -> Dict:
        """Create a new invoice record"""
        invoice_id = f"inv_{uuid.uuid4().hex[:8]}"

        invoice = {
            "invoiceID": invoice_id,
            "userEmail": user_email,
            "amount": amount,
            "planType": plan_type,  # monthly, yearly
            "status": "pending",  # pending, paid, failed, refunded
            "stripeInvoiceID": stripe_invoice_id,
            "stripeCustomerID": stripe_customer_id,
            "createdAt": datetime.utcnow().isoformat() + "Z",
            "paidAt": None,
            "dueDate": datetime.utcnow().isoformat() + "Z",
            "currency": "usd",
            "taxAmount": 0.0,
            "subtotal": amount,
            "total": amount,
        }

        self.db.data["invoices"].append(invoice)
        self.db._save_data()

        return invoice

    def update_invoice_status(
        self, invoice_id: str, status: str, paid_at: str = None
    ) -> bool:
        """Update invoice payment status"""
        for invoice in self.db.data["invoices"]:
            if invoice["invoiceID"] == invoice_id:
                invoice["status"] = status
                if paid_at:
                    invoice["paidAt"] = paid_at
                self.db._save_data()
                return True
        return False

    def get_user_invoices(self, user_email: str) -> List[Dict]:
        """Get all invoices for a user"""
        return [
            inv for inv in self.db.data["invoices"] if inv["userEmail"] == user_email
        ]

    def get_invoice_stats(self) -> Dict:
        """Get billing statistics"""
        invoices = self.db.data["invoices"]
        total_revenue = sum(
            inv["amount"] for inv in invoices if inv["status"] == "paid"
        )
        monthly_revenue = sum(
            inv["amount"]
            for inv in invoices
            if inv["status"] == "paid" and inv["planType"] == "monthly"
        )
        yearly_revenue = sum(
            inv["amount"]
            for inv in invoices
            if inv["status"] == "paid" and inv["planType"] == "yearly"
        )

        return {
            "totalInvoices": len(invoices),
            "totalRevenue": total_revenue,
            "monthlyRevenue": monthly_revenue,
            "yearlyRevenue": yearly_revenue,
            "pendingInvoices": len(
                [inv for inv in invoices if inv["status"] == "pending"]
            ),
        }


class LiveChatSession:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create_chat_session(self, user_email: str, agent_email: str = None) -> Dict:
        """Create a new live chat session"""
        session_id = f"chat_{uuid.uuid4().hex[:8]}"

        session = {
            "sessionID": session_id,
            "userEmail": user_email,
            "agentEmail": agent_email,
            "status": "active",  # active, closed, waiting
            "startTime": datetime.utcnow().isoformat() + "Z",
            "endTime": None,
            "messages": [],
            "rating": None,
            "feedback": None,
        }

        self.db.data["chat_sessions"].append(session)
        self.db._save_data()

        return session

    def add_message(
        self,
        session_id: str,
        sender_email: str,
        message: str,
        sender_type: str = "user",
    ) -> bool:
        """Add a message to a chat session"""
        for session in self.db.data["chat_sessions"]:
            if session["sessionID"] == session_id:
                message_obj = {
                    "messageID": f"msg_{uuid.uuid4().hex[:8]}",
                    "senderEmail": sender_email,
                    "senderType": sender_type,  # user, agent
                    "message": message,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                }
                session["messages"].append(message_obj)
                self.db._save_data()
                return True
        return False

    def close_session(
        self, session_id: str, rating: int = None, feedback: str = None
    ) -> bool:
        """Close a chat session"""
        for session in self.db.data["chat_sessions"]:
            if session["sessionID"] == session_id:
                session["status"] = "closed"
                session["endTime"] = datetime.utcnow().isoformat() + "Z"
                if rating:
                    session["rating"] = rating
                if feedback:
                    session["feedback"] = feedback
                self.db._save_data()
                return True
        return False

    def get_active_sessions(self) -> List[Dict]:
        """Get all active chat sessions"""
        return [
            session
            for session in self.db.data["chat_sessions"]
            if session["status"] == "active"
        ]


class KnowledgeBase:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create_article(
        self,
        title: str,
        content: str,
        category: str,
        author_email: str,
        tags: List[str] = None,
    ) -> Dict:
        """Create a new knowledge base article"""
        article_id = f"kb_{uuid.uuid4().hex[:8]}"

        article = {
            "articleID": article_id,
            "title": title,
            "content": content,
            "category": category,  # getting_started, troubleshooting, billing, features
            "authorEmail": author_email,
            "tags": tags or [],
            "status": "published",  # draft, published, archived
            "views": 0,
            "helpful_votes": 0,
            "unhelpful_votes": 0,
            "createdAt": datetime.utcnow().isoformat() + "Z",
            "updatedAt": datetime.utcnow().isoformat() + "Z",
        }

        self.db.data["knowledge_base"].append(article)
        self.db._save_data()

        return article

    def search_articles(self, query: str, category: str = None) -> List[Dict]:
        """Search knowledge base articles"""
        query_lower = query.lower()
        results = []

        for article in self.db.data["knowledge_base"]:
            if article["status"] != "published":
                continue

            if category and article["category"] != category:
                continue

            if (
                query_lower in article["title"].lower()
                or query_lower in article["content"].lower()
                or any(query_lower in tag.lower() for tag in article["tags"])
            ):
                results.append(article)

        return sorted(results, key=lambda x: x["views"], reverse=True)

    def vote_article(self, article_id: str, helpful: bool) -> bool:
        """Vote on article helpfulness"""
        for article in self.db.data["knowledge_base"]:
            if article["articleID"] == article_id:
                if helpful:
                    article["helpful_votes"] += 1
                else:
                    article["unhelpful_votes"] += 1
                self.db._save_data()
                return True
        return False

    def increment_views(self, article_id: str) -> bool:
        """Increment article view count"""
        for article in self.db.data["knowledge_base"]:
            if article["articleID"] == article_id:
                article["views"] += 1
                self.db._save_data()
                return True
        return False


class DiagnosticTools:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def run_user_diagnostics(self, user_email: str) -> Dict:
        """Run comprehensive diagnostics for a user"""
        # Find user
        user = None
        for u in self.db.data["users"]:
            if u["email"] == user_email:
                user = u
                break

        if not user:
            return {"error": "User not found"}

        # Diagnostic checks
        diagnostics = {
            "userID": user["userID"],
            "email": user_email,
            "subscriptionStatus": user.get("subscriptionStatus", "free"),
            "companion": user.get("companion", "Blayzo"),
            "chatHistoryCount": len(user.get("chatHistory", [])),
            "lastActivity": user.get("lastActivity", "Never"),
            "accountCreated": user.get("createdAt", "Unknown"),
            "issues": [],
            "recommendations": [],
            "systemHealth": "healthy",
        }

        # Check for common issues
        if len(user.get("chatHistory", [])) == 0:
            diagnostics["issues"].append("No chat history found")
            diagnostics["recommendations"].append(
                "Try starting a conversation with your AI companion"
            )

        if user.get("subscriptionStatus") == "free":
            diagnostics["recommendations"].append(
                "Consider upgrading to SoulBridge AI Plus for unlimited features"
            )

        # Check for stale accounts
        if user.get("lastActivity") == "Never":
            diagnostics["issues"].append("Account appears inactive")
            diagnostics["recommendations"].append(
                "Log in and start chatting to activate your account"
            )

        # Overall health assessment
        if len(diagnostics["issues"]) > 2:
            diagnostics["systemHealth"] = "needs_attention"
        elif len(diagnostics["issues"]) > 0:
            diagnostics["systemHealth"] = "minor_issues"

        return diagnostics

    def get_system_health(self) -> Dict:
        """Get overall system health metrics"""
        users = self.db.data["users"]
        tickets = self.db.data["support_tickets"]

        # Calculate metrics
        total_users = len(users)
        active_users = len([u for u in users if len(u.get("chatHistory", [])) > 0])
        premium_users = len([u for u in users if u.get("subscriptionStatus") != "free"])

        open_tickets = len([t for t in tickets if t["status"] == "open"])
        urgent_tickets = len([t for t in tickets if t["priority"] == "urgent"])

        # Health assessment
        health_score = 100
        if open_tickets > 10:
            health_score -= 20
        if urgent_tickets > 0:
            health_score -= 30
        if active_users < total_users * 0.5:
            health_score -= 25

        return {
            "healthScore": max(0, health_score),
            "totalUsers": total_users,
            "activeUsers": active_users,
            "premiumUsers": premium_users,
            "openTickets": open_tickets,
            "urgentTickets": urgent_tickets,
            "systemStatus": (
                "healthy"
                if health_score >= 80
                else "degraded" if health_score >= 60 else "critical"
            ),
        }


class SoulBridgeDB:
    """Main database interface for SoulBridge AI"""

    def __init__(self, db_file: str = "soulbridge_data.json"):
        self.db_manager = DatabaseManager(db_file)
        self.users = User(self.db_manager)
        self.chat_history = ChatHistory(self.db_manager)
        self.settings = UserSettings(self.db_manager)
        self.support_tickets = SupportTicket(self.db_manager)
        self.billing = BillingManager(self.db_manager)
        self.live_chat = LiveChatSession(self.db_manager)
        self.knowledge_base = KnowledgeBase(self.db_manager)
        self.diagnostics = DiagnosticTools(self.db_manager)

    def get_user_stats(self) -> Dict:
        """Get database statistics"""
        total_users = len(self.db_manager.data["users"])
        subscription_counts = {"free": 0, "plus": 0, "galaxy": 0}
        companion_counts = {}
        total_messages = 0

        for user in self.db_manager.data["users"]:
            # Count subscriptions
            sub_status = user.get("subscriptionStatus", "free")
            subscription_counts[sub_status] += 1

            # Count companions
            companion = user.get("companion", "Blayzo")
            companion_counts[companion] = companion_counts.get(companion, 0) + 1

            # Count messages
            total_messages += len(user.get("chatHistory", []))

        return {
            "totalUsers": total_users,
            "subscriptionCounts": subscription_counts,
            "companionCounts": companion_counts,
            "totalMessages": total_messages,
            "lastUpdated": self.db_manager.data["metadata"]["lastUpdated"],
        }

    def backup_data(self, backup_file: str = None) -> str:
        """Create a backup of the database"""
        if not backup_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"soulbridge_backup_{timestamp}.json"

        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(self.db_manager.data, f, indent=2, ensure_ascii=False)

        return backup_file


# Example usage and testing
if __name__ == "__main__":
    # Initialize database
    db = SoulBridgeDB("test_soulbridge.json")

    # Create a test user
    try:
        user = db.users.create_user("test@example.com", "Blayzo")
        print(f"Created user: {user['userID']}")

        # Add some chat history
        message = db.chat_history.add_message(
            user["userID"],
            "Hello, I feel stressed.",
            "I'm here for you. What's been on your mind?",
        )
        print(f"Added message: {message['messageID']}")

        # Update settings
        db.settings.update_settings(user["userID"], {"colorPalette": "red"})

        # Get stats
        stats = db.get_user_stats()
        print(f"Database stats: {stats}")

    except ValueError as e:
        print(f"Error: {e}")
