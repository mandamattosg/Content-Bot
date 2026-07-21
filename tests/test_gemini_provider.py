from app.providers.gemini import GeminiProvider


def test_parse_response_handles_markdown_json() -> None:
    provider = GeminiProvider(api_key="test-key")

    response = '''```json
{
  "topics": [
    {
      "topic": "Harry Potter",
      "score": 9.5,
      "reason": "High engagement and recurring demand",
      "sources": ["reddit", "news", "trends"],
      "video_ideas": ["one", "two", "three"]
    }
  ]
}
```'''

    parsed = provider._parse_response(response)

    assert parsed["topics"][0]["topic"] == "Harry Potter"
    assert parsed["topics"][0]["score"] == 9.5
    assert parsed["topics"][0]["sources"] == ["reddit", "news", "trends"]


def test_candidate_models_prefers_configured_model_and_fallbacks() -> None:
    provider = GeminiProvider(api_key="test-key", model_name="gemini-1.5-flash")

    assert provider._candidate_models("gemini-1.5-flash")[0] == "gemini-1.5-flash"
    assert "gemini-2.0-flash" in provider._candidate_models("gemini-1.5-flash")
