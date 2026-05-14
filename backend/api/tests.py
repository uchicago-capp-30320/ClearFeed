from django.test import TestCase
from django.urls import reverse

from .models import (
    AnalysisStatus,
    AppUser,
    BrowseSession,
    SentimentResult,
    TopicResult,
    TwitterAuthor,
    Tweet,
    ViewedTweet,
)


class FeedSummaryTests(TestCase):
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
        self.author = TwitterAuthor.objects.create(
            author_twitter_id="author-1",
            screen_name="promoted_user",
            display_name="Promoted User",
        )
        self.client.force_login(self.user)

    def _add_tweet(
        self,
        tweet_id,
        text,
        topic,
        sentiment,
        promoted=False,
        author=None,
        user=None,
        session=None,
    ):
        user = user or self.user
        session = session or self.session
        tweet = Tweet.objects.create(
            tweet_id=tweet_id,
            author=author,
            full_text=text,
            promoted=promoted,
        )
        TopicResult.objects.create(tweet=tweet, topic=topic)
        SentimentResult.objects.create(tweet=tweet, sentiment=sentiment)
        ViewedTweet.objects.create(
            user=user,
            session=session,
            tweet=tweet,
        )
        return tweet

    def test_feed_summary_combines_scrollable_payload(self):
        self._add_tweet(
            "tweet-1",
            "Future climate policy future",
            "cats",
            "positive",
            promoted=True,
            author=self.author,
        )
        self._add_tweet(
            "tweet-2",
            "Climate science future",
            "politics",
            "negative",
        )
        self._add_tweet(
            "tweet-3",
            "Policy science future",
            "cats",
            "neutral",
        )
        self._add_tweet(
            "other-tweet",
            "unrelated unrelated unrelated",
            "noise",
            "positive",
            user=self.other_user,
            session=self.other_session,
        )

        response = self.client.get("/api/feed-summary/")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(
            payload["overview"],
            {
                "top_users": ["promoted_user"],
                "total_tweets": 3,
                "since_date": payload["overview"]["since_date"],
                "promoted_percentage": 33,
            },
        )
        self.assertRegex(payload["overview"]["since_date"], r"^\d{4}-\d{2}-\d{2}$")
        self.assertEqual(
            payload["categories"],
            {
                "labels": ["Cats", "Politics"],
                "series": [
                    {
                        "name": "Topic as a Percent of Tweets",
                        "data": [67, 33],
                    }
                ],
            },
        )
        self.assertEqual(
            payload["word_frequency"],
            {
                "labels": ["future", "climate", "policy", "science"],
                "series": [
                    {
                        "name": "Frequency",
                        "data": [4, 2, 2, 2],
                    }
                ],
            },
        )
        self.assertEqual(
            payload["sentiment"],
            {
                "sentiment_average": 0.0,
                "labels": ["Negative", "Neutral", "Positive"],
                "series": [
                    {
                        "name": "Percentage of Tweets",
                        "data": [33, 33, 33],
                    }
                ],
            },
        )

    def test_feed_summary_returns_empty_payload_without_tweets(self):
        response = self.client.get("/api/feed-summary/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "overview": {
                    "top_users": [],
                    "total_tweets": 0,
                    "since_date": "",
                    "promoted_percentage": 0,
                },
                "categories": {
                    "labels": [],
                    "series": [
                        {
                            "name": "Topic as a Percent of Tweets",
                            "data": [],
                        }
                    ],
                },
                "word_frequency": {
                    "labels": [],
                    "series": [
                        {
                            "name": "Frequency",
                            "data": [],
                        }
                    ],
                },
                "sentiment": {
                    "sentiment_average": 0,
                    "labels": ["Negative", "Neutral", "Positive"],
                    "series": [
                        {
                            "name": "Percentage of Tweets",
                            "data": [0, 0, 0],
                        }
                    ],
                },
            },
        )

    def test_feed_summary_requires_authentication(self):
        self.client.logout()

        response = self.client.get("/api/feed-summary/")

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
