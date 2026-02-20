# Product Requirements Document (PRD)
## LegalAI - Professional Legal Assistant

**Version:** 1.0  
**Date:** February 19, 2026  
**Document Owner:** Product Team  
**Status:** Active Development

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Product Overview](#product-overview)
3. [Business Objectives](#business-objectives)
4. [Target Users](#target-users)
5. [User Stories](#user-stories)
6. [Functional Requirements](#functional-requirements)
7. [Non-Functional Requirements](#non-functional-requirements)
8. [Technical Architecture](#technical-architecture)
9. [System Features](#system-features)
10. [User Interface Requirements](#user-interface-requirements)
11. [API Specifications](#api-specifications)
12. [Data Management](#data-management)
13. [Security & Compliance](#security--compliance)
14. [Dependencies & Integrations](#dependencies--integrations)
15. [Success Metrics](#success-metrics)
16. [Constraints & Assumptions](#constraints--assumptions)
17. [Future Enhancements](#future-enhancements)
18. [Glossary](#glossary)

---

## Executive Summary

**LegalAI** is a sophisticated, AI-powered legal consultation chatbot designed to provide professional-grade legal assistance to individuals, law students, and legal professionals. The application combines advanced natural language processing with comprehensive legal research capabilities to deliver contextual, accurate, and well-structured legal guidance.

### Key Value Propositions
- **24/7 Availability**: Instant access to legal information and analysis
- **Comprehensive Research**: Integration with authoritative legal databases and web resources
- **Memory & Context**: Maintains conversation history for coherent, multi-turn consultations
- **Professional Interface**: ChatGPT-like user experience optimized for legal workflows
- **Session Management**: Organize and retrieve multiple legal consultations efficiently

---

## Product Overview

### Vision
To democratize access to legal knowledge by providing an intelligent, accessible, and reliable AI-powered legal assistant that bridges the gap between complex legal information and user understanding.

### Mission
Deliver accurate, contextual, and comprehensive legal guidance through an intuitive interface that combines cutting-edge AI technology with established legal research methodologies.

### Product Type
Web-based SaaS application (Flask-powered web app) with persistent data storage and AI agent integration.

### Core Technology Stack
- **Backend**: Python 3.8+, Flask, SQLite
- **AI Framework**: Agno Agent, Groq (Llama 3.3 70B Versatile)
- **Frontend**: HTML5, CSS3, JavaScript (jQuery), Marked.js, DOMPurify
- **Tools**: DuckDuckGo Search API, Custom LawBhoomi Scraper, BeautifulSoup4
- **Infrastructure**: Local/Cloud deployment, RESTful API architecture

---

## Business Objectives

### Primary Objectives
1. **Improve Legal Access**: Reduce barriers to legal information for underserved populations
2. **Enhance Efficiency**: Accelerate legal research and preliminary analysis for professionals
3. **Educational Support**: Provide comprehensive learning resources for law students
4. **User Engagement**: Achieve 80% user retention through quality responses and UX

### Secondary Objectives
1. **Brand Recognition**: Establish LegalAI as a trusted legal information platform
2. **Scalability**: Support 1,000+ concurrent users with sub-2-second response times
3. **Revenue Generation**: Prepare framework for premium tiers and API licensing
4. **Data Collection**: Build anonymized query dataset for legal trends analysis

### Success Criteria
- **User Satisfaction**: 4.5+ star rating from user feedback
- **Response Accuracy**: 90%+ accuracy in legal information retrieval
- **System Uptime**: 99.5% availability
- **Session Completion Rate**: 70%+ of sessions reach resolution

---

## Target Users

### Primary User Personas

#### 1. **Legal Researcher** (Law Student/Junior Associate)
- **Demographics**: Ages 22-30, law students or early-career professionals
- **Goals**: Quick access to case law, statutory references, and legal concepts
- **Pain Points**: Time-consuming manual research, limited access to premium databases
- **Use Case**: Preparing case briefs, understanding legal doctrines, exam preparation

#### 2. **Self-Represented Litigant**
- **Demographics**: Ages 30-55, general public seeking legal information
- **Goals**: Understand legal rights, procedures, and basic legal options
- **Pain Points**: High cost of legal consultations, complexity of legal terminology
- **Use Case**: Understanding legal procedures, preliminary contract reviews, consumer rights

#### 3. **Legal Professional** (Lawyer/Paralegal)
- **Demographics**: Ages 28-50, practicing attorneys and legal support staff
- **Goals**: Fast preliminary research, reference verification, client communication prep
- **Pain Points**: Billable hour pressure, need for rapid information retrieval
- **Use Case**: Pre-consultation research, statute verification, citation lookup

#### 4. **Small Business Owner**
- **Demographics**: Ages 35-60, entrepreneurs and SME operators
- **Goals**: Compliance understanding, contract drafting guidance, regulatory navigation
- **Pain Points**: Cost of retainer counsel, basic legal questions don't warrant attorney fees
- **Use Case**: Employment law queries, contract review basics, incorporation questions

---

## User Stories

### Core Functionality

**US-001**: As a user, I want to start a new legal consultation session so that I can organize my queries by topic.  
**Acceptance Criteria**: Click "New Consultation" creates a new session with unique ID and displays empty chat interface.

**US-002**: As a user, I want to ask legal questions in natural language so that I don't need to know legal jargon.  
**Acceptance Criteria**: System accepts plain-language queries and returns structured legal responses.

**US-003**: As a user, I want the system to remember our conversation so that I don't have to repeat context.  
**Acceptance Criteria**: Follow-up questions reference previous messages in the same session.

**US-004**: As a user, I want to see my previous consultation sessions so that I can refer back to past advice.  
**Acceptance Criteria**: Sidebar displays all sessions ordered by most recent with titles and timestamps.

**US-005**: As a user, I want to delete old sessions so that I can maintain privacy and organization.  
**Acceptance Criteria**: Delete button removes session and all associated messages from database.

### Advanced Features

**US-006**: As a legal researcher, I want the AI to cite authoritative sources so that I can verify the information.  
**Acceptance Criteria**: Responses include citations to statutes, case law, and legal commentaries.

**US-007**: As a user, I want to edit my previous messages so that I can refine my questions without starting over.  
**Acceptance Criteria**: Edit function updates message and regenerates AI response from that point forward.

**US-008**: As a user, I want real-time web search integration so that I receive current legal information.  
**Acceptance Criteria**: System uses DuckDuckGo and LawBhoomi scraper for up-to-date legal content.

**US-009**: As a user, I want responses formatted with clear structure so that I can easily understand complex legal issues.  
**Acceptance Criteria**: Responses follow template: Facts, Issues, Analysis, Law References, Cases, Conclusion.

**US-010**: As a mobile user, I want the interface to work on my smartphone so that I can access legal help anywhere.  
**Acceptance Criteria**: Responsive design supports screens 320px-2560px wide with optimized layouts.

---

## Functional Requirements

### FR-1: Session Management
- **FR-1.1**: System shall create unique UUID-based session identifiers
- **FR-1.2**: System shall auto-generate session titles from first user message (truncated to 50 chars)
- **FR-1.3**: System shall display sessions in descending order by last update timestamp
- **FR-1.4**: System shall allow users to delete sessions and all associated messages
- **FR-1.5**: System shall update session timestamps on every new message

### FR-2: Chat Functionality
- **FR-2.1**: System shall accept text input up to 10,000 characters
- **FR-2.2**: System shall validate that messages are non-empty before submission
- **FR-2.3**: System shall display user messages immediately in the UI
- **FR-2.4**: System shall show loading indicator during AI response generation
- **FR-2.5**: System shall render AI responses with Markdown formatting support
- **FR-2.6**: System shall sanitize all user input and AI output to prevent XSS attacks

### FR-3: AI Agent Integration
- **FR-3.1**: System shall use Groq's Llama 3.3 70B model with temperature 0.1 for consistency
- **FR-3.2**: System shall restrict AI responses to legal topics only
- **FR-3.3**: System shall provide structured responses with: Facts, Issues, Analysis, Laws, Cases, Conclusion
- **FR-3.4**: System shall maintain context from the last 5 messages for continuity
- **FR-3.5**: System shall refuse non-legal queries with standardized message

### FR-4: Data Persistence
- **FR-4.1**: System shall store all sessions in SQLite database with ACID compliance
- **FR-4.2**: System shall persist messages with session_id foreign key constraint
- **FR-4.3**: System shall record timestamps for all database entries
- **FR-4.4**: System shall initialize database schema on first application start
- **FR-4.5**: System shall handle database connection pooling for concurrent requests

### FR-5: Search & Research Tools
- **FR-5.1**: System shall integrate DuckDuckGo web search for general legal queries
- **FR-5.2**: System shall utilize custom LawBhoomi scraper for Indian law notes
- **FR-5.3**: System shall extract and clean HTML content from legal websites
- **FR-5.4**: System shall handle HTTP errors gracefully and report to user
- **FR-5.5**: System shall set appropriate user-agent headers for ethical scraping

### FR-6: Message Editing
- **FR-6.1**: System shall allow editing of user messages only (not assistant messages)
- **FR-6.2**: System shall delete all subsequent messages after edited message
- **FR-6.3**: System shall regenerate AI response after message edit
- **FR-6.4**: System shall update message timestamps upon edit

### FR-7: User Interface
- **FR-7.1**: System shall display animated gavel loader during page initialization
- **FR-7.2**: System shall show collapsible sidebar with session history
- **FR-7.3**: System shall auto-scroll chat to latest message
- **FR-7.4**: System shall display message timestamps in human-readable format
- **FR-7.5**: System shall highlight current active session in sidebar

---

## Non-Functional Requirements

### NFR-1: Performance
- **NFR-1.1**: Page load time shall not exceed 3 seconds on standard broadband
- **NFR-1.2**: AI response generation shall complete within 30 seconds for 95% of queries
- **NFR-1.3**: Database queries shall execute in under 100ms
- **NFR-1.4**: Application shall support 100 concurrent users without degradation
- **NFR-1.5**: Static assets shall be cached with max-age of 0 for development

### NFR-2: Reliability
- **NFR-2.1**: System uptime shall be 99.5% during business hours
- **NFR-2.2**: Database backups shall occur daily with 30-day retention
- **NFR-2.3**: Application shall recover from crashes within 30 seconds (auto-restart)
- **NFR-2.4**: All critical errors shall be logged with stack traces
- **NFR-2.5**: Graceful degradation when external APIs (Groq, DuckDuckGo) are unavailable

### NFR-3: Scalability
- **NFR-3.1**: Architecture shall support migration to PostgreSQL for production
- **NFR-3.2**: Stateless design shall enable horizontal scaling via load balancers
- **NFR-3.3**: Database schema shall accommodate 1M+ messages without performance loss
- **NFR-3.4**: API rate limiting shall be configurable per user/session

### NFR-4: Usability
- **NFR-4.1**: Interface shall be accessible to users with WCAG 2.1 Level AA compliance
- **NFR-4.2**: Navigation shall be intuitive with max 3 clicks to any feature
- **NFR-4.3**: Error messages shall be user-friendly and actionable
- **NFR-4.4**: Mobile interface shall maintain full functionality on 375px+ screens
- **NFR-4.5**: Keyboard navigation shall be fully supported

### NFR-5: Security
- **NFR-5.1**: All HTTP traffic shall use HTTPS in production
- **NFR-5.2**: Session secrets shall use cryptographically secure random generation
- **NFR-5.3**: SQL injection attacks shall be prevented via parameterized queries
- **NFR-5.4**: XSS attacks shall be prevented via DOMPurify sanitization
- **NFR-5.5**: API keys shall be stored in environment variables, never in code

### NFR-6: Maintainability
- **NFR-6.1**: Code shall follow PEP 8 style guidelines for Python
- **NFR-6.2**: Functions shall have clear docstrings explaining purpose and parameters
- **NFR-6.3**: Database migrations shall be version-controlled
- **NFR-6.4**: Configuration shall be externalized via .env files
- **NFR-6.5**: Logging shall use structured format (JSON) for easy parsing

### NFR-7: Compatibility
- **NFR-7.1**: Application shall work on Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **NFR-7.2**: Database shall be compatible with SQLite 3.31+
- **NFR-7.3**: Python runtime shall be 3.8+
- **NFR-7.4**: Mobile browsers shall be supported (iOS Safari, Chrome Mobile)

---

## Technical Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        User Browser                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │          HTML/CSS/JavaScript Frontend                │   │
│  │  - legal_chat.html (Template)                        │   │
│  │  - legal_style_final.css (Styling)                   │   │
│  │  - legal_app.js (Logic) + jQuery                     │   │
│  │  - Marked.js (Markdown) + DOMPurify (Sanitization)   │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────────────┬─────────────────────────────────────┘
                        │ AJAX/REST API
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                     Flask Application                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  app.py (Main)                       │   │
│  │  - Route Handlers (/api/chat, /api/sessions, etc.)  │   │
│  │  - Session Management Functions                     │   │
│  │  - Database Operations (CRUD)                       │   │
│  │  - Agent Initialization & Orchestration             │   │
│  └──────────────────────────────────────────────────────┘   │
└───┬───────────────────┬─────────────────────┬───────────────┘
    │                   │                     │
    ▼                   ▼                     ▼
┌─────────┐   ┌──────────────────┐   ┌──────────────────┐
│ SQLite  │   │   Agno Agent     │   │  External APIs   │
│Database │   │  ┌────────────┐  │   │  - Groq (LLM)    │
│         │   │  │ Groq Model │  │   │  - DuckDuckGo    │
│Sessions │   │  │ (Llama 3.3)│  │   │  - LawBhoomi     │
│Messages │   │  └────────────┘  │   │                  │
│         │   │  ┌────────────┐  │   │                  │
│         │   │  │   Tools    │  │   │                  │
│         │   │  │ - DDG      │──┼───┤                  │
│         │   │  │ - Scraper  │──┼───┤                  │
│         │   │  └────────────┘  │   │                  │
└─────────┘   └──────────────────┘   └──────────────────┘
```

### Component Descriptions

#### Frontend Layer
- **Template Engine**: Jinja2 (Flask default)
- **UI Framework**: Custom CSS with ChatGPT-inspired design
- **JavaScript Libraries**: jQuery 3.6.0, Marked.js, DOMPurify 3.0.6
- **Icons**: Font Awesome 6.4.0

#### Application Layer
- **Web Framework**: Flask 2.x
- **Session Management**: Flask sessions with SECRET_KEY
- **Environment Config**: python-dotenv for .env file management
- **Error Handling**: Try-catch blocks with logging

#### AI Agent Layer
- **Framework**: Agno Agent (custom autonomous agent library)
- **LLM Provider**: Groq Cloud API
- **Model**: Llama 3.3 70B Versatile (temperature=0.1)
- **Tools**: 
  - DuckDuckGoTools (web search)
  - LawbhoomiScraperTool (custom legal content scraper)

#### Data Layer
- **Database**: SQLite 3 (development), PostgreSQL-ready schema
- **ORM**: Native sqlite3 Python module
- **Schema**: Normalized relational design with foreign keys

#### External Services
- **Groq API**: Primary LLM inference
- **DuckDuckGo Search**: General web search
- **LawBhoomi**: Indian law notes repository

### Data Flow

1. **User Query Submission**:
   ```
   User → Frontend (JS) → POST /api/chat/{session_id}/message 
   → Flask Route → Save User Message → DB
   ```

2. **AI Processing**:
   ```
   Flask → Load Chat History (last 5 msgs) → Create Agent with Context
   → Agent.run(user_message) → Groq API Call → Tool Invocations (DDG/Scraper)
   → Generate Structured Response
   ```

3. **Response Delivery**:
   ```
   Agent Response → Save to DB → JSON Response → Frontend
   → Markdown Rendering → Display to User
   ```

### Database Schema

```sql
-- Table: chat_sessions
CREATE TABLE chat_sessions (
    id TEXT PRIMARY KEY,              -- UUID v4 format
    title TEXT NOT NULL,              -- Truncated first message (max 50 chars)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: chat_messages
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,         -- FK to chat_sessions.id
    role TEXT NOT NULL,               -- 'user' or 'assistant'
    content TEXT NOT NULL,            -- Message text (supports Markdown)
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions (id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_messages_session ON chat_messages(session_id);
CREATE INDEX idx_messages_timestamp ON chat_messages(timestamp DESC);
CREATE INDEX idx_sessions_updated ON chat_sessions(updated_at DESC);
```

---

## System Features

### Feature 1: Intelligent Chat Interface

**Description**: Core conversational interface with context-aware legal AI.

**User Flow**:
1. User selects/creates session
2. Types legal question in input box
3. Clicks send or presses Enter
4. Loading animation displays
5. AI response appears with Markdown formatting
6. User can continue conversation or edit previous messages

**Technical Implementation**:
- AJAX POST to `/api/chat/{session_id}/message`
- Backend retrieves last 5 messages for context
- Agno agent processes with Groq Llama 3.3 70B
- Response stored in DB and returned as JSON
- Frontend renders with Marked.js + DOMPurify

**Acceptance Criteria**:
- Response time < 30s for 95th percentile
- Markdown tables, lists, bold/italic render correctly
- No XSS vulnerabilities in rendered content
- Context maintained across 10+ message turns

---

### Feature 2: Session Management System

**Description**: Organize conversations into distinct consultation sessions.

**User Flow**:
1. Click "New Consultation" button
2. New session created with UUID
3. Session appears in sidebar with "New Legal Consultation" title
4. After first message, title auto-updates to message snippet
5. Click any session to load conversation
6. Hover over session shows delete icon

**Technical Implementation**:
- UUID generation via Python `uuid.uuid4()`
- SQLite transactions for ACID compliance
- Frontend sidebar updates via `/api/sessions` GET
- Click handler loads session via `/api/chat/{id}` GET
- Delete via `/api/delete_session/{id}` DELETE

**Acceptance Criteria**:
- Sessions persist across browser refreshes
- Deletion cascades to all messages
- Active session highlighted in sidebar
- Sidebar scrollable with 100+ sessions

---

### Feature 3: Web-Enhanced Legal Research

**Description**: AI agent autonomously searches web for current legal information.

**User Flow**:
1. User asks question requiring recent cases/laws
2. AI agent determines search needed
3. DuckDuckGo tool queries relevant terms
4. LawBhoomi scraper fetches Indian law notes (if applicable)
5. Agent synthesizes information into structured answer
6. Citations included in response

**Technical Implementation**:
- Agno agent's tool selection logic
- DuckDuckGoTools wrapper (from Agno library)
- Custom LawbhoomiScraperTool class:
  - Requests library with custom user-agent
  - BeautifulSoup4 HTML parsing
  - Content extraction with fallback logic
- Error handling for timeouts/HTTP errors

**Acceptance Criteria**:
- Tools invoked when user query contains terms like "recent," "current," "latest"
- Timeout set to 15 seconds for web requests
- Failed tool calls don't crash session
- Results integrated naturally into response prose

---

### Feature 4: Message Editing & Regeneration

**Description**: Edit previous user messages and regenerate conversation from that point.

**User Flow**:
1. User hovers over previous user message
2. Edit icon appears
3. Clicks edit, message becomes editable textarea
4. Modifies text and saves
5. All subsequent messages deleted
6. AI generates new response to edited message

**Technical Implementation**:
- PUT request to `/api/chat/{session_id}/edit/{message_id}`
- Validation: only user messages editable
- SQL: `DELETE FROM chat_messages WHERE id > {message_id}`
- Re-run agent with updated history
- Frontend re-renders conversation

**Acceptance Criteria**:
- Edit preserves all messages before edited one
- Regenerated response differs if edit is substantive
- Cannot edit assistant messages
- Loading state shown during regeneration

---

### Feature 5: Structured Legal Response Format

**Description**: AI responses follow standardized legal analysis template.

**Template Structure**:
1. **Introduction/Summary of Facts**: Context overview
2. **Legal Issues Identified**: Key questions of law
3. **Legal Analysis**: Step-by-step reasoning
4. **Applicable Laws**: Statutes, articles, sections cited
5. **Landmark Cases**: Case name, citation, relevance
6. **Conclusion/Judgment**: Clear answer with reasoning

**Technical Implementation**:
- Detailed prompt engineering in agent instructions
- Temperature set to 0.1 for consistency
- Markdown formatting for headers and lists
- Agent examples in system prompt

**Acceptance Criteria**:
- 90%+ of responses include all 6 template sections
- Case citations include case name + year
- Statutory references include Act name + section number
- Conclusion directly answers user's query

---

### Feature 6: Responsive Mobile Interface

**Description**: Full functionality on smartphones and tablets.

**Technical Implementation**:
- CSS media queries for breakpoints:
  - Mobile: 320px-768px
  - Tablet: 768px-1024px
  - Desktop: 1024px+
- Flexbox and Grid layouts
- Touch-friendly tap targets (min 44x44px)
- Collapsible sidebar on mobile
- Font scaling for readability

**Acceptance Criteria**:
- All features accessible on iPhone SE (375px width)
- Sidebar slides in/out on mobile
- Input box remains above keyboard
- No horizontal scrolling

---

## User Interface Requirements

### UI-1: Layout & Navigation

**Header Bar**:
- Logo/brand icon (gavel icon)
- Application title: "LegalAI – Professional Legal Assistant"
- New Consultation button (always visible)

**Sidebar** (Desktop: always visible, Mobile: toggleable):
- Header: "Chat History"
- Session list (scrollable)
- Each session shows: title (1 line), timestamp
- Active session highlighted in blue
- Hover shows delete icon

**Main Chat Area**:
- Message list (auto-scroll to bottom)
- User messages: right-aligned, blue background
- AI messages: left-aligned, gray background
- Timestamp below each message
- Edit icon on user message hover

**Input Area** (fixed bottom):
- Text input field (multi-line, auto-expand up to 5 lines)
- Send button (disabled when empty)
- Character count (optional enhancement)

### UI-2: Visual Design

**Color Palette (Judicial Cosmos Theme)**:
- Void: `#04060f` (near-black deep space) - main background
- Obsidian: `#0a0e1a` (panel base) - panel backgrounds
- Glass surfaces: `rgba(255,255,255,0.04-0.12)` - glassmorphism layers
- Neon Gold: `#c9a84c` (primary accent) - justice gold for UI elements
- Neon Ice: `#4fc3f7` (secondary accent) - cold legal blue
- Neon Violet: `#9b59b6` (tertiary) - judgment purple
- Plasma: `#00e5ff` (interactive highlights) - hover states
- Text Primary: `#e8eaf0` (off-white) - primary text
- Text Muted: `#6b7694` (muted blue-gray) - secondary text

**Typography**:
- Display/Logo: "Cinzel Decorative" (Google Fonts) - Roman, authoritative
- Headings: "Cormorant Garamond" (Google Fonts) - elegant editorial
- Body/UI: "DM Sans" (Google Fonts) - clean, modern, highly legible
- Mono/Citations: "JetBrains Mono" (Google Fonts) - precise, technical
- Headers: 1.5-2rem with gradient text effects
- Body: 16px (0.95rem in messages)
- Code: 0.85em monospace with glass backgrounds

**Spacing**:
- Container padding: 24px
- Message spacing: 16px vertical
- Element margins: 8px standard, 16px section breaks

**Animations**:
- Cinematic intro: 2.5s scales rotation sequence (replaces gavel loader)
- Nebula orbs: 40s floating animation with blur effects
- Star field: 150 micro-stars with staggered pulse animations
- Message entry: 0.3s cubic-bezier bounce animation
- Glassmorphic hover: Border glow + transform effects
- Custom cursor: Magnetic attraction with rotation on hover
- Typewriter effect: AI messages type first 200 characters
- All animations respect prefers-reduced-motion

### UI-3: Loading States

**Initial Page Load (Cinematic Sequence)**:
- Full-screen intro with animated scales of justice
- 2.5s choreographed sequence:
  - t=0.2s: Nebula background fades in
  - t=0.4s: Header slides down from top
  - t=0.6s: Sidebar slides in from left
  - t=0.8s: Scales icon rotates 360° and settles
  - t=1.2s: Main content reveals with stagger
- Glassmorphic layers build depth progressively

**Message Sending**:
- Disable input field with glass effect
- Show "thinking" indicator with morphing dots and cycling phrases:
  - "Analyzing legal precedents..."
  - "Researching case law..."
  - "Reviewing statutory provisions..."
  - "Consulting legal databases..."
  - "Formulating response..."
- Send button: Gold-to-plasma gradient with pulse animation
- AI avatar: Pulsing glow effect during processing

**Session Loading**:
- Skeleton loaders for messages
- Fade-in animation on content load

### UI-4: Error States

**Network Errors**:
- Red banner at top: "Connection lost. Retrying..."
- Auto-retry with exponential backoff

**Invalid Input**:
- Inline validation message below input
- Border changes to red

**AI Errors**:
- System message in chat: "I encountered an error. Please try rephrasing your question."
- Error details logged to console (not shown to user)

### UI-5: Accessibility

**Keyboard Navigation**:
- Tab order: sidebar sessions → new button → message list → input → send
- Enter to send message
- Esc to close modals/sidebar (mobile)

**Screen Readers**:
- ARIA labels on all interactive elements
- Role attributes (role="complementary" for sidebar)
- Live regions for new messages (aria-live="polite")

**Contrast Ratios**:
- Text-to-background: minimum 4.5:1 (WCAG AA)
- Interactive elements: minimum 3:1

---

## API Specifications

### API-1: Create New Session

**Endpoint**: `POST /api/new_session`

**Request**:
```json
(No body required)
```

**Response** (200 OK):
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "success"
}
```

**Error Responses**:
- 500 Internal Server Error: Database connection failure

---

### API-2: List All Sessions

**Endpoint**: `GET /api/sessions`

**Request**: (No parameters)

**Response** (200 OK):
```json
{
  "sessions": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "What is Section 509 of IPC?",
      "created_at": "2026-02-19 14:30:00",
      "updated_at": "2026-02-19 15:45:00"
    },
    {
      "id": "660f9511-f30c-52e5-b827-557766551111",
      "title": "Contract law basics",
      "created_at": "2026-02-18 10:15:00",
      "updated_at": "2026-02-18 11:20:00"
    }
  ]
}
```

---

### API-3: Get Chat History

**Endpoint**: `GET /api/chat/<session_id>`

**Path Parameters**:
- `session_id` (string): UUID of the session

**Response** (200 OK):
```json
{
  "history": [
    {
      "id": 1,
      "role": "user",
      "content": "What is Section 509 of IPC?",
      "timestamp": "2026-02-19 14:30:15"
    },
    {
      "id": 2,
      "role": "assistant",
      "content": "## Legal Issue\n\nSection 509 of the Indian Penal Code...",
      "timestamp": "2026-02-19 14:30:42"
    }
  ]
}
```

**Error Responses**:
- 404 Not Found: Session ID doesn't exist

---

### API-4: Send Message

**Endpoint**: `POST /api/chat/<session_id>/message`

**Path Parameters**:
- `session_id` (string): UUID of the session

**Request Body**:
```json
{
  "message": "What are the penalties for copyright infringement?"
}
```

**Response** (200 OK):
```json
{
  "response": "## Introduction\n\nCopyright infringement penalties vary...",
  "status": "success"
}
```

**Error Responses**:
- 400 Bad Request: Empty message
  ```json
  {"error": "Message cannot be empty"}
  ```
- 500 Internal Server Error: AI processing failure
  ```json
  {
    "error": "Internal server error",
    "details": "Groq API timeout"
  }
  ```

---

### API-5: Delete Session

**Endpoint**: `DELETE /api/delete_session/<session_id>`

**Path Parameters**:
- `session_id` (string): UUID of the session

**Response** (200 OK):
```json
{
  "status": "success"
}
```

**Error Responses**:
- 500 Internal Server Error: Database operation failed
  ```json
  {"error": "Failed to delete session"}
  ```

---

### API-6: Edit Message

**Endpoint**: `PUT /api/chat/<session_id>/edit/<message_id>`

**Path Parameters**:
- `session_id` (string): UUID of the session
- `message_id` (integer): ID of the message to edit

**Request Body**:
```json
{
  "message": "Updated question about trademark law"
}
```

**Response** (200 OK):
```json
{
  "response": "## Introduction\n\nRegarding trademark law...",
  "status": "success"
}
```

**Error Responses**:
- 400 Bad Request: Empty message
- 404 Not Found: Message doesn't exist or is not a user message
  ```json
  {"error": "Message not found or cannot edit assistant messages"}
  ```

---

## Data Management

### DM-1: Data Storage

**Database Location**: `legal_chat.db` in application root directory

**Backup Strategy**:
- Daily automated backups (cron job/scheduled task)
- Retention: 30 days
- Storage: Local disk or cloud storage (S3, Google Cloud Storage)

**Migration Path**:
- Development: SQLite (current)
- Production: PostgreSQL or MySQL
- Schema compatibility maintained via SQLAlchemy (future enhancement)

### DM-2: Data Retention

**User Data**:
- Sessions: Indefinite (user-controlled deletion)
- Messages: Indefinite (tied to session lifecycle)
- Logs: 90 days rolling window

**Analytics Data** (future):
- Anonymized query patterns: 1 year
- Performance metrics: 6 months

### DM-3: Data Privacy

**PII Handling**:
- No user authentication required (anonymous usage)
- Session IDs are non-sequential UUIDs (prevents enumeration)
- No IP tracking or browser fingerprinting
- Chat content not shared with third parties (except Groq API for processing)

**GDPR Considerations** (if serving EU users):
- Right to erasure: Implement session export + delete feature
- Data portability: Export sessions as JSON
- Consent: Display privacy notice on first use

### DM-4: Data Security

**Encryption**:
- At rest: OS-level disk encryption (BitLocker, FileVault, LUKS)
- In transit: HTTPS/TLS 1.3 in production
- Database: No sensitive PII, encryption optional

**Access Control**:
- Database file permissions: 600 (owner read/write only)
- Flask secret key: 256-bit random, stored in .env
- API keys: Environment variables, never committed to Git

---

## Security & Compliance

### SEC-1: Authentication & Authorization

**Current State**: No authentication (public access)

**Future Enhancements**:
- User registration/login (email + password or OAuth)
- Session ownership (link session to user ID)
- Rate limiting per user (100 messages/hour)

### SEC-2: Input Validation

**User Messages**:
- Max length: 10,000 characters
- Sanitization: DOMPurify on frontend, parameterized queries on backend
- Content filtering: Block executable code patterns (<script>, eval, etc.)

**Session IDs**:
- Format validation: UUID v4 regex pattern
- Existence check before operations

### SEC-3: Vulnerability Prevention

**SQL Injection**:
- Use parameterized queries exclusively (no string concatenation)
- Example: `cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))`

**XSS (Cross-Site Scripting)**:
- DOMPurify sanitizes HTML before rendering
- Content-Security-Policy header in production
- Escape Jinja2 template variables (default behavior)

**CSRF (Cross-Site Request Forgery)**:
- Flask sessions with httponly cookies
- CSRF tokens for state-changing operations (future: Flask-WTF)

**Dependency Vulnerabilities**:
- Monthly `pip-audit` scans
- Automated Dependabot/Renovate PRs for updates

### SEC-4: API Security

**Rate Limiting** (future):
- 100 requests/minute per IP
- 1000 requests/day per session
- Implementation: Flask-Limiter

**CORS (Cross-Origin Resource Sharing)**:
- Current: Same-origin only
- Production: Whitelist specific domains if needed

**API Key Protection**:
- Groq API key: .env file, never logged
- Rotation: Quarterly or on suspected breach

### SEC-5: Legal Compliance

**Disclaimer**:
- Prominent notice: "For informational purposes only, not legal advice"
- Required on initial session and in footer

**Copyright**:
- AI-generated responses: No copyright claims
- Scraped content: Fair use for educational purposes
- User content: User retains ownership

**Terms of Service** (future):
- Acceptable use policy (no illegal advice)
- Liability limitations
- Dispute resolution

---

## Dependencies & Integrations

### Core Dependencies

| Package | Version | Purpose | License |
|---------|---------|---------|---------|
| Flask | 2.x | Web framework | BSD-3-Clause |
| python-dotenv | 1.x | Environment config | BSD-3-Clause |
| agno | Latest | AI agent framework | MIT (assumed) |
| groq | Latest | LLM API client | Apache 2.0 (assumed) |
| duckduckgo-search | Latest | Web search | MIT |
| requests | 2.x | HTTP client | Apache 2.0 |
| beautifulsoup4 | 4.x | HTML parser | MIT |
| flask-cors | Latest | CORS support | MIT |

### Frontend Dependencies (CDN)

| Library | Version | Purpose |
|---------|---------|---------|
| jQuery | 3.6.0 | DOM manipulation |
| Marked.js | Latest | Markdown rendering |
| DOMPurify | 3.0.6 | HTML sanitization |
| Font Awesome | 6.4.0 | Icons |

### External Integrations

**Groq Cloud API**:
- **Purpose**: Large language model inference
- **Model**: Llama 3.3 70B Versatile
- **Pricing**: Pay-per-token (check Groq pricing)
- **Rate Limits**: 60 requests/minute (verify with Groq docs)
- **Fallback**: None (critical dependency)

**DuckDuckGo API**:
- **Purpose**: Web search for real-time legal information
- **Pricing**: Free (rate-limited)
- **Rate Limits**: ~100 requests/minute
- **Fallback**: Disable tool if exceeds limits

**LawBhoomi**:
- **Purpose**: Scrape legal notes content
- **Method**: HTTP GET + BeautifulSoup parsing
- **Rate Limits**: Self-imposed (max 10 requests/minute)
- **Fallback**: Return cached content or skip tool

---

## Success Metrics

### Key Performance Indicators (KPIs)

**Engagement Metrics**:
- **Daily Active Users (DAU)**: Target 100 by Month 3
- **Messages per Session**: Target 5+ (indicates helpful responses)
- **Session Completion Rate**: 70%+ (user gets answer before leaving)
- **Returning User Rate**: 40%+ (user creates 2+ sessions)

**Quality Metrics**:
- **User Satisfaction**: 4.5+ stars (post-session survey)
- **Response Accuracy**: 90%+ (manual review of 100 random responses/month)
- **Citation Rate**: 80%+ of responses include legal references
- **Structured Format Compliance**: 85%+ responses follow template

**Performance Metrics**:
- **Median Response Time**: <15 seconds
- **95th Percentile Response Time**: <30 seconds
- **API Error Rate**: <2% of requests
- **Uptime**: 99.5% monthly

**Business Metrics** (future):
- **Cost per Query**: <$0.05 (Groq API costs)
- **User Acquisition Cost**: TBD (marketing spend)
- **Conversion to Premium**: 10% (if freemium model)

### Monitoring & Analytics

**Application Monitoring**:
- Error tracking: Sentry or Rollbar
- Performance monitoring: New Relic or DataDog
- Uptime monitoring: UptimeRobot or Pingdom

**User Analytics**:
- Event tracking: PostHog or Mixpanel
  - Events: session_created, message_sent, session_deleted, message_edited
- Funnel analysis: First visit → first session → 5+ messages → return visit

**A/B Testing** (future):
- Test response formats (structured vs. conversational)
- Test AI model parameters (temperature, max tokens)
- Test UI variations (sidebar vs. tabs)

---

## Constraints & Assumptions

### Constraints

**Technical Constraints**:
- **TC-1**: SQLite not suitable for 10K+ concurrent users (must migrate to PostgreSQL)
- **TC-2**: Groq API rate limits restrict throughput (60 RPM)
- **TC-3**: Single-server deployment (no load balancing in v1)
- **TC-4**: No user authentication (cannot track individual users across sessions)
- **TC-5**: Web scraping subject to target site changes (LawBhoomi structure)

**Business Constraints**:
- **BC-1**: Free tier only (no monetization in v1)
- **BC-2**: No dedicated SLA or support team
- **BC-3**: Limited legal review of AI responses (rely on model accuracy)

**Legal Constraints**:
- **LC-1**: Cannot provide personalized legal advice (liability risk)
- **LC-2**: Must display prominent disclaimer
- **LC-3**: Subject to copyright fair use limitations on scraped content

### Assumptions

**User Assumptions**:
- **UA-1**: Users have basic legal literacy (understand terms like "statute," "case law")
- **UA-2**: Users will read disclaimer and understand limitations
- **UA-3**: Users have stable internet connection (min 1 Mbps)
- **UA-4**: Users access from desktop/mobile browsers (not native apps)

**Technical Assumptions**:
- **TA-1**: Groq API remains available and affordable
- **TA-2**: DuckDuckGo doesn't block automated queries
- **TA-3**: LawBhoomi content remains publicly accessible
- **TA-4**: Hosting environment has 99%+ uptime (cloud provider SLA)

**Business Assumptions**:
- **BA-1**: Legal professionals willing to use AI for preliminary research
- **BA-2**: Market demand exists for free legal information tools
- **BA-3**: Quality responses will drive organic growth (word-of-mouth)

---

## Future Enhancements

### Phase 2 Enhancements (3-6 months)

**FE-2.1: User Authentication**:
- Email/password registration
- OAuth (Google, Microsoft)
- Session ownership and cross-device sync

**FE-2.2: Document Upload**:
- PDF contract upload for analysis
- Text extraction and summarization
- Clause-by-clause breakdown

**FE-2.3: Citation Verification**:
- Automated fact-checking of case citations
- Links to primary sources (court websites, legal databases)
- Confidence scores for legal assertions

**FE-2.4: Export Functionality**:
- Export session as PDF with formatting
- Share session via unique link
- Email transcript to user

**FE-2.5: Advanced Search**:
- Search across all user sessions
- Filter by date, legal topic, jurisdiction
- Full-text search in message content

### Phase 3 Enhancements (6-12 months)

**FE-3.1: Multi-Jurisdiction Support**:
- Select jurisdiction (India, USA, UK, etc.)
- Jurisdiction-specific legal databases
- Comparative law analysis

**FE-3.2: Legal Document Drafting**:
- Template-based contract generation
- NDA, employment agreement, lease templates
- Customization via Q&A wizard

**FE-3.3: Voice Interface**:
- Speech-to-text query input
- Text-to-speech response playback
- Accessibility for visually impaired users

**FE-3.4: Collaborative Sessions**:
- Share session with another user (lawyer + client)
- Real-time co-browsing of legal research
- Annotation and highlighting

**FE-3.5: Premium Tier**:
- Priority response times (<10s)
- Access to GPT-4 or Claude models
- Unlimited sessions (vs. 10/month free tier)
- Advanced analytics dashboard

### Long-Term Vision (12+ months)

**FE-LT.1: Mobile Native Apps**:
- iOS and Android apps
- Push notifications for session updates
- Offline mode with cached responses

**FE-LT.2: Legal Knowledge Graph**:
- Visual representation of legal relationships
- Interactive case law network diagram
- Statute dependency trees

**FE-LT.3: Predictive Analytics**:
- Case outcome prediction based on facts
- Settlement value estimation
- Litigation risk assessment

**FE-LT.4: Integration with Legal Tech Stack**:
- API for e-discovery platforms
- CRM integration (Clio, MyCase)
- Calendar integration for court dates

**FE-LT.5: White-Label Solution**:
- Customizable branding for law firms
- Self-hosted deployment option
- Admin dashboard for analytics

---

## Glossary

| Term | Definition |
|------|------------|
| **Agno** | AI agent framework used for orchestrating LLM tools and workflows |
| **AJAX** | Asynchronous JavaScript and XML; technique for updating web pages without reload |
| **CRUD** | Create, Read, Update, Delete; basic database operations |
| **DDG** | DuckDuckGo; privacy-focused search engine |
| **DOMPurify** | JavaScript library for sanitizing HTML to prevent XSS attacks |
| **Groq** | AI infrastructure company providing fast LLM inference |
| **IPC** | Indian Penal Code; criminal law statute in India |
| **Jinja2** | Template engine for Python (Flask default) |
| **LawBhoomi** | Legal education website with law notes and resources |
| **Llama 3.3 70B** | Large language model (70 billion parameters) by Meta AI |
| **LLM** | Large Language Model; AI trained on vast text corpora |
| **Markdown** | Lightweight markup language for formatted text |
| **REST API** | Representational State Transfer; architectural style for web services |
| **SQLite** | Lightweight relational database management system |
| **UUID** | Universally Unique Identifier; 128-bit label for session identification |
| **WCAG** | Web Content Accessibility Guidelines; standards for accessible web design |
| **XSS** | Cross-Site Scripting; security vulnerability allowing script injection |

---

## Appendix

### A: Environment Setup

**Required Environment Variables**:
```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxx
SECRET_KEY=your-256-bit-secret-key-here
DEBUG=True  # Set to False in production
PORT=8080
```

**Installation Commands**:
```bash
# Clone repository
git clone <repo-url>
cd LegalAI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
python app.py
```

### B: Testing Checklist

**Functional Tests**:
- [ ] Create new session generates unique UUID
- [ ] Send message saves to database and returns AI response
- [ ] Edit message deletes subsequent messages and regenerates
- [ ] Delete session removes all associated messages
- [ ] Session list displays in reverse chronological order
- [ ] Markdown rendering works for tables, lists, code blocks
- [ ] Web search tools invoked for appropriate queries

**Non-Functional Tests**:
- [ ] Load test: 100 concurrent users for 10 minutes
- [ ] Response time <30s for standard legal query
- [ ] Database handles 10K+ messages without slowdown
- [ ] Mobile responsive design on 375px screen
- [ ] Accessibility: keyboard navigation, screen reader compatibility
- [ ] Security: XSS, SQL injection, CSRF prevention verified

### C: Deployment Checklist

**Production Readiness**:
- [ ] Set `DEBUG=False` in environment
- [ ] Generate strong `SECRET_KEY` (256-bit random)
- [ ] Configure HTTPS/TLS certificate
- [ ] Set up database backups (daily)
- [ ] Configure error logging (Sentry)
- [ ] Set up uptime monitoring
- [ ] Implement rate limiting
- [ ] Add Content-Security-Policy headers
- [ ] Conduct security audit (OWASP Top 10)
- [ ] Load test with expected traffic

---

**Document Version History**:
- v1.0 (2026-02-19): Initial PRD creation

**Approval**:
- Product Manager: ___________________
- Engineering Lead: ___________________
- Legal Counsel: ___________________

**Next Review Date**: 2026-05-19
