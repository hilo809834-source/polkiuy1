"""
Model Router - config-driven, multi-provider, pinned model versions, capped retries.

Per ARCHITECTURE.md model routing strategy:
- Route by task type, not by habit.
- Keep this entirely config-driven — provider and model string per tier, 
  swappable without touching calling code.
- Hugging Face's hosted Inference API is a legitimate provider for any tier.
- Pin exact model versions explicitly in config.
- Use litellm as the unified interface for provider calls.

Phase 1 DoD: a real call succeeds against two different real providers, 
with the actual response text from each pasted as evidence.
"""
import os
import time
import sys
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from enum import Enum

import litellm

from core.config.settings import MODEL_CONFIG, API_KEYS, MAX_RETRIES, RETRY_DELAY_SECONDS

# Set litellm to suppress debug output
os.environ["LITELLM_LOG"] = "ERROR"
os.environ["LITELLM_DROP_PARAMS"] = "True"


class ModelTier(Enum):
    FAST = "fast"
    MID = "mid"
    FRONTIER = "frontier"


@dataclass
class ModelResponse:
    """Response from a model call."""
    content: str
    provider: str
    model: str
    tokens_used: Optional[int] = None
    latency_ms: Optional[float] = None
    raw_response: Optional[Dict[str, Any]] = None


class ModelProviderError(Exception):
    """Raised when a model provider call fails."""
    pass


class ModelRouter:
    """
    Config-driven model router with multi-provider support.
    Routes by tier (fast/mid/frontier), not by habit.
    Uses litellm for unified provider access.
    """
    
    def __init__(self):
        self.config = MODEL_CONFIG
        self.api_keys = API_KEYS
        self.max_retries = MAX_RETRIES
        self.retry_delay = RETRY_DELAY_SECONDS
    
    def _get_provider_config(self, tier: ModelTier) -> Dict[str, str]:
        """Get provider and model config for a tier."""
        tier_name = tier.value
        if tier_name not in self.config:
            raise ValueError(f"Unknown tier: {tier_name}")
        return self.config[tier_name]
    
    def _get_api_key(self, provider: str) -> str:
        """Get API key for a provider."""
        key = self.api_keys.get(provider)
        if not key:
            raise ModelProviderError(f"No API key configured for provider: {provider}")
        return key
    
    async def call(self, tier: ModelTier, prompt: str, system_message: Optional[str] = None) -> ModelResponse:
        """
        Make a model call through the appropriate provider.
        Routes by tier, uses config-driven provider/model.
        """
        config = self._get_provider_config(tier)
        provider = config["provider"]
        model = config["model"]
        
        # Set API key in environment for litellm
        api_key = self._get_api_key(provider)
        
        # Build messages
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        start_time = time.time()
        
        try:
            # Use litellm for unified API access
            # litellm handles provider-specific logic
            if provider == "openai":
                response = await litellm.acompletion(
                    model=f"openai/{model}",
                    messages=messages,
                    api_key=api_key,
                    max_tokens=1000
                )
            elif provider == "anthropic":
                response = await litellm.acompletion(
                    model=f"anthropic/{model}",
                    messages=messages,
                    api_key=api_key,
                    max_tokens=1000
                )
            elif provider == "huggingface":
                # HuggingFace via litellm
                response = await litellm.acompletion(
                    model=f"huggingface/{model}",
                    messages=messages,
                    api_key=api_key,
                    max_tokens=250
                )
            else:
                raise ModelProviderError(f"Unknown provider: {provider}")
            
            latency = (time.time() - start_time) * 1000
            
            return ModelResponse(
                content=response["choices"][0]["message"]["content"],
                provider=provider,
                model=model,
                tokens_used=response.get("usage", {}).get("total_tokens"),
                latency_ms=latency,
                raw_response=response
            )
            
        except Exception as e:
            raise ModelProviderError(f"{provider} call failed: {e}")
    
    async def call_provider_direct(
        self, 
        provider: str, 
        model: str, 
        messages: List[Dict],
        api_key: str
    ) -> ModelResponse:
        """
        Make a direct call to a specific provider/model.
        Used for Phase 1 DoD: real calls against multiple providers.
        """
        start_time = time.time()
        
        try:
            response = await litellm.acompletion(
                model=f"{provider}/{model}",
                messages=messages,
                api_key=api_key,
                max_tokens=1000
            )
            
            latency = (time.time() - start_time) * 1000
            
            return ModelResponse(
                content=response["choices"][0]["message"]["content"],
                provider=provider,
                model=model,
                tokens_used=response.get("usage", {}).get("total_tokens"),
                latency_ms=latency,
                raw_response=response
            )
            
        except Exception as e:
            raise ModelProviderError(f"{provider} call failed: {e}")


# Singleton instance
_model_router: Optional[ModelRouter] = None

def get_model_router() -> ModelRouter:
    global _model_router
    if _model_router is None:
        _model_router = ModelRouter()
    return _model_router
