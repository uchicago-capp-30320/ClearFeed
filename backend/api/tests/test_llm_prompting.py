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
        self.feed_summary = {
            "overview": {
                "top_users": ["alice"],
                "total_tweets": 2,
                "since_date": "2026-05-01",
                "promoted_percentage": 0,
            },
            "categories": {
                "labels": ["Climate", "Transit"],
                "series": [
                    {
                        "name": "Topic as a Percent of Tweets",
                        "data": [50, 50],
                    }
                ],
            },
            "word_frequency": {
                "labels": ["climate", "policy"],
                "series": [
                    {
                        "name": "Frequency",
                        "data": [3, 2],
                    }
                ],
            },
            "sentiment": {
                "sentiment_average": 0.5,
                "labels": ["Negative", "Neutral", "Positive"],
                "series": [
                    {
                        "name": "Percentage of Tweets",
                        "data": [0, 50, 50],
                    }
                ],
            },
        }

    def test_build_analysis_prompt_includes_sample_and_feed_context(self):
        prompt = build_analysis_prompt(self.sample, feed_summary=self.feed_summary)

        self.assertIn("Return JSON only", prompt)
        self.assertIn("Feed-wide stats:", prompt)
        self.assertIn("total tweets 2", prompt)
        self.assertIn("Climate (50%)", prompt)
        self.assertIn("climate (3)", prompt)
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
            payload = analyze_sampled_tweets(
                self.sample, feed_summary=self.feed_summary
            )

        self.assertEqual(payload["model_name"], "microsoft/Phi-3.5-mini-instruct")
        self.assertEqual(payload["parse_status"], "ok")
        self.assertEqual(
            payload["analysis"]["reflection"], "Paragraph one.\n\nParagraph two."
        )
        self.assertTrue(payload["prompt"])
        self.assertIn("Feed-wide stats:", payload["prompt"])

    def test_analyze_sampled_tweets_falls_back_on_errors(self):
        with patch(
            "api.services.llm_prompting.get_llm_generator",
            side_effect=RuntimeError("model unavailable"),
        ):
            payload = analyze_sampled_tweets(self.sample)

        self.assertEqual(payload["parse_status"], "fallback")
        self.assertTrue(payload["analysis"]["reflection"])
        self.assertIn("fallback_reason", payload["analysis"])
