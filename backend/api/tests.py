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

        response = self.client.get(
            reverse("topic_summary"), {"user_id": str(self.user.id)}
        )

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
