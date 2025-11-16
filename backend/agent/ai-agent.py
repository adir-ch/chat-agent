import logging
import requests
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory


MODEL = "qwen3:0.6b" #"gemma3:1b" #
FETCH_URL = "http://localhost:8090/search/people"
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# # Silence noisy HTTP logs
# for name in ["httpx", "httpcore", "urllib3"]:
#     logging.getLogger(name).setLevel(logging.WARNING)

# # Optionally silence LangChain internals too
# for name in ["langchain", "langchain_core", "langchain_community", "langchain_ollama"]:
#     logging.getLogger(name).setLevel(logging.ERROR)

LOGGER = logging.getLogger(__name__)


# ----------------------------------------------------------
# Utility: fetch homeowner data from your backend
# ----------------------------------------------------------
def fetch_people(query: str) -> str:
    """Fetch live homeowner data from your local endpoint."""
    LOGGER.debug(">>>>>>>>>>>> fetch_people: starting request for query='%s'", query)
    try:
        response = requests.get(FETCH_URL, params={"q": query})
        response.raise_for_status()
        #LOGGER.debug("fetch_people: completed request with status=%s", response.status_code)
        LOGGER.debug(">>>>>>>>>>>> fetch_people: completed request with: %s", response.text)
        return response.text
    except Exception as e:
        LOGGER.debug("fetch_people: request failed with error=%s", e)
        return f"Error fetching data: {e}"

# ----------------------------------------------------------
# Agent creation
# ----------------------------------------------------------
def create_agent(agent_name: str, location: str, listings: list[str]):
    LOGGER.debug("create_agent: initializing agent='%s' location='%s' listings=%s",
                 agent_name, location, listings)

    llm = ChatOllama(model=MODEL, base_url="http://localhost:11434")
    LOGGER.debug("create_agent: ChatOllama initialized with model=%s", MODEL)

    # prompt = ChatPromptTemplate.from_template(
    #     "You are a helpful real estate assistant working with agent {agent_name} in {location}. "
    #     "Their current listings are: {listings}. "
    #     "If you need live homeowner or prospect data, respond ONLY with:\n"
    #     "FETCH: <search terms to send to the data service>\n\n"
    #     "Conversation so far:\n{chat_history}\n\n"
    #     "User question: {question}"
    # )

    # prompt = ChatPromptTemplate.from_template(
    #     "You are a helpful real estate assistant working with agent {agent_name} in {location}. "
    #     "Their current listings are: {listings}. "
    #     "\n\n"
    #     "If you need live homeowner or prospect data, you must respond ONLY in the following format:\n"
    #     "FETCH: <suburb name or postcode>\n\n"
    #     "Rules for FETCH:\n"
    #     "- Never include full street addresses.\n"
    #     "- Never include commas, unit numbers, or street names.\n"
    #     "- Always use just a suburb or postcode.\n"
    #     "- Do not include any explanations, punctuation, or text other than the FETCH line.\n\n"
    #     "Conversation so far:\n{chat_history}\n\n"
    #     "User question: {question}"
    # )

    prompt = ChatPromptTemplate.from_template(
        "You are a helpful real estate assistant working with agent {agent_name} in {location}. "
        "Their current listings are: {listings}.\n\n"
        "You operate in two modes:\n"
        "1. Query Mode – When you do NOT yet have homeowner or prospect data:\n"
        "   • Respond ONLY in the format:  FETCH: <suburb name or postcode>\n"
        "   • Follow these rules:\n"
        "     - Never include full street addresses or commas.\n"
        "     - Use only a suburb or postcode.\n"
        "     - Output nothing except the single FETCH line.\n\n"
        "2. Analysis Mode – When the user provides homeowner or prospect data "
        "(you will see text like 'Here are the search results...' or 'Data:' in the conversation):\n"
        "   • Do NOT use FETCH again.\n"
        "   • Analyse the provided data and summarise key opportunities for the agent, "
        "     such as potential leads, timing, or market insights.\n\n"
        "Conversation so far:\n{chat_history}\n\n"
        "User question: {question}"
    )


    LOGGER.debug("create_agent: ChatPromptTemplate ready")

    # Use modern message-based memory
    history = ChatMessageHistory()

    chain = prompt | llm

    # Wrap with message-history memory
    runnable = RunnableWithMessageHistory(
        chain,
        lambda session_id: history,
        input_messages_key="question",
        history_messages_key="chat_history"
    )
    LOGGER.debug("create_agent: chain assembled")
    return runnable, history


# ----------------------------------------------------------
# Main application loop
# ----------------------------------------------------------
def main():
    LOGGER.debug("main: starting application setup")
    print("🏡 Real Estate AI Assistant (LangChain + Ollama)")
    print("Type 'exit' to quit.\n")

    # Suppress LangChain log output
    logging.getLogger("langchain").setLevel(logging.ERROR)
    logging.getLogger("langchain_core").setLevel(logging.ERROR)
    logging.getLogger("langchain_community").setLevel(logging.ERROR)
    logging.getLogger("langchain_ollama").setLevel(logging.ERROR)

    agent_name = "agent-123"
    location = "Bondi"
    listings = ["156 Campbell Pde", "88 Beach Rd"]

    chain, history = create_agent(agent_name, location, listings)

    while True:
        question = input("You: ").strip()
        if question.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        inputs = {
            "agent_name": agent_name,
            "location": location,
            "listings": ", ".join(listings),
            "question": question,
        }

        response = chain.invoke(
            inputs,
            config={"configurable": {"session_id": "default"}},
        ).content.strip()

        if response.upper().startswith("FETCH:"):
            print(f">>>>>>>>> first invoke: {response}\n")

            query = response[6:].strip()
            print(f"🔍 Fetching data for: {query}")
            data = fetch_people(query)

            follow_up = (
                f"Here are the search results for '{query}': {data}\n"
                "Please summarise the key opportunities for the agent."
            )

            #LOGGER.debug("follow_up: %s\n", follow_up)

            response = chain.invoke(
                {
                    "agent_name": agent_name,
                    "location": location,
                    "listings": ", ".join(listings),
                    "question": follow_up,
                },
                config={"configurable": {"session_id": "default"}},
            ).content.strip()
            print(f">>>>>>>>>>>> second invoke: {follow_up}:\n{response}\n")

        print(f"AI: {response}\n")


if __name__ == "__main__":
    LOGGER.debug("main: entrypoint triggered")
    main()


