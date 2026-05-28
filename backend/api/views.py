from api.forms import AppUserCreationForm
from api.models import LLMAnalysisRun
from api.services.feed_summary import build_feed_summary
from api.services.llm_analysis_runner import run_user_llm_analysis
from api.services.ingestion import ingest_posts
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Max
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from .models import (
    AppUser,
    BrowseSession,
    AnalysisStatus,
    TopicResult,
    Tweet,
    ViewedTweet,
)


# Because the ClearFeed Capture extension cannot get the CSRF token from Django,
# we use the @csrf_exempt decorator to tell Django to skip the CSRF check for
# this specific endpoint.
@csrf_exempt
def import_dataset(request):
    """
    POST /api/import-dataset/

    Receives raw NDJSON from the ClearFeed Capture browser extension and runs
    it through the ingestion pipeline. Requires the user to be logged in —
    the extension sends the session cookie via credentials: 'include'.

    Returns the session ID and post count on success.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"error": "not authenticated"}, status=401)

    platform = request.headers.get("X-Zeeschuimer-Platform", "unknown")
    user_agent = request.headers.get("User-Agent", None)
    body = request.body.decode("utf-8")

    try:
        session, post_count = ingest_posts(body, platform, user_agent, request.user)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        print(f"Ingestion failed: {e}")
        return JsonResponse({"error": "ingestion failed"}, status=500)

    return JsonResponse(
        {
            "status": "success",
            "session_id": str(session.id),
            "posts_received": post_count,
        }
    )


@csrf_exempt
def session_status(request, session_id):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "not authenticated"}, status=401)

    try:
        session = BrowseSession.objects.get(id=session_id, user=request.user)
    except BrowseSession.DoesNotExist:
        return JsonResponse({"error": "session not found"}, status=404)

    tweet_ids = (
        ViewedTweet.objects.filter(session=session)
        .values_list("tweet_id", flat=True)
        .distinct()
    )
    tweet_count = tweet_ids.count()
    status_counts = {
        item["analysis_status"]: item["count"]
        for item in Tweet.objects.filter(tweet_id__in=tweet_ids)
        .values("analysis_status")
        .annotate(count=Count("tweet_id", distinct=True))
    }

    pending_count = status_counts.get(AnalysisStatus.PENDING, 0)
    processing_count = status_counts.get(AnalysisStatus.PROCESSING, 0)
    complete_count = status_counts.get(AnalysisStatus.COMPLETE, 0)
    failed_count = status_counts.get(AnalysisStatus.FAILED, 0)
    analyzed_count = complete_count + failed_count
    progress = round((analyzed_count / tweet_count) * 100) if tweet_count else 0

    return JsonResponse(
        {
            "session_id": str(session.id),
            "status": session.status,
            "tweet_count": tweet_count,
            "pending_count": pending_count,
            "processing_count": processing_count,
            "complete_count": complete_count,
            "failed_count": failed_count,
            "progress": progress,
        }
    )


# ----------------------------------------------------------------------
# ADMIN/BACKGROUND views
# ----------------------------------------------------------------------


def home(request):
    if not request.user.is_authenticated:
        return redirect("landing")
    return render(request, "home.html")


def landing(request):
    return render(request, "landing.html")


def signup(request):
    if request.method == "POST":
        form = AppUserCreationForm(
            request.POST
        )  # pass in user data to custom AppUserCreationForm model

        if form.is_valid():
            user = form.save()

            login(request, user)  # automatically sign in user after sign up

            return redirect("onboarding")

    else:
        form = AppUserCreationForm()

    return render(request, "registration/signup.html", {"form": form})


def onboarding(request):
    return render(request, "onboarding.html", {})


def profile(request, user_id):
    user = AppUser.objects.filter(id=user_id)

    context = {
        "user": AppUser.objects.filter(id=user),
    }

    return render(request, "profile.html", context)


def privacy(request):
    return render(request, "privacy.html", {})


def topics_page(request):
    return render(request, "topics.html")


@login_required
def wordcloud_page(request):
    return render(request, "wordcloud.html")


def _resolve_analysis_user(request):
    if request.user.is_authenticated:
        return request.user, None

    user_id = request.session.get("user_id") or request.GET.get("user_id")
    if not user_id:
        return None, JsonResponse({"error": "not authenticated"}, status=401)

    try:
        return AppUser.objects.get(id=user_id), None
    except (AppUser.DoesNotExist, ValueError):
        return None, JsonResponse({"error": "user not found"}, status=404)


@csrf_exempt
def llm_analysis_runs(request):
    user, error_response = _resolve_analysis_user(request)
    if error_response:
        return error_response

    if request.method != "POST":
        return JsonResponse({"error": "method not allowed"}, status=405)

    sample_size = request.POST.get("sample_size", 10)
    seed = request.POST.get("seed")

    try:
        if seed in ("", None):
            seed = None
        else:
            seed = int(seed)
    except ValueError:
        return JsonResponse({"error": "invalid seed"}, status=400)

    try:
        run = run_user_llm_analysis(user, sample_size=sample_size, seed=seed)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    return JsonResponse(
        {
            "run_id": str(run.id),
            "status": run.status,
            "sample_size": run.sample_size,
        },
        status=201,
    )


@csrf_exempt
def llm_analysis_run_detail(request, run_id):
    user, error_response = _resolve_analysis_user(request)
    if error_response:
        return error_response

    try:
        run = LLMAnalysisRun.objects.get(id=run_id, user=user)
    except LLMAnalysisRun.DoesNotExist:
        return JsonResponse({"error": "run not found"}, status=404)

    return JsonResponse(
        {
            "run_id": str(run.id),
            "status": run.status,
            "sample_size": run.sample_size,
            "sample_seed": run.sample_seed,
            "model_name": run.model_name,
            "sample_metadata": run.sample_metadata,
            "result": run.result,
            "raw_output": run.raw_output,
            "error_message": run.error_message,
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "updated_at": run.updated_at.isoformat() if run.updated_at else None,
        }
    )


def _get_llm_reflection_summary(user):
    run = LLMAnalysisRun.objects.filter(user=user).order_by("-created_at").first()

    if not run:
        return {
            "status": "not_started",
            "reflection": "",
            "run_id": None,
        }

    reflection = ""
    if isinstance(run.result, dict):
        reflection = run.result.get("reflection", "") or ""

    return {
        "status": run.status,
        "reflection": reflection,
        "run_id": str(run.id),
        "model_name": run.model_name,
        "created_at": run.created_at.isoformat() if run.created_at else None,
    }


def _get_home_summary_stats(user):
    total_sessions = BrowseSession.objects.filter(user=user).count()
    total_tweets = (
        ViewedTweet.objects.filter(user=user).values("tweet_id").distinct().count()
    )
    last_session_at = (
        BrowseSession.objects.filter(user=user)
        .aggregate(last_session=Max("created_at"))
        .get("last_session")
    )
    days_since_last = (timezone.now() - last_session_at).days if last_session_at else 0

    return {
        "total_sessions": total_sessions,
        "total_tweets": total_tweets,
        "days_since_last": days_since_last,
    }


def topic_results(request, user_id=None):
    if user_id is None:
        user_id = request.session.get("user_id")

    try:
        user = AppUser.objects.get(id=user_id)
    except AppUser.DoesNotExist:
        return JsonResponse({"error": "user not found"}, status=404)

    context = {
        "user": user,
        "topic_results": TopicResult.objects.filter(tweet__viewedtweet__user=user),
    }
    return render(request, "topic_results.html", context)


def api_feed_summary(request):
    """
    GET /api/feed-summary/

    Returns the combined payload used by the scrollable feed analysis view.
    """
    user, error_response = _resolve_analysis_user(request)
    if error_response:
        return error_response

    return JsonResponse(
        {
            **build_feed_summary(user),
            "llm_analysis": _get_llm_reflection_summary(user),
        }
    )


def api_home_summary(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "not authenticated"}, status=401)

    return JsonResponse(
        {
            "summary_stats": _get_home_summary_stats(request.user),
        }
    )


def feed_summary(request):
    """
    Returns the actual feed summary page, which uses fetch to get the data from /api/feed-summary/.

    User check and data acquisition occurs in api_feed_summary.
    """
    return render(request, "user_scroll.html")
