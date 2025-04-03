# System Patterns

## Coding Patterns
- Consistent error handling across all API calls
- Modular architecture with clear separation:
  - AI providers
  - Trading logic
  - Decision filtering
- Configuration-driven constraints
- Extensive logging throughout execution

## Architectural Patterns
- Main trading loop with interval scheduling
- AI decision making pipeline:
```mermaid
graph LR
    A[Market Data] --> B[AI Analysis]
    B --> C[Decision Filtering]
    C --> D[Trade Execution]
```
- Multi-provider AI interface pattern
- Hallucination filtering pattern

## Trading Patterns
- Portfolio balancing constraints
- Watchlist rotation based on time
- PDT restriction handling
- Demo mode implementation

## AI Provider Configuration (Updated 2025-04-02)

- **Primary Provider**: Requesty.ai
  - Base URL: https://router.requesty.ai/v1
  - Default Model: parasail/parasail-gemma3-27b-it
  - Fallback Position: First

- **Fallback Providers**:
  1. DeepSeek
    - Base URL: https://api.deepseek.com/v1
    - Models: deepseek-chat, deepseek-reasoner
  2. OpenAI
    - Base URL: https://api.openai.com/v1
    - Model: gpt-4

- **Implementation Details**:
  - Automatic fallback on failure
  - Configurable via environment variables
  - Provider selection through AIProvider enum

[2025-04-02 14:56:31] - Updated AI provider configuration with Requesty as primary and fallback support
## AI Provider Configuration (Updated 2025-04-02)

- **Primary Provider**: Requesty.ai
  - Base URL: https://router.requesty.ai/v1
  - Default Model: parasail/parasail-gemma3-27b-it
  - Signup: https://app.requesty.ai/sign-up

- **Fallback Providers**:
  1. DeepSeek
    - Base URL: https://api.deepseek.com/v1
    - Models: deepseek-chat, deepseek-reasoner
    - Signup: https://platform.deepseek.com/signup
  2. OpenRouter
    - Base URL: https://openrouter.ai/api/v1
    - Features: Finance model rankings, multiple model providers
    - Signup: https://openrouter.ai/register
  3. OpenAI
    - Base URL: https://api.openai.com/v1
    - Model: gpt-4
    - Signup: https://platform.openai.com/signup

- **Finance Model Rankings**:
  - Automatically fetches top 5 finance models from OpenRouter
  - Includes cost per completion
  - Updated on each API initialization


## Implementation Patterns

### Retry Logic
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def make_api_request(self, endpoint):
    # Implementation with automatic retries
```

### Rate Limiting
```python
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=60, period=60)
def make_request(self):
    # Implementation with rate limiting
```

### Trade Execution
```python
async def execute_trade(self, order):
    # Get best price from multiple sources
    prices = await asyncio.gather(*[
        self.get_price_from_source(source)
        for source in self.price_sources
    ])
    best_price = min(prices)
    # Smart order routing implementation
```

### Risk Management
```python
def calculate_position_size(self, atr, risk_per_trade):
    risk_amount = self.equity * risk_per_trade
    return risk_amount / atr  # ATR-based position sizing
```

## Rate Limiting Patterns (2025-04-02)

### API Rate Limiting Implementation
- **Decorator Pattern**: Using `@limits` + `@sleep_and_retry`
- **Combined with Retry**: Works alongside tenacity retry logic
- **Configuration**:
  - Trading operations: 5 calls/minute
  - Data operations: 10 calls/minute

### Key Considerations
1. Always place rate limit decorators ABOVE retry decorators
2. Monitor actual API usage to adjust limits
3. Combine with circuit breakers for robust failure handling

## Price Caching Strategy (2025-04-02)

### Cache Implementation
- **Type**: TTLCache
- **Size**: 1000 items
- **TTL**: 300 seconds (5 minutes)
- **Key Format**: `{symbol}:{interval}:{span}`

### Cache Behavior
1. Automatically evicts oldest entries when full
2. Automatically expires entries after TTL
3. Integrated with rate limiting and retry logic

### Monitoring Considerations
1. Track cache hit/miss ratios
2. Monitor memory usage
3. Adjust TTL based on market volatility

## Summary of Upgrades

- **Integration with project management tools**
- **Memory bank visualization**
- **Automated backup system**
- **Automated memory bank synchronization**
- **Version history tracking**
- **README update script**
- **Validation checks for memory bank file formats**
- **Enhanced error handling**
- **Exponential backoff for external API calls**
- **Standardized update formats across documentation**
- **Added cross-references between memory bank files**
- **Integration with Robinhood API**
- **AI-driven trading decisions**
- **Real-time market analysis**
- **Portfolio management**
- **Risk management controls**
- **Multiple operation modes (demo/manual/auto)**
- **Comprehensive logging and monitoring**
- **Execution engine enhancements**
- **Risk management system**
- **Data processing improvements**
- **Upcoming architecture improvements**
[2025-04-02 15:06:56] - Added OpenRouter integration and finance model rankings
2024-07-28 10:55:45 - Initial memory bank creation