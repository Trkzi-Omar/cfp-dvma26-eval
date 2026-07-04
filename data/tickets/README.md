# data/tickets

The raw shape of an incoming support ticket, as the system receives it, before any
eval metadata is attached. `sample_incoming_ticket.json` shows the minimal fields:
`id`, `subject`, `body`, `customer_tier`.

The named scenarios the talk uses live in `examples/` (same shape, plus an
`expected_route`, a `failure_mode`, and `notes`). The evaluation dataset lives in
`evals/datasets/`. All of this data is invented for illustration.

Run any raw ticket through the system:

```bash
python -m app.main data/tickets/sample_incoming_ticket.json
```
