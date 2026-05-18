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
from .services.llm_sampling import sample_user_tweets


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

    def test_feed_summary_accepts_session_user_id(self):
        self.client.logout()
        session = self.client.session
        session["user_id"] = str(self.user.id)
        session.save()

        response = self.client.get("/api/feed-summary/")

        self.assertEqual(response.status_code, 200)

    def test_feed_summary_accepts_query_user_id(self):
        self.client.logout()

        response = self.client.get("/api/feed-summary/", {"user_id": str(self.user.id)})

        self.assertEqual(response.status_code, 200)


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


class LlmSamplingTests(TestCase):
    def setUp(self):
        self.user = AppUser.objects.create()
        self.session = BrowseSession.objects.create(
            user=self.user,
            platform="x",
            user_agent="test-agent",
        )
        self.author = TwitterAuthor.objects.create(
            author_twitter_id="author-1",
            screen_name="alice",
            display_name="Alice",
        )

    def _add_tweet(self, tweet_id, text, author=None):
        tweet = Tweet.objects.create(
            tweet_id=tweet_id,
            author=author or self.author,
            full_text=text,
        )
        ViewedTweet.objects.create(
            user=self.user,
            session=self.session,
            tweet=tweet,
        )
        return tweet

    def test_sample_user_tweets_returns_all_when_fewer_than_target(self):
        self._add_tweet("tweet-1", "first tweet")
        self._add_tweet("tweet-2", "second tweet")
        self._add_tweet("tweet-3", "third tweet")
        self._add_tweet("tweet-4", "fourth tweet")

        sample = sample_user_tweets(self.user, sample_size=10, seed=7)

        self.assertEqual(len(sample), 4)
        self.assertTrue(
            all(
                item["tweet_id"] in {"tweet-1", "tweet-2", "tweet-3", "tweet-4"}
                for item in sample
            )
        )
        self.assertTrue(all("text" in item for item in sample))

    def test_sample_user_tweets_caps_sample_at_target_size(self):
        for index in range(12):
            self._add_tweet(f"tweet-{index}", f"tweet {index}")

        sample = sample_user_tweets(self.user, sample_size=10, seed=7)

        self.assertEqual(len(sample), 10)

    def test_sample_user_tweets_is_user_scoped(self):
        other_user = AppUser.objects.create(email="other@example.com")
        other_session = BrowseSession.objects.create(
            user=other_user,
            platform="x",
            user_agent="test-agent",
        )
        other_author = TwitterAuthor.objects.create(
            author_twitter_id="author-2",
            screen_name="bob",
            display_name="Bob",
        )
        tweet = Tweet.objects.create(
            tweet_id="other-tweet",
            author=other_author,
            full_text="other person's tweet",
        )
        ViewedTweet.objects.create(
            user=other_user,
            session=other_session,
            tweet=tweet,
        )
        self._add_tweet("tweet-1", "first tweet")

        sample = sample_user_tweets(self.user, sample_size=10, seed=1)

        self.assertEqual(len(sample), 1)
        self.assertEqual(sample[0]["tweet_id"], "tweet-1")
