import os
import pytest
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
from deepeval.test_case import LLMTestCase


pytestmark = pytest.mark.skipif(
    (os.getenv("RUN_DEEPEVAL", "0") != "1") or (not os.getenv("OPENAI_API_KEY")),
    reason="Set RUN_DEEPEVAL=1 and OPENAI_API_KEY to run DeepEval online metrics.",
)


def _print_eval_case(case_name: str, query: str, actual_output: str, retrieval_context: list[str]) -> None:
    """
    Verbose description for what DeepEval is judging.
    Use `pytest -s` to see this output.
    """
    print(f"\n[DeepEval] Case: {case_name}")
    print(f"[DeepEval] Query: {query}")
    print("[DeepEval] What is being judged:")
    print("  1) AnswerRelevancy -> Is the answer directly relevant to the user query?")
    print("  2) Faithfulness -> Is the answer grounded in retrieved incident context?")
    print(f"[DeepEval] Candidate answer: {actual_output}")
    print(f"[DeepEval] Retrieval context ({len(retrieval_context)} item(s)):")
    for idx, ctx in enumerate(retrieval_context, start=1):
        print(f"  - [{idx}] {ctx}")


@pytest.mark.parametrize(
    "case_name,query,actual_output,retrieval_context",
    [
        (
            "memory-leak-slowdown",
            "Our application runs fine after restart but slows down later. What might be causing this?",
            "Likely memory leak or connection leak. Check process memory growth, thread pool saturation, and recycle the impacted worker as a short-term fix.",
            ["Incident IM0000004: Closed. Root cause memory leak in worker process. Resolution: Restarted app pool and patched leak."],
        ),
        (
            "vpn-access-denied",
            "Users cannot access VPN from home though credentials are correct.",
            "Check VPN gateway health, certificate expiry, and MFA policy sync. Validate auth logs for denied reason and rotate expired certs if found.",
            ["Incident IM0001022: Closed. Root cause expired VPN certificate and MFA drift. Resolution: Renewed cert and synced policy."],
        ),
        (
            "db-lock-timeout",
            "Record update operations freeze and time out after 30 seconds.",
            "The most likely cause is DB lock contention during write bursts. Apply index tuning and resize the connection pool to stabilize updates.",
            ["Incident IM0002048: Closed. Root cause DB lock contention during write bursts. Resolution: index tuning and pool resize."],
        ),
        (
            "storage-threshold-upload-failure",
            "Media uploads are failing because storage is full. What should we do first?",
            "Archive old media files and expand the storage volume, then monitor free-space thresholds to prevent repeated upload failures.",
            [
                "Incident INC-5001: Disk Space Alert. Storage exceeded threshold causing upload failures. Solution: Archive old media files and expand storage volume."
            ],
        ),
        (
            "load-balancer-saturation-timeout",
            "The load balancer is overwhelmed and requests are timing out.",
            "Start with capacity and health checks on the load balancer tier, then tune routing and backend pool settings to reduce timeout pressure.",
            [
                "Incident INC-5012: Load balancer saturation during traffic spike. Solution: Scale LB instances, tune backend pool, and adjust timeout policy."
            ],
        ),
        (
            "encoding-crash-recovery",
            "Media encoding jobs crash during conversion.",
            "Restart the encoder service and update the codec library, then verify conversion stability on a controlled test batch.",
            [
                "Incident INC-5003: Encoding Crash during media conversion. Solution: Restart encoder service and update codec library."
            ],
        ),
    ],
    ids=[
        "memory-leak-slowdown",
        "vpn-access-denied",
        "db-lock-timeout",
        "storage-threshold-upload-failure",
        "load-balancer-saturation-timeout",
        "encoding-crash-recovery",
    ],
)
def test_resolution_quality(case_name, query, actual_output, retrieval_context):
    _print_eval_case(case_name, query, actual_output, retrieval_context)

    test_case = LLMTestCase(
        input=query,
        actual_output=actual_output,
        retrieval_context=retrieval_context,
    )

    relevancy_metric = AnswerRelevancyMetric(threshold=0.65, include_reason=True)
    faithfulness_metric = FaithfulnessMetric(threshold=0.65, include_reason=True)

    assert_test(test_case, [relevancy_metric, faithfulness_metric])
