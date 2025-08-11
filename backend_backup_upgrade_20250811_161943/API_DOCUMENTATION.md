# SoulBridge AI - API Documentation

## Overview
This document describes the REST API endpoints for SoulBridge AI user data management.

## Base URL
```
https://your-domain.com/api
```

## Authentication
Currently, the API endpoints are open. In production, consider adding authentication middleware.

---

## User Management

### Create User
**POST** `/users`

Create a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "companion": "Blayzo"  // Optional, defaults to "Blayzo"
}
```

**Response:**
```json
{
  "success": true,
  "user": {
    "userID": "uid12345678",
    "email": "user@example.com",
    "subscriptionStatus": "free",
    "companion": "Blayzo",
    "chatHistory": [],
    "settings": {
      "colorPalette": "cyan",
      "voiceEnabled": true,
      "historySaving": true
    },
    "createdDate": "2025-07-14T15:00:00Z"
  }
}
```

### Get User by ID
**GET** `/users/{userID}`

Retrieve user information by user ID.

**Response:**
```json
{
  "success": true,
  "user": {
    "userID": "uid12345678",
    "email": "user@example.com",
    // ... full user object
  }
}
```

### Get User by Email
**GET** `/users/email/{email}`

Retrieve user information by email address.

**Response:**
```json
{
  "success": true,
  "user": {
    "userID": "uid12345678",
    "email": "user@example.com",
    // ... full user object
  }
}
```

---

## Subscription Management

### Update Subscription
**PUT** `/users/{userID}/subscription`

Update user's subscription status.

**Request Body:**
```json
{
  "subscriptionStatus": "plus"  // "free", "plus", or "galaxy"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Subscription updated successfully"
}
```

---

## Companion Management

### Change Companion
**PUT** `/users/{userID}/companion`

Change user's AI companion.

**Request Body:**
```json
{
  "companion": "Blayzion"  // Valid companions: "Blayzo", "Blayzion", "Crimson", "Blayzica", "Blayzia", "Violet"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Companion updated successfully"
}
```

---

## Chat History

### Add Chat Message
**POST** `/users/{userID}/chat`

Add a new message to user's chat history.

**Request Body:**
```json
{
  "userMessage": "Hello, I feel stressed.",
  "aiResponse": "I'm here for you. What's been on your mind?"
}
```

**Response:**
```json
{
  "success": true,
  "message": {
    "messageID": "msg12345678",
    "timestamp": "2025-07-14T15:00:00Z",
    "userMessage": "Hello, I feel stressed.",
    "aiResponse": "I'm here for you. What's been on your mind?"
  }
}
```

### Get Chat History
**GET** `/users/{userID}/chat?limit=50`

Retrieve user's chat history.

**Query Parameters:**
- `limit` (optional): Maximum number of messages to return (default: 50)

**Response:**
```json
{
  "success": true,
  "chatHistory": [
    {
      "messageID": "msg12345678",
      "timestamp": "2025-07-14T15:00:00Z",
      "userMessage": "Hello, I feel stressed.",
      "aiResponse": "I'm here for you. What's been on your mind?"
    }
    // ... more messages
  ]
}
```

### Clear Chat History
**DELETE** `/users/{userID}/chat`

Clear all chat history for a user.

**Response:**
```json
{
  "success": true,
  "message": "Chat history cleared successfully"
}
```

---

## User Settings

### Get User Settings
**GET** `/users/{userID}/settings`

Retrieve user's settings.

**Response:**
```json
{
  "success": true,
  "settings": {
    "colorPalette": "cyan",
    "voiceEnabled": true,
    "historySaving": true
  }
}
```

### Update User Settings
**PUT** `/users/{userID}/settings`

Update user's settings.

**Request Body:**
```json
{
  "colorPalette": "red",
  "voiceEnabled": false,
  "historySaving": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Settings updated successfully"
}
```

---

## Statistics & Administration

### Get Database Statistics
**GET** `/stats`

Get overall database statistics.

**Response:**
```json
{
  "success": true,
  "stats": {
    "totalUsers": 150,
    "subscriptionCounts": {
      "free": 120,
      "plus": 25,
      "galaxy": 5
    },
    "companionCounts": {
      "Blayzo": 75,
      "Blayzion": 30,
      "Crimson": 20,
      "Blayzica": 15,
      "Blayzia": 8,
      "Violet": 2
    },
    "totalMessages": 5432,
    "lastUpdated": "2025-07-14T15:00:00Z"
  }
}
```

### Create Backup
**POST** `/backup`

Create a backup of the database.

**Response:**
```json
{
  "success": true,
  "backupFile": "soulbridge_backup_20250714_150000.json",
  "message": "Backup created successfully"
}
```

---

## Error Responses

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": "Error description"
}
```

**Common HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (invalid input)
- `404` - Not Found (user/resource not found)
- `500` - Internal Server Error

---

## Data Models

### User Object
```json
{
  "userID": "string",           // Unique user identifier
  "email": "string",            // User's email address
  "subscriptionStatus": "string", // "free", "plus", or "galaxy"
  "companion": "string",        // Active AI companion
  "chatHistory": [],            // Array of chat messages
  "settings": {},               // User preference object
  "createdDate": "string"       // ISO 8601 timestamp
}
```

### Chat Message Object
```json
{
  "messageID": "string",        // Unique message identifier
  "timestamp": "string",        // ISO 8601 timestamp
  "userMessage": "string",      // User's message
  "aiResponse": "string"        // AI's response
}
```

### Settings Object
```json
{
  "colorPalette": "string",     // UI color theme
  "voiceEnabled": "boolean",    // Voice chat enabled
  "historySaving": "boolean"    // Save chat history
}
```

---

## Usage Examples

### JavaScript/Fetch
```javascript
// Create a new user
const response = await fetch('/api/users', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email: 'user@example.com',
    companion: 'Blayzo'
  })
});

const result = await response.json();
console.log(result.user.userID);
```

### Python/Requests
```python
import requests

# Add chat message
response = requests.post('https://your-domain.com/api/users/uid12345/chat', 
  json={
    'userMessage': 'How are you?',
    'aiResponse': 'I am doing well, thank you!'
  }
)

data = response.json()
print(data['message']['messageID'])
```

### cURL
```bash
# Get user by email
curl -X GET "https://your-domain.com/api/users/email/user@example.com"

# Update subscription
curl -X PUT "https://your-domain.com/api/users/uid12345/subscription" \
  -H "Content-Type: application/json" \
  -d '{"subscriptionStatus": "plus"}'
```

---

## Notes

- All timestamps are in ISO 8601 format with UTC timezone
- User IDs are generated automatically and prefixed with "uid"
- Message IDs are generated automatically and prefixed with "msg"
- Email addresses must be unique across all users
- The system automatically sets appropriate color palettes based on selected companions
- Chat history is stored indefinitely unless manually cleared or disabled in settings