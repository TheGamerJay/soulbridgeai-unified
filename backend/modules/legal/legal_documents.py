"""
SoulBridge AI - Legal Documents Manager
Manages legal document templates, versions, and multi-language support
Extracted from backend/app.py with improvements
"""
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import json

logger = logging.getLogger(__name__)

class LegalDocuments:
    """Service for managing legal documents, templates, and content"""
    
    def __init__(self):
        self.supported_languages = ['en', 'es', 'fr', 'de', 'it', 'pt', 'ja', 'zh']
        self.document_versions = {
            'terms_of_service': 'v1.0',
            'privacy_policy': 'v1.0', 
            'cookie_policy': 'v1.0',
            'ai_disclosure': 'v1.0',
            'data_processing': 'v1.0'
        }
        
        # Legal document templates
        self.document_templates = self._initialize_document_templates()
    
    def get_terms_of_service(self, language: str = 'en', version: str = None) -> Dict[str, Any]:
        """Get Terms of Service document"""
        try:
            # Validate language
            if language not in self.supported_languages:
                language = 'en'
            
            # Use current version if not specified
            doc_version = version or self.document_versions['terms_of_service']
            
            template = self.document_templates['terms_of_service'][language]
            
            # Replace template variables
            content = template.copy()
            content['version'] = doc_version
            content['effective_date'] = '2024-01-01'
            content['last_updated'] = datetime.now().strftime('%Y-%m-%d')
            
            return {
                'success': True,
                'document': content,
                'language': language,
                'version': doc_version
            }
            
        except Exception as e:
            logger.error(f"Error getting Terms of Service: {e}")
            return {
                'success': False,
                'error': 'Failed to load Terms of Service'
            }
    
    def get_privacy_policy(self, language: str = 'en', version: str = None) -> Dict[str, Any]:
        """Get Privacy Policy document"""
        try:
            # Validate language
            if language not in self.supported_languages:
                language = 'en'
            
            # Use current version if not specified
            doc_version = version or self.document_versions['privacy_policy']
            
            template = self.document_templates['privacy_policy'][language]
            
            # Replace template variables
            content = template.copy()
            content['version'] = doc_version
            content['effective_date'] = '2024-01-01'
            content['last_updated'] = datetime.now().strftime('%Y-%m-%d')
            
            return {
                'success': True,
                'document': content,
                'language': language,
                'version': doc_version
            }
            
        except Exception as e:
            logger.error(f"Error getting Privacy Policy: {e}")
            return {
                'success': False,
                'error': 'Failed to load Privacy Policy'
            }
    
    def get_combined_legal_document(self, language: str = 'en') -> Dict[str, Any]:
        """Get combined Terms of Service and Privacy Policy for acceptance page"""
        try:
            # Get both documents
            terms_result = self.get_terms_of_service(language)
            privacy_result = self.get_privacy_policy(language)
            
            if not terms_result['success'] or not privacy_result['success']:
                return {
                    'success': False,
                    'error': 'Failed to load legal documents'
                }
            
            # Combine into single document for acceptance
            combined_document = {
                'title': 'Terms of Service & Privacy Policy',
                'language': language,
                'version': terms_result['document']['version'],
                'effective_date': terms_result['document']['effective_date'],
                'last_updated': terms_result['document']['last_updated'],
                'sections': {}
            }
            
            # Add terms sections
            terms_sections = terms_result['document']['sections']
            for section_key, section_data in terms_sections.items():
                combined_document['sections'][f'terms_{section_key}'] = section_data
            
            # Add privacy sections
            privacy_sections = privacy_result['document']['sections']
            for section_key, section_data in privacy_sections.items():
                combined_document['sections'][f'privacy_{section_key}'] = section_data
            
            # Add acceptance requirements
            combined_document['acceptance_requirements'] = [
                {
                    'id': 'ai_understanding',
                    'label': self._get_acceptance_label('ai_understanding', language),
                    'required': True,
                    'description': 'User acknowledges this service uses AI technology'
                },
                {
                    'id': 'terms_privacy',
                    'label': self._get_acceptance_label('terms_privacy', language),
                    'required': True,
                    'description': 'User accepts both Terms of Service and Privacy Policy'
                },
                {
                    'id': 'age_confirmation',
                    'label': self._get_acceptance_label('age_confirmation', language),
                    'required': True,
                    'description': 'User confirms they meet minimum age requirements'
                },
                {
                    'id': 'responsible_use',
                    'label': self._get_acceptance_label('responsible_use', language),
                    'required': True,
                    'description': 'User agrees to use service responsibly and ethically'
                }
            ]
            
            return {
                'success': True,
                'document': combined_document,
                'language': language
            }
            
        except Exception as e:
            logger.error(f"Error getting combined legal document: {e}")
            return {
                'success': False,
                'error': 'Failed to create combined legal document'
            }
    
    def get_ai_disclosure(self, language: str = 'en') -> Dict[str, Any]:
        """Get AI service disclosure document"""
        try:
            if language not in self.supported_languages:
                language = 'en'
            
            # AI-specific disclosures
            ai_disclosure = {
                'title': 'AI Service Disclosure',
                'language': language,
                'version': self.document_versions['ai_disclosure'],
                'sections': {
                    'ai_nature': {
                        'title': 'Nature of AI Services',
                        'content': 'SoulBridge AI uses artificial intelligence to provide personalized wellness guidance, creative writing assistance, and interactive conversations. Our AI companions are powered by large language models.'
                    },
                    'limitations': {
                        'title': 'AI Limitations',
                        'content': 'AI responses may not always be accurate, complete, or appropriate. The AI cannot replace professional medical, mental health, or legal advice.'
                    },
                    'training_data': {
                        'title': 'Training Data',
                        'content': 'Our AI models are trained on diverse text data. They may reflect biases present in training data and should not be considered authoritative on any topic.'
                    },
                    'user_responsibility': {
                        'title': 'User Responsibility',
                        'content': 'Users are responsible for evaluating AI-generated content and should not rely solely on AI responses for important decisions.'
                    },
                    'continuous_learning': {
                        'title': 'Model Updates',
                        'content': 'We continuously improve our AI models. This may result in changes to response styles and capabilities over time.'
                    }
                }
            }
            
            return {
                'success': True,
                'document': ai_disclosure,
                'language': language
            }
            
        except Exception as e:
            logger.error(f"Error getting AI disclosure: {e}")
            return {
                'success': False,
                'error': 'Failed to load AI disclosure'
            }
    
    def get_document_changelog(self) -> Dict[str, Any]:
        """Get changelog of legal document updates"""
        try:
            changelog = {
                'last_updated': datetime.now().strftime('%Y-%m-%d'),
                'current_versions': self.document_versions,
                'changes': [
                    {
                        'date': '2024-01-01',
                        'version': 'v1.0',
                        'documents': ['terms_of_service', 'privacy_policy'],
                        'summary': 'Initial version of Terms of Service and Privacy Policy',
                        'changes': [
                            'Established basic terms of service',
                            'Defined privacy practices and data handling',
                            'Added AI service disclosures',
                            'Set user responsibilities and age requirements'
                        ]
                    }
                ],
                'supported_languages': self.supported_languages
            }
            
            return {
                'success': True,
                'changelog': changelog
            }
            
        except Exception as e:
            logger.error(f"Error getting document changelog: {e}")
            return {
                'success': False,
                'error': 'Failed to load changelog'
            }
    
    def validate_document_acceptance(self, acceptances: Dict[str, bool]) -> Dict[str, Any]:
        """Validate that all required legal acceptances are provided"""
        try:
            required_acceptances = [
                'ai_understanding',
                'terms_privacy',
                'age_confirmation', 
                'responsible_use'
            ]
            
            missing_acceptances = []
            
            for requirement in required_acceptances:
                if not acceptances.get(requirement, False):
                    missing_acceptances.append(requirement)
            
            if missing_acceptances:
                return {
                    'valid': False,
                    'missing': missing_acceptances,
                    'message': f'Missing required acceptances: {", ".join(missing_acceptances)}'
                }
            
            return {
                'valid': True,
                'message': 'All required acceptances provided'
            }
            
        except Exception as e:
            logger.error(f"Error validating document acceptance: {e}")
            return {
                'valid': False,
                'error': 'Failed to validate acceptances'
            }
    
    def _initialize_document_templates(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Initialize legal document templates"""
        return {
            'terms_of_service': {
                'en': {
                    'title': 'Terms of Service',
                    'sections': {
                        'acceptance': {
                            'title': 'Acceptance of Terms',
                            'content': 'By accessing and using SoulBridge AI ("the Service"), you accept and agree to be bound by the terms and provision of this agreement. Please read these Terms of Service carefully before using our service.'
                        },
                        'description': {
                            'title': 'Description of Service',
                            'content': 'SoulBridge AI is an artificial intelligence-powered platform that provides wellness guidance, creative writing assistance, personal growth tools, and interactive AI companions. Our service is designed to support your journey of self-discovery and wellbeing.'
                        },
                        'user_accounts': {
                            'title': 'User Accounts',
                            'content': 'To access certain features, you must create an account. You are responsible for maintaining the confidentiality of your account information and for all activities that occur under your account.'
                        },
                        'acceptable_use': {
                            'title': 'Acceptable Use',
                            'content': 'You agree to use the Service only for lawful purposes and in accordance with these Terms. You must not use the Service in any way that could damage, disable, or impair the Service.'
                        },
                        'ai_limitations': {
                            'title': 'AI Service Limitations',
                            'content': 'Our AI services are provided "as is" and may not always be accurate or appropriate. AI responses should not be considered professional advice. You acknowledge that AI technology has inherent limitations.'
                        },
                        'subscription': {
                            'title': 'Subscription Terms',
                            'content': 'Paid subscriptions are billed in advance and are non-refundable. You may cancel your subscription at any time, but you will continue to have access until the end of your billing period.'
                        },
                        'intellectual_property': {
                            'title': 'Intellectual Property',
                            'content': 'The Service and its original content, features, and functionality are and will remain the exclusive property of SoulBridge AI and its licensors.'
                        },
                        'privacy': {
                            'title': 'Privacy',
                            'content': 'Your privacy is important to us. Please review our Privacy Policy, which also governs your use of the Service.'
                        },
                        'termination': {
                            'title': 'Termination',
                            'content': 'We may terminate or suspend your account and bar access to the Service immediately, without prior notice, for any reason whatsoever, including breach of the Terms.'
                        },
                        'limitation_of_liability': {
                            'title': 'Limitation of Liability',
                            'content': 'In no event shall SoulBridge AI be liable for any indirect, incidental, special, consequential, or punitive damages resulting from your use of the Service.'
                        },
                        'changes': {
                            'title': 'Changes to Terms',
                            'content': 'We reserve the right to modify these Terms at any time. We will notify users of any material changes to these Terms.'
                        }
                    }
                }
            },
            'privacy_policy': {
                'en': {
                    'title': 'Privacy Policy',
                    'sections': {
                        'introduction': {
                            'title': 'Introduction',
                            'content': 'SoulBridge AI ("we," "our," or "us") respects your privacy and is committed to protecting your personal data. This Privacy Policy describes how we collect, use, and safeguard your information.'
                        },
                        'data_collection': {
                            'title': 'Information We Collect',
                            'content': 'We collect information you provide directly to us (account information, communications with AI), information automatically collected (usage data, device information), and information from third parties (payment processors).'
                        },
                        'data_use': {
                            'title': 'How We Use Your Information',
                            'content': 'We use your information to provide and improve our services, personalize your experience, communicate with you, ensure security, and comply with legal obligations.'
                        },
                        'data_sharing': {
                            'title': 'Information Sharing',
                            'content': 'We do not sell your personal information. We may share your information with service providers, for legal compliance, or with your explicit consent.'
                        },
                        'data_security': {
                            'title': 'Data Security',
                            'content': 'We implement appropriate technical and organizational measures to protect your personal information against unauthorized access, alteration, disclosure, or destruction.'
                        },
                        'ai_interactions': {
                            'title': 'AI Interactions',
                            'content': 'Your conversations with AI companions are processed to provide personalized responses. We do not use your personal conversations for training our AI models without explicit consent.'
                        },
                        'data_retention': {
                            'title': 'Data Retention',
                            'content': 'We retain your personal information for as long as necessary to provide services, comply with legal obligations, and resolve disputes. You can request data deletion at any time.'
                        },
                        'your_rights': {
                            'title': 'Your Privacy Rights',
                            'content': 'You have the right to access, correct, delete, or port your personal information. You can also object to processing or withdraw consent. Contact us to exercise these rights.'
                        },
                        'cookies': {
                            'title': 'Cookies and Tracking',
                            'content': 'We use cookies and similar technologies to enhance your experience, remember your preferences, and analyze usage patterns. You can control cookies through your browser settings.'
                        },
                        'children_privacy': {
                            'title': 'Children\'s Privacy',
                            'content': 'Our service is not intended for children under 13. We do not knowingly collect personal information from children under 13. If you believe we have collected such information, please contact us.'
                        },
                        'international_transfers': {
                            'title': 'International Data Transfers',
                            'content': 'Your information may be transferred to and processed in countries other than your own. We ensure appropriate safeguards are in place for such transfers.'
                        },
                        'updates': {
                            'title': 'Updates to This Policy',
                            'content': 'We may update this Privacy Policy from time to time. We will notify you of any material changes by posting the new policy and updating the "Last Updated" date.'
                        },
                        'contact': {
                            'title': 'Contact Information',
                            'content': 'If you have any questions about this Privacy Policy or our privacy practices, please contact us at privacy@soulbridgeai.com.'
                        }
                    }
                }
            }
        }
    
    def _get_acceptance_label(self, acceptance_id: str, language: str) -> str:
        """Get localized acceptance label"""
        labels = {
            'en': {
                'ai_understanding': 'I understand this service uses AI technology',
                'terms_privacy': 'I accept the Terms of Service and Privacy Policy',
                'age_confirmation': 'I confirm I am at least 13 years old',
                'responsible_use': 'I agree to use this service responsibly'
            }
            # Add more languages as needed
        }
        
        return labels.get(language, labels['en']).get(acceptance_id, acceptance_id)