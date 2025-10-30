Prompt

# LLM Chat App PRD

A technical requirements document for a locally-hosted LLM-powered chat application using Ollama, Go, React/Vite, and Elasticsearch.

## Overview

The goal of the app is to let real estate agents chat with an LLM and ask for property or people data related to the area they are working in.
This application enables users to interact with a locally running LLM via an intuitive chat interface. The backend architecture can instructs the LLM to call external functions for more property or people contextual data that will help the LLM to produce a better response.

## User Interface

- **Centred Chat Bar:** The chat interface displays a single input bar, centred on the page.
- **Minimalist Design:** UI follows a clean, uncluttered layout.
- **Frontend Tech:** Built using Node.js, React, and Vite.
- **Design:** Black Theme

## Backend Architecture

### LLM Adapter Service (Go)

- API Endpoint: Receives chat queries from the UI.
- System Prompt Augmentation: Each query is wrapped with system instructions, guiding the LLM's response style and behaviour. The instruction should include the external function definitions that the LLM should call to fetch additional data to help generate an agent-personalised response.
- Context Injection: Enriches queries by fetching user info from a local database. The local database would be SQLite-based.
- LLM Query: Forwards the composed prompt to the locally-running Ollama LLM and waits for its output.
- Function Invocation: If the LLM needs it will invoke the external API call to get additional data.

### User Profile DB ===

Will store the user data and will be accessed by the LLM adaper. 
The DB will have the following tables: 

- UserInfo
  -- Agent ID (Primary Key)
  -- First Name
  -- Last Name
  -- Agency
  -- Area of work that will be list of suburbs (names and post code)
- PropertyListings - Addresses of properties that the agent listed for sale in the past, currently listed properties and the state of the listing
  -- Agent ID (UserInfo.AgentID)
  -- Sold, sold date - the date of when the property was sold
  -- Active
  -- Withdrew
- LLM Conversations
  -- Agent ID (UserInfo.AgentID)
  -- Query
  -- Response

### Backend Search Service (Go)

- **Search API Endpoints:**
  - `/search/people`: Accepts person-related queries.
  - `/search/property`: Accepts property-related queries.
- **Database Operations:** Communicates with an Elasticsearch backend to fulfil search requests.
- **Response Delivery:** Returns search results to the LLM, which use them to generate the response responses.

## LLM Function Calling with Ollama

- **Function Definition:** Backend defines tools/functions, with names, descriptions, and parameter schemas (JSON schema).
- **Prompt Integration:** Functions are described to the LLM in each session.
- **Result Injection:** Search results or external data are returned to the LLM for final response generation.

## Technologies Used


| Component           | Technology           |
| ------------------- | -------------------- |
| Frontend            | React, Vite, Node.js |
| LLM Adapter Service | Go                   |
| Local LLM           | Ollama               |
| Search Service      | Go                   |
| Search Database     | Elasticsearch        |

## User and API Flow Example

1. User submits a chat message via the frontend that calls the LLM adapter.
2. Adapter wraps the message with system context, agent profile info that will contain the agent working area and property listings listings, and the external data-fetching function call instruction and definitions and forwards it to LLM as a single prompt.
3. LLM start generating a response, and if needed, calls the external function it got as part of the prompt and uses it to generate a response to the user. If the call to the external function to get data returns an empty value, then proceed without the data.
4. The LLM reply back to the LLM adapter with the response
5. LLM Adapter store the request and the response in its local DB
6. Final response is delivered to the user and displayed on the UI.

## Recommended Languages

- **Go** for backend services and function execution, for speed, concurrency, and maintainability.

# Repo structure 
- frontend: will contain the UI code 
- backend: will have the backend services 
