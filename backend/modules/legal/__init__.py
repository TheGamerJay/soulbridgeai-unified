# SoulBridge AI - Legal and Compliance Module
from .terms_service import TermsService
from .privacy_manager import PrivacyManager
from .legal_documents import LegalDocuments
from .routes import legal_bp

__all__ = ['TermsService', 'PrivacyManager', 'LegalDocuments', 'legal_bp']