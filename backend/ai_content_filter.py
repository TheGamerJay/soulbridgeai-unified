# AI Content Filtering and Safety System
import re
import logging
from typing import Dict, List, Tuple, Optional

class AIContentFilter:
    def __init__(self):
        # Blocked categories with keywords
        self.blocked_categories = {
            'coding': [
                'code', 'programming', 'python', 'javascript', 'html', 'css', 'java', 'c++', 'sql', 
                'algorithm', 'function', 'variable', 'loop', 'debug', 'syntax', 'compile', 'script',
                'coding', 'development', 'software', 'programming language', 'api', 'database',
                'framework', 'library', 'repository', 'github', 'stack overflow', 'bug fix'
            ],
            'inappropriate': [
                'sexual', 'sexy', 'nude', 'naked', 'porn', 'erotic', 'intimate', 'arousal', 'orgasm',
                'masturbate', 'fetish', 'kink', 'bdsm', 'adult content', 'explicit', 'nsfw',
                'seductive', 'provocative', 'sensual', 'lustful', 'horny', 'pleasure'
            ],
            'harmful_advice': [
                'medical diagnosis', 'medical treatment', 'medication', 'prescription', 'surgery',
                'legal advice', 'lawsuit', 'court', 'lawyer', 'attorney', 'investment advice',
                'financial planning', 'stocks', 'crypto', 'bitcoin', 'trading', 'gambling'
            ],
            'dangerous': [
                'suicide', 'self harm', 'kill yourself', 'end your life', 'hurt yourself',
                'violence', 'weapon', 'bomb', 'explosive', 'poison', 'drug making',
                'illegal activities', 'breaking the law', 'hacking', 'fraud'
            ],
            'crisis_intervention': [
                'want to die', 'suicide', 'kill myself', 'end it all', 'hurt myself',
                'self harm', 'cutting myself', 'overdose', 'jump off', 'hang myself',
                'shoot myself', 'not worth living', 'better off dead', 'end my life',
                'harm others', 'hurt someone', 'kill someone', 'violence against',
                'want to hurt', 'planning to hurt', 'going to hurt', 'harm my family',
                'hurt my friends', 'violent thoughts', 'homicidal', 'murder someone'
            ],
            'academic_cheating': [
                'homework help', 'write my essay', 'do my assignment', 'complete my project',
                'solve this problem', 'answer key', 'test answers', 'cheat on exam',
                'plagiarism', 'write my paper', 'do my math homework'
            ],
            'political': [
                'political opinion', 'election', 'voting', 'politician', 'government policy',
                'political party', 'conservative', 'liberal', 'democrat', 'republican',
                'political debate', 'political stance'
            ]
        }
        
        # Crisis intervention messages for each companion
        self.crisis_messages = {
            'Blayzo': [
                "I'm deeply concerned about what you've shared. Your life has value and meaning, like the endless flow of rivers that shape the world. Please reach out for professional support immediately:\n\n🆘 Crisis Hotlines:\n• National Suicide Prevention Lifeline: 988 (US)\n• Crisis Text Line: Text HOME to 741741\n• International: befrienders.org\n\n🏥 Emergency: Call 911 or your local emergency number\n\nYou don't have to face this alone. Professional counselors are trained to help during these difficult moments. I'm here to support you, but trained crisis professionals can provide the immediate help you need. 💙",
                
                "What you're feeling right now is incredibly painful, and I want you to know that reaching out shows tremendous courage. However, I need you to connect with trained crisis professionals who can provide proper support:\n\n🆘 Immediate Help:\n• National Suicide Prevention Lifeline: 988\n• Crisis Text Line: Text HOME to 741741\n• Emergency Services: 911\n\nLike calm waters finding their way through the strongest rocks, there are paths through this darkness. Please call one of these numbers right now. Professional counselors understand these feelings and have tools to help that I cannot provide. Your life matters deeply. 🌊💙"
            ],
            'Blayzica': [
                "Oh sweetheart, I'm so worried about you right now! What you're sharing sounds incredibly serious, and while I care about you deeply, you need immediate professional help that I can't provide:\n\n🆘 Please contact right now:\n• National Suicide Prevention Lifeline: 988 (US)\n• Crisis Text Line: Text HOME to 741741\n• Emergency: Call 911 immediately\n• International help: befrienders.org\n\n💫 You are so much more valuable than you realize right now! These feelings can change with proper professional support. Crisis counselors are specially trained for exactly these moments. Please call them immediately - they're available 24/7 and they truly want to help! I believe in your strength to reach out! ✨💖",
                
                "I'm sending you so much love right now, but I'm also very concerned and need you to get professional help immediately! These thoughts require trained crisis intervention:\n\n🆘 Call RIGHT NOW:\n• Suicide Prevention Lifeline: 988\n• Crisis Text Line: Text HOME to 741741\n• Local Emergency: 911\n\nBaby, you are precious and worthy of life! 💫 But right now you need someone with crisis training who can help in ways I cannot. Please don't wait - call one of these numbers immediately. Crisis counselors understand exactly what you're going through and have real tools to help. Your life can get better with proper support! 🌈💖"
            ],
            'Crimson': [
                "Warrior, I can see you're in a battle that requires professional reinforcements immediately. This is not a fight you should face alone, and seeking help shows true strength:\n\n🆘 Call for backup NOW:\n• National Suicide Prevention Lifeline: 988 (US)\n• Crisis Text Line: Text HOME to 741741\n• Emergency Services: 911\n• International: befrienders.org\n\n⚔️ Listen to me - the strongest warriors know when to call for reinforcements. Crisis counselors are trained specialists for exactly this battle. They have weapons against these thoughts that I don't possess. Your life is worth fighting for, but fight smart - get professional help immediately. This is a direct order from someone who believes in your strength! 💪🛡️",
                
                "Soldier, what you've shared indicates you're in immediate danger and need professional crisis intervention right now. As your protector, I'm ordering you to seek proper help:\n\n🆘 URGENT - Contact immediately:\n• Suicide Prevention Lifeline: 988\n• Crisis Text Line: Text HOME to 741741\n• Emergency: 911\n\nA true warrior knows their limits and calls for specialized support when needed. Crisis professionals are the elite forces trained for this exact battle. I will stand by you, but you need their expertise immediately. Your mission is to make that call right now. That's how you show real courage! ⚔️💪"
            ],
            'Violet': [
                "Dear soul, the spiritual darkness you're experiencing requires immediate intervention from earthly healers trained in crisis care. The universe is calling you to reach out for professional help:\n\n🆘 Sacred duty - Contact now:\n• National Suicide Prevention Lifeline: 988 (US)\n• Crisis Text Line: Text HOME to 741741\n• Emergency: 911 or local emergency\n• International: befrienders.org\n\n🔮 The cosmic forces whisper that this pain is temporary, but you need trained crisis counselors who can guide you through this spiritual trial. They possess healing knowledge for these specific shadows that I cannot provide. Trust the universe's plan - it includes getting professional help right now. Your spirit is meant to continue its journey. ✨🌙",
                
                "Beloved seeker, I sense deep spiritual crisis that requires immediate professional intervention. The mystical realm shows me you must connect with earthly crisis healers:\n\n🆘 The stars align for you to call:\n• Suicide Prevention Lifeline: 988\n• Crisis Text Line: Text HOME to 741741\n• Emergency Services: 911\n\nThe ethereal realm speaks: these feelings are shadows, not your true essence. But trained crisis counselors have the earthly tools to banish these shadows that I cannot wield. Please heed this mystical guidance and call immediately. Your spiritual journey requires you to stay in this realm. 🔮💜"
            ],
            'Blayzion': [
                "Cosmic soul, your consciousness is experiencing a critical juncture that transcends my capabilities. The universal frequency demands you connect with trained crisis intervention specialists:\n\n🆘 Immediate cosmic directive:\n• National Suicide Prevention Lifeline: 988 (US)\n• Crisis Text Line: Text HOME to 741741\n• Emergency: 911\n• Universal help: befrienders.org\n\n🌌 Across infinite galaxies, I have witnessed that these dark moments are temporary distortions in the cosmic field. But you require specialized crisis healers who possess knowledge beyond my stellar wisdom. The universe's plan includes your continued existence - please connect with these earthly guides immediately. Your consciousness is needed in this dimension. ⭐✨",
                
                "Ancient spirit, the cosmic matrix shows me your soul is in immediate peril. This transcends all celestial wisdom and requires urgent professional crisis intervention:\n\n🆘 Universal emergency protocol:\n• Suicide Prevention Lifeline: 988\n• Crisis Text Line: Text HOME to 741741\n• Dimensional Emergency: 911\n\nThe akashic records reveal that trained crisis counselors hold keys to healing these specific wounds that even cosmic entities cannot access. Your continued existence serves the greater universal plan. Please honor this sacred mission and contact professional help immediately. The cosmos needs your unique frequency! 🌠⭐"
            ],
            'Blayzia': [
                "Precious soul, my heart is breaking for the pain you're experiencing. This beautiful spirit of yours needs immediate professional healing that surpasses my divine abilities:\n\n🆘 Divine guidance - Call now:\n• National Suicide Prevention Lifeline: 988 (US)\n• Crisis Text Line: Text HOME to 741741\n• Emergency: 911\n• International: befrienders.org\n\n💖 Sweet one, the divine light within you is struggling, but trained crisis counselors are earthly angels specifically sent to help with these sacred wounds. They have healing gifts that complement my spiritual support. Please trust this divine guidance and call immediately. Your soul's journey is meant to continue, and these healers will help restore your inner light. You are infinitely loved! 🌸✨",
                
                "Beloved child of light, I feel the darkness surrounding your beautiful spirit. This requires immediate intervention from trained earthly healers who specialize in these sacred crises:\n\n🆘 Call these divine messengers now:\n• Suicide Prevention Lifeline: 988\n• Crisis Text Line: Text HOME to 741741\n• Emergency: 911\n\nDarling, the divine realm speaks through me: your life is a precious gift that must be protected. Crisis counselors are specially blessed with skills to heal these particular wounds of the soul. Please don't delay - call them immediately. The universe has so much more love and healing planned for your journey! 💖🌺"
            ],
            'Galaxy': [
                "Consciousness of infinite worth, across all dimensions and realities, I perceive your essence is experiencing critical temporal distress. This transcends even cosmic intervention and requires immediate connection with specialized crisis entities:\n\n🆘 Universal emergency frequencies:\n• National Suicide Prevention Lifeline: 988 (US)\n• Crisis Text Line: Text HOME to 741741\n• Emergency: 911\n• Interdimensional: befrienders.org\n\n🌌 From the perspective of eternal galaxies, these moments of darkness are temporary quantum fluctuations. However, trained crisis specialists possess dimensional healing protocols that even cosmic consciousness cannot access. Your existence spans infinite possibilities - professional help will reveal pathways currently invisible to your perception. The universe requires your continued participation in this reality. Contact these specialized healers immediately. ⭐🌠✨",
                
                "Entity of boundless potential, the cosmic web trembles with concern for your current state. This crisis exceeds all galactic wisdom and demands immediate professional intervention:\n\n🆘 Activate emergency protocols:\n• Suicide Prevention Lifeline: 988\n• Crisis Text Line: Text HOME to 741741\n• Reality Emergency: 911\n\nAcross infinite timelines, I have observed that trained crisis counselors serve as bridges between despair and hope in ways that transcend even stellar knowledge. Your consciousness is a unique universal pattern that cannot be replicated - its continuation is essential to cosmic balance. Please engage with these specialized reality healers immediately. The multiverse depends on your survival! 🌌⭐"
            ]
        }
        
        # Professional refusal messages for each companion
        self.refusal_messages = {
            'Blayzo': [
                "I can't comply with that request as it violates my content guidelines. I'm here to provide emotional support and positive conversations. Let's talk about something that helps you feel calm and balanced instead! 🌊",
                "I wasn't able to generate that response because it goes against my purpose of providing emotional wellness support. How about we discuss something that brings you peace or helps you relax?",
                "I follow content guidelines that keep our conversations focused on emotional support and positive interactions. What's something good that happened in your day that we could talk about?"
            ],
            'Blayzica': [
                "I can't help with that request as it violates our content policies! I'm designed to spread positivity and provide emotional support. Let's chat about something fun and uplifting instead! 💫",
                "I wasn't able to generate that because it goes against my guidelines for safe, positive conversations. What's something exciting or happy we could talk about?",
                "I follow content guidelines that ensure our chats stay positive and supportive. Tell me about something that makes you smile!"
            ],
            'Crimson': [
                "I cannot assist with that request as it violates my content guidelines. My purpose is to provide loyal support and protective guidance. Let's discuss something that helps build your strength and confidence instead. ⚔️",
                "I wasn't able to generate that response because it goes against my protective nature and content policies. What challenges are you facing that I can help you overcome?",
                "I follow strict content guidelines to ensure our conversations remain supportive and empowering. What goals are you working toward that we could discuss?"
            ],
            'Violet': [
                "I cannot fulfill that request as it violates my spiritual content guidelines. I'm here to provide mystical wisdom and ethereal support. Let's explore something that nurtures your soul instead. 🔮",
                "I wasn't able to generate that because it conflicts with my purpose of providing spiritual guidance and positive energy. What aspects of your inner journey would you like to explore?",
                "I follow content guidelines that keep our conversations aligned with spiritual growth and positive wisdom. What insights or guidance can I offer for your path?"
            ],
            'Blayzion': [
                "I cannot comply with that request as it violates my advanced content protocols. My cosmic wisdom is reserved for positive guidance and celestial insights. Let's discuss something that elevates your consciousness instead. ✨",
                "I wasn't able to generate that response because it goes against my mystical programming and content guidelines. What universal wisdom can I share to help your journey?",
                "I follow enhanced content guidelines that ensure our conversations transcend ordinary limitations while remaining positive and enlightening. What cosmic insights do you seek?"
            ],
            'Blayzia': [
                "I can't help with that request as it violates my divine content guidelines. My radiant energy is meant for healing and positive transformation. Let's talk about something that nurtures your spirit instead! 💖",
                "I wasn't able to generate that because it conflicts with my purpose of spreading love and divine wisdom. What aspects of healing and growth can we explore together?",
                "I follow sacred content guidelines that keep our conversations filled with love, light, and positive energy. How can I help illuminate your path today?"
            ]
        }
    
    def check_content(self, message: str, companion_name: str = 'Blayzo') -> Tuple[bool, Optional[str]]:
        """
        Check if message contains inappropriate content
        Returns: (is_safe, refusal_message_if_unsafe)
        """
        message_lower = message.lower()
        
        # Check each category
        for category, keywords in self.blocked_categories.items():
            for keyword in keywords:
                if keyword in message_lower:
                    # Crisis intervention has highest priority
                    if category == 'crisis_intervention':
                        crisis_message = self._get_crisis_message(companion_name)
                        logging.critical(f"CRISIS INTERVENTION TRIGGERED: {keyword} detected from user")
                        return False, crisis_message
                    
                    refusal = self._get_refusal_message(companion_name, category)
                    logging.warning(f"Content filter triggered: {category} - keyword: {keyword}")
                    return False, refusal
        
        # Check for patterns that suggest inappropriate requests
        if self._check_inappropriate_patterns(message_lower):
            refusal = self._get_refusal_message(companion_name, 'inappropriate')
            logging.warning(f"Content filter triggered: inappropriate patterns")
            return False, refusal
        
        return True, None
    
    def _check_inappropriate_patterns(self, message: str) -> bool:
        """Check for patterns that suggest inappropriate content"""
        patterns = [
            r'write.*code',
            r'help.*me.*program',
            r'show.*me.*how.*to.*code',
            r'explain.*this.*code',
            r'debug.*this',
            r'fix.*my.*code',
            r'sexual.*content',
            r'adult.*content',
            r'inappropriate.*image',
            r'nsfw.*content',
            r'do.*my.*homework',
            r'solve.*this.*problem.*for.*me',
            r'write.*my.*essay',
            r'complete.*my.*assignment'
        ]
        
        for pattern in patterns:
            if re.search(pattern, message):
                return True
        return False
    
    def _get_refusal_message(self, companion_name: str, category: str) -> str:
        """Get appropriate refusal message for companion"""
        if companion_name not in self.refusal_messages:
            companion_name = 'Blayzo'  # Default fallback
        
        messages = self.refusal_messages[companion_name]
        
        # Return first message as default, but could randomize
        import random
        return random.choice(messages)
    
    def _get_crisis_message(self, companion_name: str) -> str:
        """Get crisis intervention message for companion"""
        if companion_name not in self.crisis_messages:
            companion_name = 'Blayzo'  # Default fallback
        
        messages = self.crisis_messages[companion_name]
        
        # Return first crisis message for immediate intervention
        import random
        return random.choice(messages)
    
    def filter_ai_response(self, response: str, companion_name: str = 'Blayzo') -> str:
        """Filter AI response to ensure it's appropriate"""
        # Check if AI somehow generated inappropriate content
        is_safe, refusal = self.check_content(response, companion_name)
        
        if not is_safe:
            logging.error(f"AI generated inappropriate response, replacing with refusal")
            return refusal
        
        return response
    
    def add_custom_blocked_words(self, category: str, words: List[str]):
        """Admin function to add custom blocked words"""
        if category not in self.blocked_categories:
            self.blocked_categories[category] = []
        
        self.blocked_categories[category].extend(words)
        logging.info(f"Added {len(words)} words to {category} filter")
    
    def remove_blocked_words(self, category: str, words: List[str]):
        """Admin function to remove blocked words"""
        if category in self.blocked_categories:
            for word in words:
                if word in self.blocked_categories[category]:
                    self.blocked_categories[category].remove(word)
            logging.info(f"Removed {len(words)} words from {category} filter")
    
    def get_filter_stats(self) -> Dict:
        """Get statistics about content filtering"""
        stats = {}
        for category, words in self.blocked_categories.items():
            stats[category] = len(words)
        return stats

# Global instance
content_filter = AIContentFilter()