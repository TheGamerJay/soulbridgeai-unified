# SoulBridgeAI - Emotional Support Chat Application

## Overview

SoulBridgeAI is a web-based emotional support chat application that provides users with a compassionate AI companion to help them understand and express their feelings. The application uses OpenAI's GPT-4o model to deliver empathetic responses and emotional guidance in a safe, supportive environment.

## System Architecture

### Frontend Architecture
- **Framework**: Pure HTML/CSS/JavaScript with Bootstrap for responsive design
- **UI Theme**: Dark theme using Replit's Bootstrap agent theme
- **Design Pattern**: Single Page Application (SPA) with real-time chat interface
- **Styling**: Custom CSS with Font Awesome icons for enhanced visual appeal

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Session Management**: Flask sessions for maintaining chat history
- **API Integration**: OpenAI API for AI-powered responses
- **Logging**: Python's built-in logging module for debugging and monitoring

### Key Technologies
- Python 3.x
- Flask web framework
- OpenAI API (GPT-4o model)
- Bootstrap 5 with dark theme
- Font Awesome for icons
- HTML5/CSS3/JavaScript ES6+

## Key Components

### Backend Components
1. **Flask Application** (`app.py`):
   - Main application entry point
   - Route handlers for chat interface
   - OpenAI client initialization
   - Session management for chat history

2. **System Prompt Configuration**:
   - Specialized prompt for emotional support AI
   - Guidelines for empathetic responses
   - Safety measures for mental health concerns

3. **Environment Configuration**:
   - OpenAI API key management
   - Session secret key for security
   - Development/production environment handling

### Frontend Components
1. **Chat Interface** (`templates/chat.html`):
   - Responsive chat layout
   - Message display area
   - Input controls and send functionality
   - Welcome message and branding

2. **Styling** (`static/css/style.css`):
   - Custom chat message styling
   - User/AI message differentiation
   - Responsive design elements

3. **JavaScript Logic** (`static/js/chat.js`):
   - Real-time message handling
   - API communication (incomplete in current state)
   - User interaction management

## Data Flow

1. **User Interaction**: User types message in chat interface
2. **Session Storage**: Flask session stores conversation history
3. **API Request**: User message sent to OpenAI API with system prompt
4. **AI Response**: OpenAI returns empathetic response based on system prompt
5. **Display**: Response displayed in chat interface with appropriate styling

## External Dependencies

### Required APIs
- **OpenAI API**: Core AI functionality using GPT-4o model
  - Requires `OPENAI_API_KEY` environment variable
  - Used for generating empathetic responses

### Third-party Libraries
- **Bootstrap 5**: UI framework and responsive design
- **Font Awesome**: Icon library for enhanced visual elements
- **OpenAI Python SDK**: Official client library for API integration

### CDN Dependencies
- Bootstrap CSS (Replit dark theme variant)
- Font Awesome CSS for icons

## Deployment Strategy

### Environment Variables
- `OPENAI_API_KEY`: Required for OpenAI API access
- `SESSION_SECRET`: Flask session encryption key (defaults to development key)

### Deployment Considerations
- Application designed for web deployment
- Session-based architecture requires persistent storage
- API key security must be maintained in production
- HTTPS recommended for secure communication

### Current State
- Basic Flask application structure established
- Frontend template and styling implemented
- OpenAI integration configured but incomplete
- JavaScript chat functionality partially implemented

## Changelog

```
Changelog:
- July 07, 2025. Initial setup
- July 08, 2025. Added Kodular integration API endpoint
```

## User Preferences

```
Preferred communication style: Simple, everyday language.
```

## Notes for Development

### Completed Features
- ✓ Full web chat interface with SoulBridgeAI branding
- ✓ OpenAI API integration with GPT-4o model
- ✓ Session-based conversation history for web interface
- ✓ Mobile-friendly API endpoint for Kodular integration (/api/chat)
- ✓ CORS support for cross-origin requests
- ✓ Comprehensive error handling and user feedback
- ✓ Dark theme with visible message bubbles

### Integration Capabilities  
- ✓ Kodular mobile app integration via REST API
- ✓ Cross-platform compatibility
- ✓ Stateless API calls for mobile applications

### Recommended Next Steps
1. Complete the Flask API endpoint for handling chat messages
2. Finish JavaScript implementation for sending/receiving messages
3. Add proper error handling for API failures
4. Implement message persistence (database integration)
5. Add user authentication if multi-user support is needed
6. Implement safety features for mental health crisis detection

### Security Considerations
- API key protection in production environment
- Session security and CSRF protection
- Input validation and sanitization
- Rate limiting for API calls