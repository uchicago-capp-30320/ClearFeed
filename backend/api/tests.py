from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse

from .models import (
    AnalysisStatus,
    AppUser,
    BrowseSession,
    TopicResult,
    Tweet,
    ViewedTweet,
)


class SessionStatusTests(TestCase):
    def setUp(self):
        self.user = AppUser.objects.create()
        self.other_user = AppUser.objects.create()
        self.session = BrowseSession.objects.create(
            user=self.user,
            platform="x",
            user_agent="test-agent",
        )
        self.client.force_login(self.user)

    def _add_tweet(self, tweet_id, status):
        tweet = Tweet.objects.create(
            tweet_id=tweet_id,
            full_text=f"{tweet_id} text",
            analysis_status=status,
        )
        ViewedTweet.objects.create(
            user=self.user,
            session=self.session,
            tweet=tweet,
        )

    def test_session_status_returns_progress(self):
        self._add_tweet("tweet-1", AnalysisStatus.PENDING)
        self._add_tweet("tweet-2", AnalysisStatus.PROCESSING)
        self._add_tweet("tweet-3", AnalysisStatus.COMPLETE)
        self._add_tweet("tweet-4", AnalysisStatus.FAILED)

        response = self.client.get(
            reverse("session_status", kwargs={"session_id": self.session.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "session_id": str(self.session.id),
                "status": "queued",
                "tweet_count": 4,
                "pending_count": 1,
                "processing_count": 1,
                "complete_count": 1,
                "failed_count": 1,
                "progress": 50,
            },
        )

    def test_session_status_rejects_other_users_sessions(self):
        other_session = BrowseSession.objects.create(
            user=self.other_user,
            platform="x",
            user_agent="test-agent",
        )

        response = self.client.get(
            reverse("session_status", kwargs={"session_id": other_session.id})
        )

        self.assertEqual(response.status_code, 404)

    def test_session_status_requires_authentication(self):
        self.client.logout()

        response = self.client.get(
            reverse("session_status", kwargs={"session_id": self.session.id})
        )

        self.assertEqual(response.status_code, 401)


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
