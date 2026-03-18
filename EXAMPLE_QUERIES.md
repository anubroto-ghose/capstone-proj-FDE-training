1. **Slow system / performance degradation**  
Main query:  
`The system is very slow this morning. Pages are timing out intermittently. What should we check first?`  
Sub-queries:
- `Find similar incidents for system slowdown and intermittent timeout`
- `Filter incidents with priority P1 or P2 and impact high`
- `What closure codes were used in similar resolved incidents?`
- `Predict resolution time for performance category and high priority`
- `Validate proposed fix steps before final response`

2. **Database timeout and app freeze**  
Main query:  
`Users report app freeze while updating records, then request timeout errors appear.`  
Sub-queries:
- `Search incidents related to DB timeout during update operations`
- `Filter category Database and impact medium/high`
- `Retrieve incidents with successful resolution summaries for DB lock/contention`
- `Assess fix accuracy for restart + query optimization + connection pool tuning`
- `Escalate to L2 if root cause unclear after initial triage`

3. **VPN / remote access denied**  
Main query:  
`Remote users cannot connect to company network today though credentials are correct.`  
Sub-queries:
- `Find incidents for VPN access denied with valid credentials`
- `Filter category Network and priority P2/P3`
- `Check incidents involving expired certificates or MFA misconfiguration`
- `Predict resolution time for network access incident`
- `If repeated failures across users, handoff for RCA`

4. **Restart temporarily fixes issue**  
Main query:  
`After restart the app works, but after a few hours it becomes unresponsive again.`  
Sub-queries:
- `Find recurring incidents where restart gives temporary relief`
- `Search for memory leak, thread exhaustion, or connection leak patterns`
- `Filter by resolved incidents and compare recency-ranked results`
- `Generate probable root cause + permanent remediation steps`
- `Validate remediation plan via judge tool`

5. **Auth failures after deployment**  
Main query:  
`After today’s deployment, many users get login failures and token errors.`  
Sub-queries:
- `Find incidents with authentication failures post release`
- `Filter category Security/Auth and high impact`
- `Check for JWT secret mismatch, clock skew, session invalidation patterns`
- `Estimate fix time and confidence score`
- `Escalate to L2 if cross-service config mismatch is suspected`

6. **Email queue backlog / delayed notifications**  
Main query:  
`Notification emails are delayed by 30-40 minutes and queue size keeps increasing.`  
Sub-queries:
- `Search incidents for queue backlog and delayed notification processing`
- `Filter category Middleware/Integration`
- `Find fixes involving worker scaling, retry policy, dead-letter queues`
- `Assess fix accuracy for worker autoscaling + queue partitioning`
- `Request RCA if backlog recurs after short-term fix`

7. **Disk space and service crash**  
Main query:  
`One server keeps crashing and logs show low disk space warnings before failure.`  
Sub-queries:
- `Find incidents with disk exhaustion preceding service crash`
- `Filter impact high and category Infrastructure`
- `Retrieve resolution summaries involving log rotation and cleanup automation`
- `Predict resolution time for infra-critical issue`
- `Validate runbook safety before execution`

8. **Inter-service API 5xx spike**  
Main query:  
`Since noon, service A calling service B is seeing many 502/503 errors.`  
Sub-queries:
- `Find incidents with downstream dependency 502/503 spikes`
- `Filter by recent incidents and high success-rate resolutions`
- `Check fixes related to circuit breaker, timeout config, connection pool`
- `Estimate resolution time and confidence`
- `Escalate to RCA for systemic architecture bottleneck`

9. **Configuration drift / environment mismatch**  
Main query:  
`Staging works fine but production fails with config-related errors after restart.`  
Sub-queries:
- `Search incidents involving prod-only config drift`
- `Filter category Configuration and impact medium/high`
- `Find fixes involving env var sync, secrets rotation, config version pinning`
- `Validate change plan before rollout`
- `Handoff to L2 for deep config dependency analysis`

10. **Intermittent DNS/network resolution failures**  
Main query:  
`Services randomly fail to resolve hostnames for a few seconds, then recover.`  
Sub-queries:
- `Find incidents with intermittent DNS resolution failures`
- `Filter category Network with recurring incident pattern`
- `Retrieve fixes involving DNS cache, resolver failover, TTL adjustments`
- `Assess confidence in proposed DNS remediation`
- `Escalate to RCA if failures persist across multiple clusters`

Use these to test:
- L1 triage quality
- metadata filtering
- hybrid retrieval relevance
- L1 → L2 → RCA handoffs
- judge validation + metrics tools
- feedback loop after each assistant response
