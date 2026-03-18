import os
import pytest
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
from deepeval.test_case import LLMTestCase


pytestmark = pytest.mark.skipif(
    (os.getenv("RUN_DEEPEVAL", "0") != "1") or (not os.getenv("OPENAI_API_KEY")),
    reason="Set RUN_DEEPEVAL=1 and OPENAI_API_KEY to run DeepEval online metrics.",
)


@pytest.mark.parametrize(
    "query,actual_output,retrieval_context",
    [
        (
            "Our application runs fine after restart but slows down later. What might be causing this?",
            "Likely memory leak or connection leak. Check process memory growth, thread pool saturation, and recycle the impacted worker as a short-term fix.",
            ["Incident IM0000004: Closed. Root cause memory leak in worker process. Resolution: Restarted app pool and patched leak."],
        ),
        (
            "Users cannot access VPN from home though credentials are correct.",
            "Check VPN gateway health, certificate expiry, and MFA policy sync. Validate auth logs for denied reason and rotate expired certs if found.",
            ["Incident IM0001022: Closed. Root cause expired VPN certificate and MFA drift. Resolution: Renewed cert and synced policy."],
        ),
        (
            "Record update operations freeze and time out after 30 seconds.",
            "The most likely cause is DB lock contention during write bursts. Apply index tuning and resize the connection pool to stabilize updates.",
            ["Incident IM0002048: Closed. Root cause DB lock contention during write bursts. Resolution: index tuning and pool resize."],
        ),
    ],
)
def test_resolution_quality(query, actual_output, retrieval_context):
    test_case = LLMTestCase(
        input=query,
        actual_output=actual_output,
        retrieval_context=retrieval_context,
    )

    relevancy_metric = AnswerRelevancyMetric(threshold=0.65)
    faithfulness_metric = FaithfulnessMetric(threshold=0.65)

    assert_test(test_case, [relevancy_metric, faithfulness_metric])
