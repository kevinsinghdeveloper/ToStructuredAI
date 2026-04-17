"""LangChain-based AI service manager supporting multiple LLM providers."""
import json
from typing import Dict, Any, List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from abstractions.IServiceManagerBase import IServiceManagerBase
from abstractions.connectors.ChatAgentConnectorBase import ChatAgentConnectorBase


class LangChainServiceManager(IServiceManagerBase, ChatAgentConnectorBase):
    """
    LangChain-based AI service manager.
    Supports OpenAI and Anthropic providers for chat completions.
    """

    def __init__(self, service_manager_config: Dict[str, Any]):
        IServiceManagerBase.__init__(self, service_manager_config)
        ChatAgentConnectorBase.__init__(self, service_manager_config.get("config", {}))
        self._format = service_manager_config.get("config", {}).get("format")

    def configure(self):
        config = self.get_config()
        provider = config.get("provider")
        model_name = config.get("model_name")
        gen_config = config.get("gen_config", {})
        api_key = gen_config.get("api_key")

        if not provider:
            raise ValueError("Model provider must be specified")
        if not model_name:
            raise ValueError("Model Name must be specified")

        provider = provider.lower()
        if provider == "openai":
            if not api_key:
                raise ValueError("Model API key must be specified")
            self._configure_openai(model_name, api_key, gen_config)
        elif provider == "anthropic":
            self._configure_anthropic(model_name, api_key, gen_config)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def _configure_openai(self, model_name: str, api_key: Optional[str], gen_config: Dict):
        from langchain_openai import ChatOpenAI
        self._model = ChatOpenAI(
            model=model_name, api_key=api_key,
            temperature=gen_config.get("temperature", 0.7),
            max_tokens=gen_config.get("max_tokens", 2000),
            top_p=gen_config.get("top_p"),
            frequency_penalty=gen_config.get("frequency_penalty"),
            presence_penalty=gen_config.get("presence_penalty"),
            timeout=gen_config.get("timeout", 60),
        )

    def _configure_anthropic(self, model_name: str, api_key: Optional[str], gen_config: Dict):
        from langchain_anthropic import ChatAnthropic
        self._model = ChatAnthropic(
            model_name=model_name, api_key=api_key,
            temperature=gen_config.get("temperature", 0.7),
            max_tokens_to_sample=gen_config.get("max_tokens", 2000),
            top_p=gen_config.get("top_p"),
            top_k=gen_config.get("top_k"),
            timeout=gen_config.get("timeout", 60),
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    def _invoke_with_retry(self, messages):
        return self._model.invoke(messages)

    def submit_general_prompt(
        self, prompt: str, llm_instructions: Optional[str] = None, is_json: bool = False
    ) -> Dict[str, Any]:
        from langchain_core.messages import SystemMessage, HumanMessage

        messages = []
        if llm_instructions:
            content = llm_instructions
            if is_json and self._format != "json":
                content += "\n\nIMPORTANT: Return your response as valid JSON."
            messages.append(SystemMessage(content=content))
        messages.append(HumanMessage(content=prompt))

        response = self._invoke_with_retry(messages)
        return {
            "message": {"content": response.content},
            "model": self._model_name,
            "provider": self._provider,
        }

    def create_chat_completion(
        self, messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

        lc_messages = []
        for msg in messages:
            role, content = msg.get("role"), msg.get("content")
            if role == "system":
                lc_messages.append(SystemMessage(content=content))
            elif role == "user":
                lc_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))

        if response_format:
            instruction = "\n\nIMPORTANT: Return your response as valid JSON matching this schema: " + json.dumps(response_format)
            if lc_messages and isinstance(lc_messages[0], SystemMessage):
                lc_messages[0].content += instruction
            else:
                lc_messages.insert(0, SystemMessage(content=instruction))

        if temperature is not None or max_tokens is not None:
            model = self._model
            if temperature is not None:
                model = model.bind(temperature=temperature)
            if max_tokens is not None:
                model = model.bind(max_tokens=max_tokens)
            response = model.invoke(lc_messages)
        else:
            response = self._invoke_with_retry(lc_messages)

        return response.content

    def create_completion(
        self, messages: List[Dict[str, str]],
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        return self.create_chat_completion(messages=messages, response_format=response_format)

    def run_task(self, request: Dict[str, Any]) -> Any:
        task_type = request.get("task_type")
        if task_type == "completion":
            return self.create_completion(request.get("messages", []), request.get("response_format"))
        elif task_type == "prompt":
            result = self.submit_general_prompt(
                request.get("prompt", ""), request.get("instructions"), request.get("is_json", False)
            )
            return result["message"]["content"]
        else:
            raise ValueError(f"Unknown task type: {task_type}")
