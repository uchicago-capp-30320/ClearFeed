from api.models import LLMAnalysisRun, LLMAnalysisStatus
from api.services.feed_summary import build_feed_summary
from api.services.llm_prompting import analyze_sampled_tweets
from api.services.llm_sampling import sample_user_tweets


def run_user_llm_analysis(user, sample_size=10, seed=None):
    """
    Orchestrate one user-level LLM analysis run.

    The runner owns persistence and status transitions. The sampling and
    prompt services stay reusable and testable on their own.
    """
    run = LLMAnalysisRun.objects.create(
        user=user,
        status=LLMAnalysisStatus.QUEUED,
        sample_size=sample_size,
        sample_seed=seed,
        model_name="",
        sample_metadata={},
    )

    run.status = LLMAnalysisStatus.PROCESSING
    run.save(update_fields=["status", "updated_at"])

    try:
        sampled_tweets = sample_user_tweets(user, sample_size=sample_size, seed=seed)
        if not sampled_tweets:
            raise ValueError("no tweets available for analysis")

        feed_summary = build_feed_summary(user)
        analysis_payload = analyze_sampled_tweets(
            sampled_tweets,
            feed_summary=feed_summary,
        )
        run.model_name = analysis_payload.get("model_name", "")
        run.sample_metadata = {
            "sample_size": len(sampled_tweets),
            "tweet_ids": [tweet["tweet_id"] for tweet in sampled_tweets],
            "prompt_context": {
                "feed_summary": feed_summary,
            },
        }
        run.raw_output = analysis_payload.get("raw_output", "")
        run.result = analysis_payload.get("analysis", {})
        run.status = LLMAnalysisStatus.COMPLETE
        run.error_message = None
        run.save(
            update_fields=[
                "model_name",
                "sample_metadata",
                "raw_output",
                "result",
                "status",
                "error_message",
                "updated_at",
            ]
        )
        return run
    except Exception as exc:
        run.status = LLMAnalysisStatus.FAILED
        run.error_message = str(exc)
        run.save(update_fields=["status", "error_message", "updated_at"])
        raise
