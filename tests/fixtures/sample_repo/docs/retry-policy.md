# Webhook Delivery Retry Policy

Outbound webhook deliveries use exponential backoff.

## Policy

- Attempt 1: immediate
- Attempt 2: after 30 seconds
- Attempt 3: after 2 minutes
- Attempt 4: after 10 minutes
- Give up after 4 failures and mark the delivery as `dead_letter`

Idempotency keys are required on every retry so duplicate deliveries are dropped.
