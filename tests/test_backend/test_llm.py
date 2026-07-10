from backend.ai.llms.base_llm import BaseLLM
from backend.ai.llms.gemini import GeminiLLM


def test_base_llm_subclass() -> None:
    """
    Verifies that GeminiLLM correctly inherits from BaseLLM and has target attributes.
    """
    llm = GeminiLLM(model_name="gemini-2.5-flash", temperature=0.5)
    assert isinstance(llm, BaseLLM)
    assert llm.model_name == "gemini-2.5-flash"
    assert llm.temperature == 0.5


def test_gemini_client_lazy_load() -> None:
    """
    Verifies that the unified client manager holds a lazy loading initialization flag.
    """
    llm = GeminiLLM()
    assert llm._client is None

    # Trigger client load (it resolves even under mock environment keys)
    client = llm._get_client()
    assert client is not None
    assert llm._client is not None
