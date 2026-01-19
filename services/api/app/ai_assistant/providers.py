from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import structlog

logger = structlog.get_logger()


class Message:
    """Represents a message in the conversation"""
    def __init__(self, role: str, content: str):
        self.role = role  # "user", "assistant", "system"
        self.content = content


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def generate(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """Generate a response from the LLM"""
        pass
    
    @abstractmethod
    def generate_with_tools(
        self,
        messages: List[Message],
        tools: List[Dict],
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a response with tool calling support"""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider"""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
        except ImportError:
            logger.error("openai package not installed")
            raise
    
    def generate(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """Generate response using OpenAI"""
        formatted_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=formatted_messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
    
    def generate_with_tools(
        self,
        messages: List[Message],
        tools: List[Dict],
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate with tool calling"""
        formatted_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=formatted_messages,
            tools=tools,
            temperature=temperature
        )
        
        message = response.choices[0].message
        
        if message.tool_calls:
            return {
                "type": "tool_call",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                    for tc in message.tool_calls
                ]
            }
        else:
            return {
                "type": "text",
                "content": message.content
            }


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider"""
    
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key
        self.model = model
        
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=api_key)
        except ImportError:
            logger.error("anthropic package not installed")
            raise
    
    def generate(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """Generate response using Anthropic"""
        # Separate system message
        system_message = None
        formatted_messages = []
        
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                formatted_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_message,
            messages=formatted_messages
        )
        
        return response.content[0].text
    
    def generate_with_tools(
        self,
        messages: List[Message],
        tools: List[Dict],
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate with tool calling"""
        system_message = None
        formatted_messages = []
        
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                formatted_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=temperature,
            system=system_message,
            messages=formatted_messages,
            tools=tools
        )
        
        # Check for tool use
        for block in response.content:
            if block.type == "tool_use":
                return {
                    "type": "tool_call",
                    "tool_calls": [{
                        "id": block.id,
                        "name": block.name,
                        "arguments": block.input
                    }]
                }
        
        # Text response
        return {
            "type": "text",
            "content": response.content[0].text
        }


class GeminiProvider(LLMProvider):
    """Google Gemini provider"""
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-pro"):
        self.api_key = api_key
        self.model = model
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel(model)
        except ImportError:
            logger.error("google-generativeai package not installed")
            raise
    
    def generate(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """Generate response using Gemini"""
        # Convert messages to Gemini format
        chat_history = []
        for msg in messages[:-1]:  # All except last
            if msg.role != "system":
                chat_history.append({
                    "role": "user" if msg.role == "user" else "model",
                    "parts": [msg.content]
                })
        
        # Start chat
        chat = self.client.start_chat(history=chat_history)
        
        # Send last message
        last_message = messages[-1].content
        response = chat.send_message(
            last_message,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens
            }
        )
        
        return response.text
    
    def generate_with_tools(
        self,
        messages: List[Message],
        tools: List[Dict],
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate with tool calling (function calling in Gemini)"""
        # Convert tools to Gemini format
        gemini_tools = []
        for tool in tools:
            gemini_tools.append({
                "function_declarations": [{
                    "name": tool["function"]["name"],
                    "description": tool["function"]["description"],
                    "parameters": tool["function"]["parameters"]
                }]
            })
        
        # Create model with tools
        import google.generativeai as genai
        model_with_tools = genai.GenerativeModel(
            self.model,
            tools=gemini_tools
        )
        
        # Convert messages
        chat_history = []
        for msg in messages[:-1]:
            if msg.role != "system":
                chat_history.append({
                    "role": "user" if msg.role == "user" else "model",
                    "parts": [msg.content]
                })
        
        chat = model_with_tools.start_chat(history=chat_history)
        response = chat.send_message(messages[-1].content)
        
        # Check for function calls
        if response.candidates[0].content.parts[0].function_call:
            fc = response.candidates[0].content.parts[0].function_call
            return {
                "type": "tool_call",
                "tool_calls": [{
                    "id": "gemini_call",
                    "name": fc.name,
                    "arguments": dict(fc.args)
                }]
            }
        
        return {
            "type": "text",
            "content": response.text
        }


def create_provider(provider_name: str, api_key: str, model: Optional[str] = None) -> LLMProvider:
    """
    Factory function to create LLM provider.
    
    Args:
        provider_name: "openai", "anthropic", or "gemini"
        api_key: API key for the provider
        model: Optional model name override
    """
    provider_name = provider_name.lower()
    
    if provider_name == "openai":
        return OpenAIProvider(api_key, model or "gpt-4")
    elif provider_name == "anthropic":
        return AnthropicProvider(api_key, model or "claude-3-5-sonnet-20241022")
    elif provider_name == "gemini":
        return GeminiProvider(api_key, model or "gemini-1.5-pro")
    else:
        raise ValueError(f"Unknown provider: {provider_name}")
