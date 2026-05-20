# retryable

A decorator-based retry library for Python with exponential backoff and jitter strategies.

## Installation

```bash
pip install retryable
```

## Usage

```python
from retryable import retry

# Retry up to 3 times with exponential backoff
@retry(max_attempts=3, backoff="exponential", base_delay=1.0)
def fetch_data(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

# Add jitter to avoid thundering herd
@retry(max_attempts=5, backoff="exponential", jitter=True, base_delay=0.5)
def call_api():
    ...

# Retry only on specific exceptions
@retry(max_attempts=3, exceptions=(TimeoutError, ConnectionError))
def unreliable_service():
    ...
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_attempts` | `3` | Maximum number of retry attempts |
| `backoff` | `"exponential"` | Backoff strategy: `"fixed"`, `"linear"`, or `"exponential"` |
| `base_delay` | `1.0` | Initial delay in seconds between retries |
| `jitter` | `False` | Add randomness to delay to reduce contention |
| `exceptions` | `(Exception,)` | Tuple of exceptions that trigger a retry |

## Features

- Simple decorator API
- Exponential, linear, and fixed backoff strategies
- Optional jitter for distributed systems
- Configurable exception filtering
- Async support via `@async_retry`

## License

MIT