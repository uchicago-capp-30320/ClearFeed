from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from .models import AppUser, BrowseSession, TopicResult, Tweet, ViewedTweet


class TopicSummaryTests(TestCase):
    def setUp(self):
        self.user = AppUser.objects.create()
        self.session = BrowseSession.objects.create(
            user=self.user,
            platform="x",
            user_agent="test-agent",
        )

    def _add_tweets(self, topic, count):
        for index in range(count):
            tweet = Tweet.objects.create(
                tweet_id=f"{topic}-{index}",
                full_text=f"{topic} tweet {index}",
            )
            TopicResult.objects.create(tweet=tweet, topic=topic)
            ViewedTweet.objects.create(
                user=self.user,
                session=self.session,
                tweet=tweet,
            )

    def test_topic_summary_returns_chart_payload(self):
        self._add_tweets("cats", 10)
        self._add_tweets("politics", 8)
        self._add_tweets("basketball", 2)
        self._add_tweets("family_and_friends", 2)
        self._add_tweets("weddings", 2)

        self.client.force_login(self.user)
        response = self.client.get(reverse("topic_summary"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "categories": [
                    "Cats",
                    "Politics",
                    "Basketball",
                    "Family and Friends",
                    "Weddings",
                ],
                "series": [
                    {
                        "name": "Topic as a Percent of Tweets",
                        "data": [42, 33, 8, 8, 8],
                    }
                ],
            },
        )

    def test_topic_summary_requires_user(self):
        response = self.client.get(reverse("topic_summary"))

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"error": "not authenticated"})

    def test_topic_summary_rejects_non_get_requests(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("topic_summary"))

        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json(), {"error": "method not allowed"})

    def test_topic_summary_returns_empty_series_when_no_topics_exist(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("topic_summary"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "categories": [],
                "series": [
                    {
                        "name": "Topic as a Percent of Tweets",
                        "data": [],
                    }
                ],
            },
        )

    @patch("api.views._get_topic_summary", side_effect=Exception("boom"))
    def test_topic_summary_returns_500_when_summary_fails(self, mock_summary):
        self.client.force_login(self.user)

        response = self.client.get(reverse("topic_summary"))

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"error": "failed to load topic summary"})


class ImportDatasetTests(TestCase):
    def setUp(self):
        self.user = AppUser.objects.create(email="test@example.com")

    def test_import_dataset_rejects_empty_body(self):
        self.client.force_login(self.user)

        response = self.client.post(
            "/api/import-dataset/", data="", content_type="text/plain"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "empty request body"})
