from django.test import TestCase, SimpleTestCase
from unittest.mock import patch, call
from datetime import datetime, timezone as dt_timezone
from api.models import (
    AppUser,
    BrowseSession,
    TwitterAuthor,
    Tweet,
    AnalysisStatus,
)
from api.services.ingestion import (
    _parse_ndjson,
    _upsert_authors,
    _insert_tweets,
)


class TestParseNdjson(SimpleTestCase):
    def test_parse_ndjson_basic(self):
        """Basic test for ndjson parsing functionality."""
        body = '{"item_id":"123", "data":{}, "id":67}\n{"item_id":"456", "data":{"core":{}}}\n{"item_id":"789", "data":{}}\n'
        posts = _parse_ndjson(body)
        self.assertEqual(
            posts,
            [
                {"item_id": "123", "data": {}, "id": 67},
                {"item_id": "456", "data": {"core": {}}},
                {"item_id": "789", "data": {}},
            ],
        )

    def test_parse_ndjson_skip_bad_lines(self):
        """Test ndjson parsing with non-json data."""
        body = '{"item_id":"123", "data":{}}\nheyman%%%heyman%%%\n{"item_id":"789", "data":{}}\n'
        posts = _parse_ndjson(body)
        self.assertEqual(
            posts, [{"item_id": "123", "data": {}}, {"item_id": "789", "data": {}}]
        )


class TestIngestion(TestCase):
    def setUp(self):
        self.user = AppUser.objects.create_user(
            email="test@example.com", password="password123"
        )

        self.session = BrowseSession.objects.create(
            user=self.user,
            platform="x",
            user_agent="test-agent",
        )

    def make_post(
        self,
        tweet_id="123",
        author_id="456",
        screen_name="testuser",
        full_text="hello world",
    ):
        return {
            "timestamp_collected": "1776105301128",
            "source_platform_url": "https://x.com/test/status/123",
            "data": {
                "core": {
                    "user_results": {
                        "result": {
                            "rest_id": author_id,
                            "core": {
                                "screen_name": screen_name,
                                "name": "Test User",
                                "created_at": "Fri Jul 22 16:50:20 +0000 2011",
                            },
                            "legacy": {
                                "description": "bio",
                                "followers_count": 100,
                                "friends_count": 50,
                                "statuses_count": 1000,
                            },
                            "location": {"location": "Miami, FL"},
                            "is_blue_verified": False,
                        }
                    }
                },
                "legacy": {
                    "id_str": tweet_id,
                    "conversation_id_str": tweet_id,
                    "created_at": "Fri Jul 22 16:50:20 +0000 2022",
                    "full_text": full_text,
                    "entities": {"hashtags": [{"text": "test"}]},
                    "lang": "en",
                    "favorite_count": 10,
                    "retweet_count": 2,
                    "reply_count": 1,
                    "quote_count": 0,
                    "bookmark_count": 3,
                },
                "views": {"count": "100"},
            },
        }

    def test_upsert_authors_new_author(self):
        posts = [
            self.make_post(tweet_id="1968", author_id="1901"),
            self.make_post(tweet_id="500", author_id="501"),
        ]

        _upsert_authors(posts)

        self.assertTrue(TwitterAuthor.objects.filter(author_twitter_id="1901").exists())
        self.assertTrue(TwitterAuthor.objects.filter(author_twitter_id="501").exists())

    def test_upsert_authors_duplicate_author(self):
        TwitterAuthor.objects.create(
            author_twitter_id="1",
            screen_name="Joshua Zirkzee",
            display_name="jzirk",
            bio="bio",
            location="Manchester, UK",
            followers_count=100,
            following_count=100,
            statuses_count=1,
            is_blue_verified=True,
            account_created_at=datetime.strptime(
                "Fri Jul 22 16:50:20 +0000 2022", "%a %b %d %H:%M:%S +0000 %Y"
            ).replace(tzinfo=dt_timezone.utc),
        )

        posts = [
            self.make_post(tweet_id="1", author_id="1", screen_name="Bruno Fernandes")
        ]

        _upsert_authors(posts)
        test_author = TwitterAuthor.objects.get(author_twitter_id="1")

        self.assertIsNotNone(test_author)
        self.assertTrue(test_author.screen_name == "Bruno Fernandes")

    @patch("api.services.ingestion._insert_viewed_tweet")
    @patch("api.services.ingestion._insert_media")
    def test_insert_tweets_basic(
        self,
        mock_insert_media,
        mock_insert_viewed_tweet,
    ):
        post_one = self.make_post(
            tweet_id="23",
            author_id="23",
            screen_name="Michael Jordan",
            full_text="I'm the GOAT",
        )
        post_two = self.make_post(
            tweet_id="99",
            author_id="99",
            screen_name="Kendrick Perkins",
            full_text="I'm Kendrick Perkins",
        )
        posts = [post_one, post_two]

        _insert_tweets(posts, self.user, self.session)

        tweet_one = Tweet.objects.get(tweet_id="23")

        self.assertIsNotNone(tweet_one)
        self.assertEqual(tweet_one.full_text, "I'm the GOAT")
        self.assertEqual(tweet_one.hashtags, ["test"])
        self.assertEqual(tweet_one.analysis_status, AnalysisStatus.PENDING)

        tweet_two = Tweet.objects.get(tweet_id="99")

        self.assertIsNotNone(tweet_two)
        self.assertEqual(tweet_two.full_text, "I'm Kendrick Perkins")
        self.assertEqual(tweet_two.hashtags, ["test"])
        self.assertEqual(tweet_two.analysis_status, AnalysisStatus.PENDING)

        self.assertEqual(mock_insert_media.call_count, 2)
        self.assertEqual(mock_insert_viewed_tweet.call_count, 2)

        expected_media_calls = [
            call(post_one, tweet_one),
            call(post_two, tweet_two),
        ]
        mock_insert_media.assert_has_calls(expected_media_calls)

        expected_viewed_calls = [
            call(
                post_one,
                post_one["data"]["legacy"],
                tweet_one,
                self.user,
                self.session,
            ),
            call(
                post_two,
                post_two["data"]["legacy"],
                tweet_two,
                self.user,
                self.session,
            ),
        ]
        mock_insert_viewed_tweet.assert_has_calls(expected_viewed_calls)
