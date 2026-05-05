from django.test import TestCase

from api.models import AppUser, BrowseSession, Tweet, TwitterAuthor, ViewedTweet
from api.services.ingestion import HARDCODED_USER_ID


class UserSummaryEndpointTests(TestCase):
    def setUp(self):
        self.user = AppUser.objects.create(id=HARDCODED_USER_ID)
        self.session = BrowseSession.objects.create(
            user=self.user,
            platform="twitter",
            user_agent="pytest",
        )

        authors = [
            ("top_user_one", 4, 2),
            ("top_user_two", 2, 1),
            ("top_user_three", 2, 0),
            ("top_user_four", 1, 1),
            ("top_user_five", 1, 0),
        ]

        tweet_number = 1
        for screen_name, tweet_count, promoted_count in authors:
            author = TwitterAuthor.objects.create(
                author_twitter_id=f"author-{screen_name}",
                screen_name=screen_name,
            )

            for promoted in [True] * promoted_count + [False] * (
                tweet_count - promoted_count
            ):
                tweet = Tweet.objects.create(
                    tweet_id=f"tweet-{tweet_number}",
                    author=author,
                    promoted=promoted,
                )
                ViewedTweet.objects.create(
                    user=self.user,
                    session=self.session,
                    tweet=tweet,
                )
                tweet_number += 1

    def test_user_summary_endpoint_returns_expected_payload(self):
        response = self.client.get("/api/promoted/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "top_users": [
                    "top_user_one",
                    "top_user_two",
                    "top_user_three",
                    "top_user_four",
                    "top_user_five",
                ],
                "total_tweets": 10,
                "since_date": self.user.created_at.date().isoformat(),
                "promoted_percentage": 40,
            },
        )
