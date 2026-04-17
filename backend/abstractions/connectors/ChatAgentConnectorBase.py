"""Base class for chat/completion AI connectors."""
from abc import abstractmethod
from typing import Dict, Any, List, Optional
from abstractions.connectors.AIConnectorBase import AIConnectorBase


class ChatAgentConnectorBase(AIConnectorBase):

    @abstractmethod
    def submit_general_prompt(
        self, prompt: str, llm_instructions: Optional[str] = None, is_json: bool = False
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def create_chat_completion(
        self, messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        pass

    @abstractmethod
    def create_completion(
        self, messages: List[Dict[str, str]],
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        pass

    def format_messages(self, prompt: str, system_message: Optional[str] = None) -> List[Dict[str, str]]:
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        return messages
