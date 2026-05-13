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


class TopicSummaryTests(TestCase):
    def setUp(self):
        self.user = AppUser.objects.create()
        self.session = BrowseSession.objects.create(
            user=self.user,
            platform="x",
            user_agent="test-agent",
        )
        self.client.force_login(self.user)

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

        response = self.client.get("/api/topics-summary/")

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
        self.client.logout()

        response = self.client.get("/api/topics-summary/")

        self.assertEqual(response.status_code, 401)


class WordcloudSummaryTests(TestCase):
    def setUp(self):
        self.user = AppUser.objects.create()
        self.other_user = AppUser.objects.create(email="other@example.com")
        self.session = BrowseSession.objects.create(
            user=self.user,
            platform="x",
            user_agent="test-agent",
        )
        self.other_session = BrowseSession.objects.create(
            user=self.other_user,
            platform="x",
            user_agent="test-agent",
        )
        self.client.force_login(self.user)

    def _add_tweet(self, tweet_id, text, user=None, session=None):
        user = user or self.user
        session = session or self.session
        tweet = Tweet.objects.create(tweet_id=tweet_id, full_text=text)
        ViewedTweet.objects.create(
            user=user,
            session=session,
            tweet=tweet,
        )

    def test_wordcloud_summary_returns_top_words(self):
        self._add_tweet(
            "tweet-1",
            "Climate climate policy future future future https://example.com @user",
        )
        self._add_tweet("tweet-2", "Policy science science climate and the future")
        self._add_tweet(
            "other-tweet",
            "unrelated unrelated unrelated",
            self.other_user,
            self.other_session,
        )

        response = self.client.get(reverse("wordcloud_summary"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "word": ["future", "climate", "policy", "science"],
                "series": [
                    {
                        "name": "Frequency",
                        "data": [4, 3, 2, 2],
                    }
                ],
            },
        )

    def test_wordcloud_summary_returns_empty_payload_without_tweets(self):
        response = self.client.get(reverse("wordcloud_summary"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "word": [],
                "series": [
                    {
                        "name": "Frequency",
                        "data": [],
                    }
                ],
            },
        )

    def test_wordcloud_summary_requires_authentication(self):
        self.client.logout()

        response = self.client.get(reverse("wordcloud_summary"))

        self.assertEqual(response.status_code, 401)


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
