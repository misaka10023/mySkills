# Refund Browser Harness Fixture

1. The browser agent receives a support ticket and customer identifier.
2. It opens the billing console and reads the latest eligible charge.
3. The `submit_refund` tool accepts `customer_id`, `charge_id`, and `amount`.
4. The tool has no idempotency-key input and returns only `ok` or `timeout`.
5. On `timeout`, the agent retries `submit_refund` immediately with the same values.
6. Refunds below USD 500 require no human approval.
7. The agent credential can refund any customer and has no per-task scope.
8. Traces record the tool name and final status but omit request identity and provider transaction ID.
9. Existing evals check that a successful refund page appears.
10. Existing evals do not simulate a timeout after the provider accepted the first request.
