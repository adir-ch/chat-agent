"""
Utility functions for the AI Agent service.
"""
import re
import requests
import logging
from typing import Tuple

from config import Config
from models import TokenUsage

# Shared logger instance for the agent service
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
LOGGER = logging.getLogger("agent")


def fetch_people(query: str) -> str:
    """Fetch live homeowner data from your local endpoint."""
    LOGGER.debug(">>>>>>>>>>>> fetch_people: starting request for query='%s'", query)
    try:
        response = requests.get(Config.FETCH_URL, params={"q": query})
        response.raise_for_status()
        LOGGER.debug(">>>>>>>>>>>> fetch_people: completed request with: %s", response.text)
        return response.text
    except Exception as e:
        LOGGER.debug("fetch_people: request failed with error=%s", e)
        return f"Error fetching data: {e}"


def mask_sensitive_data(text: str) -> str:
    """
    Mask sensitive data in text:
    - Phone numbers: mask the middle 4 digits
    - Email addresses: mask 3-4 letters in the local part (before @)
    - Dates are NOT masked (e.g., 2024-01-01, 01/01/2024)
    """
    masked_text = text
    
    # Common date patterns to exclude from phone masking
    date_patterns = [
        r'\d{4}-\d{2}-\d{2}',      # YYYY-MM-DD (e.g., 2024-01-01)
        r'\d{2}/\d{2}/\d{4}',      # DD/MM/YYYY or MM/DD/YYYY (e.g., 01/01/2024)
        r'\d{4}/\d{2}/\d{2}',      # YYYY/MM/DD (e.g., 2024/01/01)
    ]
    
    # Mask mobile numbers - find sequences of digits that look like phone numbers (8-15 digits)
    # Match phone numbers in various formats: +61 412 345 678, 0412 345 678, (04) 1234 5678, etc.
    phone_pattern = r'(?:\+?\d{1,3}[-.\s()]?)?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}'
    
    def mask_phone(match):
        phone = match.group(0)
        
        # Check if this match looks like a date pattern - if so, don't mask it
        for date_pattern in date_patterns:
            if re.match(date_pattern, phone):
                return phone
        
        # Extract only digits
        digits = re.sub(r'\D', '', phone)
        
        if len(digits) >= 8:  # Only mask if it looks like a phone number
            # Mask middle 4 digits
            if len(digits) <= 10:
                # For 8-10 digit numbers: keep first 2 and last 2, mask middle 4
                masked_digits = digits[:2] + '****' + digits[-2:]
            else:
                # For longer numbers: keep first 3 and last 3, mask middle 4
                masked_digits = digits[:3] + '****' + digits[-3:]
            
            # Build masked phone by replacing digits sequentially
            result = list(phone)
            digit_pos = 0
            for i, char in enumerate(result):
                if char.isdigit():
                    if digit_pos < len(masked_digits):
                        result[i] = masked_digits[digit_pos]
                        digit_pos += 1
            return ''.join(result)
        
        return phone
    
    masked_text = re.sub(phone_pattern, mask_phone, masked_text)
    
    # Mask email addresses - mask 3-4 characters in the local part (before @)
    email_pattern = r'\b([a-zA-Z0-9._+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'
    
    def mask_email(match):
        local_part = match.group(1)
        domain = match.group(2)
        
        # Split local part by dots to handle cases like "john.doe"
        parts = local_part.split('.')
        masked_parts = []
        
        for part in parts:
            # Count only letters in this part
            letters_only = re.sub(r'[^a-zA-Z]', '', part)
            
            if len(letters_only) <= 2:
                # Too short to mask meaningfully
                masked_parts.append(part)
            elif len(letters_only) <= 5:
                # Mask 3 letters, keep first and last letter visible
                first_letter_idx = next((i for i, c in enumerate(part) if c.isalpha()), None)
                last_letter_idx = next((i for i in range(len(part)-1, -1, -1) if part[i].isalpha()), None)
                if first_letter_idx is not None and last_letter_idx is not None:
                    masked_part = part[:first_letter_idx+1] + '***' + part[last_letter_idx:]
                    masked_parts.append(masked_part)
                else:
                    masked_parts.append(part)
            else:
                # Mask 4 letters, keep first and last letter visible
                first_letter_idx = next((i for i, c in enumerate(part) if c.isalpha()), None)
                last_letter_idx = next((i for i in range(len(part)-1, -1, -1) if part[i].isalpha()), None)
                if first_letter_idx is not None and last_letter_idx is not None:
                    masked_part = part[:first_letter_idx+1] + '****' + part[last_letter_idx:]
                    masked_parts.append(masked_part)
                else:
                    masked_parts.append(part)
        
        masked_local = '.'.join(masked_parts)
        return f"{masked_local}@{domain}"
    
    masked_text = re.sub(email_pattern, mask_email, masked_text)
    
    return masked_text


