from django.test import TestCase, SimpleTestCase
from unittest.mock import patch, call
from datetime import datetime, timezone as dt_timezone
from api.models import (
    AppUser,
    BrowseSession,
    TwitterAuthor,
    Tweet,
    AnalysisStatus,
    TweetMedia,
    ViewedTweet,
)
from api.services.ingestion import (
    _parse_ndjson,
    _upsert_authors,
    _insert_tweets,
    _insert_media,
    _insert_viewed_tweet,
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
            posts,
            [
                {"item_id": "123", "data": {}},
                {"item_id": "789", "data": {}},
            ],  # skips non-JSON line
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

    # mock Tweet JSON builder
    def make_post(
        self,
        tweet_id="123",
        author_id="456",
        screen_name="testuser",
        full_text="hello world",
        media_key="987",
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
                    "extended_entities": {
                        "media": [
                            {
                                "media_key": media_key,
                                "type": "video",
                                "media_url_https": "https://pbs.twimg.com/media/test.jpg",
                                "original_info": {
                                    "width": 1920,
                                    "height": 1080,
                                },
                                "video_info": {
                                    "duration_millis": 15000,
                                    "variants": [
                                        {
                                            "bitrate": 256000,
                                            "content_type": "video/mp4",
                                            "url": "https://video.twimg.com/test_256.mp4",
                                        }
                                    ],
                                },
                            }
                        ]
                    },
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
        """Basic test for ingesting new Tweet authors into DB."""
        posts = [
            self.make_post(tweet_id="1968", author_id="1901"),
            self.make_post(tweet_id="500", author_id="501"),
        ]

        _upsert_authors(posts)

        self.assertTrue(TwitterAuthor.objects.filter(author_twitter_id="1901").exists())
        self.assertTrue(TwitterAuthor.objects.filter(author_twitter_id="501").exists())

    def test_upsert_authors_duplicate_author(self):
        """Test for updating existing author information in DB."""
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

    def test_upsert_authors_incomplete_post(self):
        """Test for avoiding insertion of incomplete author data into DB."""
        posts = [
            self.make_post(tweet_id="1968", author_id=None),
            self.make_post(tweet_id="500", author_id="501"),
        ]

        _upsert_authors(posts)

        self.assertEqual(TwitterAuthor.objects.count(), 1)
        self.assertTrue(TwitterAuthor.objects.filter(author_twitter_id="501").exists())
        self.assertFalse(
            TwitterAuthor.objects.filter(author_twitter_id="1901").exists()
        )

    @patch("api.services.ingestion._insert_viewed_tweet")
    @patch("api.services.ingestion._insert_media")
    def test_insert_tweets_basic(
        self,
        mock_insert_media,
        mock_insert_viewed_tweet,
    ):
        """Integration test for ingesting new Tweet data into DB."""
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
        mock_insert_media.assert_has_calls(
            expected_media_calls
        )  # confirm other functions called as expected

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

    @patch("api.services.ingestion._insert_viewed_tweet")
    @patch("api.services.ingestion._insert_media")
    def test_insert_tweets_duplicate(
        self,
        mock_insert_media,
        mock_insert_viewed_tweet,
    ):
        """Integration test for ingesting duplicate Tweet data into DB."""
        Tweet.objects.create(
            tweet_id="23",
            conversation_id="1234567890",
            full_text="Lebron > MJ",
            lang="fr",
            source_platform_url="https://x.com/test/status/1234567890",
            tweet_created_at=datetime.strptime(
                "Fri Jul 22 16:50:20 +0000 2022", "%a %b %d %H:%M:%S +0000 %Y"
            ).replace(tzinfo=dt_timezone.utc),
        )

        # duplicate of existing tweet in db
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

        # duplicate tweet should be consistent with original value when inserted
        self.assertEqual(tweet_one.full_text, "Lebron > MJ")
        self.assertEqual(tweet_one.lang, "fr")

        self.assertEqual(tweet_one.analysis_status, AnalysisStatus.PENDING)

        tweet_two = Tweet.objects.get(tweet_id="99")

        # new tweets should ingest as expected
        self.assertIsNotNone(tweet_two)
        self.assertEqual(tweet_two.full_text, "I'm Kendrick Perkins")
        self.assertEqual(tweet_two.hashtags, ["test"])
        self.assertEqual(tweet_two.analysis_status, AnalysisStatus.PENDING)

        self.assertEqual(mock_insert_media.call_count, 2)
        self.assertEqual(mock_insert_viewed_tweet.call_count, 2)

        # media and viewed tweet calls should function as normal
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

    @patch("api.services.ingestion._insert_viewed_tweet")
    @patch("api.services.ingestion._insert_media")
    def test_insert_tweets_incomplete_post(
        self,
        mock_insert_media,
        mock_insert_viewed_tweet,
    ):
        """Integration test for avoiding ingestion of incomplete Tweet data into DB."""
        post_one = self.make_post(
            tweet_id=None,
            author_id="23",
            screen_name="Michael Jordan",
            full_text="I'm the GOAT",
        )  # incomplete Tweet info, invalid
        post_two = self.make_post(
            tweet_id="99",
            author_id="99",
            screen_name="Kendrick Perkins",
            full_text="I'm Kendrick Perkins",
        )
        posts = [post_one, post_two]

        _insert_tweets(posts, self.user, self.session)

        # Incomplete tweet not ingested, only valid tweet in db
        self.assertEqual(Tweet.objects.count(), 1)

        tweet_two = Tweet.objects.get(tweet_id="99")

        self.assertIsNotNone(tweet_two)
        self.assertEqual(tweet_two.full_text, "I'm Kendrick Perkins")
        self.assertEqual(tweet_two.hashtags, ["test"])
        self.assertEqual(tweet_two.analysis_status, AnalysisStatus.PENDING)

        # media and viewed tweet calls only for valid post
        self.assertEqual(mock_insert_media.call_count, 1)
        self.assertEqual(mock_insert_viewed_tweet.call_count, 1)

        expected_media_calls = [call(post_two, tweet_two)]
        mock_insert_media.assert_has_calls(expected_media_calls)

        expected_viewed_calls = [
            call(
                post_two,
                post_two["data"]["legacy"],
                tweet_two,
                self.user,
                self.session,
            )
        ]
        mock_insert_viewed_tweet.assert_has_calls(expected_viewed_calls)

    def test_insert_media_basic(self):
        """Basic test for ingesting Tweet media data into DB."""

        # instantiate tweet objects to be used as valid foreign key for media insertion
        tweet_one = Tweet.objects.create(
            tweet_id="1968",
            conversation_id="1234567890",
            full_text="Lebron > MJ",
            lang="fr",
            source_platform_url="https://x.com/test/status/1234567890",
            tweet_created_at=datetime.strptime(
                "Fri Jul 22 16:50:20 +0000 2022", "%a %b %d %H:%M:%S +0000 %Y"
            ).replace(tzinfo=dt_timezone.utc),
        )
        tweet_two = Tweet.objects.create(
            tweet_id="500",
            conversation_id="1234567890",
            full_text="Jeremy Lin is the GOAT",
            lang="en",
            source_platform_url="https://x.com/test/status/1234567890",
            tweet_created_at=datetime.strptime(
                "Fri Jul 22 16:50:20 +0000 2022", "%a %b %d %H:%M:%S +0000 %Y"
            ).replace(tzinfo=dt_timezone.utc),
        )

        post_one = self.make_post(tweet_id="1968", media_key="777")
        post_two = self.make_post(tweet_id="500", media_key="000")

        _insert_media(post_one, tweet_one)
        _insert_media(post_two, tweet_two)

        self.assertEqual(TweetMedia.objects.count(), 2)
        self.assertTrue(TweetMedia.objects.filter(media_key="777").exists())
        self.assertTrue(TweetMedia.objects.filter(media_key="000").exists())

    def test_insert_media_duplicate(self):
        """Test for ingesting duplicate Tweet media data into DB."""

        # instantiate tweet objects to be used as valid foreign key for media insertion
        tweet_one = Tweet.objects.create(
            tweet_id="1968",
            conversation_id="1234567890",
            full_text="Lebron > MJ",
            lang="fr",
            source_platform_url="https://x.com/test/status/1234567890",
            tweet_created_at=datetime.strptime(
                "Fri Jul 22 16:50:20 +0000 2022", "%a %b %d %H:%M:%S +0000 %Y"
            ).replace(tzinfo=dt_timezone.utc),
        )
        tweet_two = Tweet.objects.create(
            tweet_id="500",
            conversation_id="1234567890",
            full_text="Jeremy Lin is the GOAT",
            lang="en",
            source_platform_url="https://x.com/test/status/1234567890",
            tweet_created_at=datetime.strptime(
                "Fri Jul 22 16:50:20 +0000 2022", "%a %b %d %H:%M:%S +0000 %Y"
            ).replace(tzinfo=dt_timezone.utc),
        )

        post_one = self.make_post(tweet_id="1968", media_key="777")

        # media shouldn't be created for duplicate
        post_two = self.make_post(tweet_id="500", media_key="777")

        _insert_media(post_one, tweet_one)
        _insert_media(post_two, tweet_two)

        self.assertEqual(
            TweetMedia.objects.count(), 1
        )  # only one item, no duplicate insertion
        self.assertTrue(TweetMedia.objects.filter(media_key="777").exists())

    def test_insert_media_incomplete_post(self):
        """Test for avoiding ingestion of incomplete Tweet media data into DB."""

        # instantiate tweet objects to be used as valid foreign key for media insertion
        tweet_one = Tweet.objects.create(
            tweet_id="1968",
            conversation_id="1234567890",
            full_text="Lebron > MJ",
            lang="fr",
            source_platform_url="https://x.com/test/status/1234567890",
            tweet_created_at=datetime.strptime(
                "Fri Jul 22 16:50:20 +0000 2022", "%a %b %d %H:%M:%S +0000 %Y"
            ).replace(tzinfo=dt_timezone.utc),
        )
        tweet_two = Tweet.objects.create(
            tweet_id="500",
            conversation_id="1234567890",
            full_text="Jeremy Lin is the GOAT",
            lang="en",
            source_platform_url="https://x.com/test/status/1234567890",
            tweet_created_at=datetime.strptime(
                "Fri Jul 22 16:50:20 +0000 2022", "%a %b %d %H:%M:%S +0000 %Y"
            ).replace(tzinfo=dt_timezone.utc),
        )

        # media shouldn't be created for incomplete post
        post_one = self.make_post(tweet_id="1968", media_key=None)

        post_two = self.make_post(tweet_id="500", media_key="777")

        _insert_media(post_one, tweet_one)
        _insert_media(post_two, tweet_two)

        self.assertEqual(TweetMedia.objects.count(), 1)
        self.assertTrue(TweetMedia.objects.filter(media_key="777").exists())

    def test_insert_viewed_tweet_basic(self):
        """Basic test for creating new ViewedTweet object in DB."""
        tweet_one = Tweet.objects.create(
            tweet_id="1968",
            conversation_id="1234567890",
            full_text="Lebron > MJ",
            lang="fr",
            source_platform_url="https://x.com/test/status/1234567890",
            tweet_created_at=datetime.strptime(
                "Fri Jul 22 16:50:20 +0000 2022", "%a %b %d %H:%M:%S +0000 %Y"
            ).replace(tzinfo=dt_timezone.utc),
        )
        tweet_two = Tweet.objects.create(
            tweet_id="500",
            conversation_id="1234567890",
            full_text="Jeremy Lin is the GOAT",
            lang="en",
            source_platform_url="https://x.com/test/status/1234567890",
            tweet_created_at=datetime.strptime(
                "Fri Jul 22 16:50:20 +0000 2022", "%a %b %d %H:%M:%S +0000 %Y"
            ).replace(tzinfo=dt_timezone.utc),
        )

        post_one = self.make_post(tweet_id="1968", media_key="777")
        post_two = self.make_post(tweet_id="500", media_key="000")

        legacy_one = post_one.get("data", {}).get("legacy", {})
        legacy_two = post_two.get("data", {}).get("legacy", {})

        _insert_viewed_tweet(post_one, legacy_one, tweet_one, self.user, self.session)
        _insert_viewed_tweet(post_two, legacy_two, tweet_two, self.user, self.session)

        self.assertEqual(ViewedTweet.objects.count(), 2)
        self.assertTrue(ViewedTweet.objects.filter(tweet=tweet_one).exists())
        self.assertTrue(ViewedTweet.objects.filter(tweet=tweet_two).exists())

    def test_insert_viewed_tweet_duplicate(self):
        """Basic test for creating multiple ViewedTweet objects that reference same Tweet in DB."""
        tweet_one = Tweet.objects.create(
            tweet_id="1968",
            conversation_id="1234567890",
            full_text="Lebron > MJ",
            lang="fr",
            source_platform_url="https://x.com/test/status/1234567890",
            tweet_created_at=datetime.strptime(
                "Fri Jul 22 16:50:20 +0000 2022", "%a %b %d %H:%M:%S +0000 %Y"
            ).replace(tzinfo=dt_timezone.utc),
        )

        post_one = self.make_post(tweet_id="1968", media_key="777")

        legacy_one = post_one.get("data", {}).get("legacy", {})

        # replicate same tweet being viewed twice, create two ViewedTweet
        _insert_viewed_tweet(post_one, legacy_one, tweet_one, self.user, self.session)
        _insert_viewed_tweet(post_one, legacy_one, tweet_one, self.user, self.session)

        # both duplicates recorded in system
        self.assertEqual(ViewedTweet.objects.count(), 2)
        self.assertTrue(ViewedTweet.objects.filter(tweet=tweet_one).exists())
