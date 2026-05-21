from django.test import SimpleTestCase
from unittest.mock import patch

from api.services.llm_prompting import (
    analyze_sampled_tweets,
    build_analysis_prompt,
    parse_analysis_output,
)


class LlmPromptingTests(SimpleTestCase):
    def setUp(self):
        self.sample = [
            {
                "tweet_id": "1",
                "author_name": "Alice",
                "screen_name": "alice",
                "text": "Climate policy and clean energy",
                "promoted": False,
                "is_reply": False,
            },
            {
                "tweet_id": "2",
                "author_name": "Alice",
                "screen_name": "alice",
                "text": "Transit delays and city updates",
                "promoted": False,
                "is_reply": True,
            },
        ]

    def test_build_analysis_prompt_includes_sample_context(self):
        prompt = build_analysis_prompt(self.sample)

        self.assertIn("Return JSON only", prompt)
        self.assertIn("Sample size: 2", prompt)
        self.assertIn("@alice (Alice)", prompt)
        self.assertIn("Climate policy and clean energy", prompt)

    def test_parse_analysis_output_prefers_json(self):
        parsed = parse_analysis_output(
            '{"reflection":"Paragraph one.\\n\\nParagraph two."}'
        )

        self.assertEqual(parsed["reflection"], "Paragraph one.\n\nParagraph two.")

    def test_analyze_sampled_tweets_returns_structured_payload(self):
        with patch(
            "api.services.llm_prompting.get_llm_generator",
            return_value=lambda prompt, **kwargs: [
                {
                    "generated_text": '{"reflection":"Paragraph one.\\n\\nParagraph two."}'
                }
            ],
        ):
            payload = analyze_sampled_tweets(self.sample)

        self.assertEqual(payload["model_name"], "google/flan-t5-small")
        self.assertEqual(payload["prompt_version"], "v2")
        self.assertEqual(payload["parse_status"], "ok")
        self.assertEqual(
            payload["analysis"]["reflection"], "Paragraph one.\n\nParagraph two."
        )
        self.assertTrue(payload["prompt"])

    def test_analyze_sampled_tweets_falls_back_on_errors(self):
        with patch(
            "api.services.llm_prompting.get_llm_generator",
            side_effect=RuntimeError("model unavailable"),
        ):
            payload = analyze_sampled_tweets(self.sample)

        self.assertEqual(payload["parse_status"], "fallback")
        self.assertTrue(payload["analysis"]["reflection"])
        self.assertIn("fallback_reason", payload["analysis"])