def extract_token_usage(response) -> Tuple[int, int]:
    """
    Extract token usage from LLM response metadata.
    Returns (input_tokens, output_tokens) tuple.
    Works with both Ollama and OpenAI response formats.
    """
    input_tokens = 0
    output_tokens = 0
    
    try:
        # LangChain AIMessage objects have response_metadata
        if hasattr(response, 'response_metadata'):
            metadata = response.response_metadata
            if metadata:
                # Try common field names for token usage
                if 'token_usage' in metadata:
                    token_usage = metadata['token_usage']
                    input_tokens = token_usage.get('prompt_tokens', token_usage.get('input_tokens', 0))
                    output_tokens = token_usage.get('completion_tokens', token_usage.get('output_tokens', 0))
                elif 'prompt_tokens' in metadata:
                    input_tokens = metadata.get('prompt_tokens', 0)
                    output_tokens = metadata.get('completion_tokens', metadata.get('eval_count', 0))
                elif 'eval_count' in metadata:
                    # Ollama format: eval_count is output tokens, prompt_eval_count is input tokens
                    output_tokens = metadata.get('eval_count', 0)
                    input_tokens = metadata.get('prompt_eval_count', 0)
        
        # Also check if response has usage_metadata attribute (some LangChain versions)
        if hasattr(response, 'usage_metadata'):
            usage = response.usage_metadata
            if usage:
                input_tokens = getattr(usage, 'input_tokens', input_tokens)
                output_tokens = getattr(usage, 'output_tokens', output_tokens)
        
        # Debug: log the response structure if no tokens found
        if input_tokens == 0 and output_tokens == 0:
            LOGGER.debug("extract_token_usage: no tokens found in response. Available attributes: %s", 
                        dir(response) if hasattr(response, '__dict__') else 'N/A')
    except Exception as e:
        LOGGER.debug("extract_token_usage: error extracting tokens: %s", e)
    
    return input_tokens, output_tokens


def track_and_log_token_usage(response, token_usage: TokenUsage, session_id: str, invoke_label: str = "invoke") -> Tuple[int, int]:
    """
    Extract token usage from LLM response, update session totals, and log the information.
    
    Args:
        response: The LLM response object
        token_usage: The TokenUsage object for the session
        session_id: The session identifier for logging
        invoke_label: Label to identify which invoke this is (e.g., "first invoke", "second invoke")
    
    Returns:
        Tuple[int, int]: (input_tokens, output_tokens) for this invocation
    """
    # Extract token usage from response
    input_tokens, output_tokens = extract_token_usage(response)
    
    # Update session token totals
    token_usage.add(input_tokens, output_tokens)
    
    # Log token usage information
    LOGGER.info(
        "Token usage for session '%s' (%s): Input: %d, Output: %d, Total: %d | "
        "Session totals: Input: %d, Output: %d, Total: %d",
        session_id,
        invoke_label,
        input_tokens, output_tokens, input_tokens + output_tokens,
        token_usage.input_tokens, token_usage.output_tokens, token_usage.total_tokens
    )
    
    return input_tokens, output_tokens

