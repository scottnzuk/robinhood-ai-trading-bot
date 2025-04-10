# Trading System Architecture v2.1

## Core Components

```mermaid
graph TD
    A[API Client] --> B[Validation Layer]
    B --> C[Rate Limiter]
    C --> D[Circuit Breaker]
    D --> E[Business Logic]
    E --> F[Metrics Collector]
    F --> G[Persistence Layer]
```

## Dynamic Rate Limiting

```mermaid
flowchart TD
    A[API Request] --> B[Check Current Rate]
    B --> C{Within Limits?}
    C -->|Yes| D[Process Request]
    C -->|No| E[Reject Request]
    D --> F[Record Metrics]
    F --> G[Adjust Rate Based On Health]
    G --> H[Update Rate Limits]
```

Key Features:
- **Dynamic Adjustment**: Rates adjust between 50-150% of baseline based on system health
- **Health Factors**:
  - Error rates (weight: 40%)
  - Latency percentiles (weight: 30%)
  - Resource utilization (weight: 30%)
- **Backoff Strategy**: Exponential backoff during degraded performance
- **Monitoring**: Integrated with Prometheus/Grafana

Configuration:
```yaml
rate_limits:
  robinhood:
    base_calls: 60
    period: 60s
    min_calls: 30 # 50% of base
    max_calls: 90 # 150% of base
  ai_service:
    base_calls: 30
    period: 60s
    min_calls: 15
    max_calls: 45
```

## Validation Flow

```mermaid
sequenceDiagram
    participant Client
    participant Validator
    participant Service
    
    Client->>Validator: Request (params)
    Validator->>Validator: Validate inputs
    alt Valid
        Validator->>Service: Forward request
        Service->>Client: Response
    else Invalid
        Validator->>Client: ValidationError
    end
```

## Metrics Collection

```mermaid
flowchart LR
    A[API Call] --> B[Track Latency]
    B --> C[Count Success/Error]
    C --> D[Record Trade Metrics]
    D --> E[Prometheus]
    E --> F[Grafana Dashboard]
```

## Error Handling Hierarchy

```mermaid
classDiagram
    TradingSystemError <|-- ValidationError
    TradingSystemError <|-- RateLimitExceededError
    TradingSystemError <|-- CircuitTrippedError
    TradingSystemError <|-- APIEndpointError
    APIEndpointError <|-- RobinhoodAPIError
    APIEndpointError <|-- AIProviderError
    
    class TradingSystemError{
        +message: str
    }
    class ValidationError{
        +field: str
    }
    class APIEndpointError{
        +endpoint: str
        +status_code: int
    }
```

## Updated Component Diagram

```mermaid
graph LR
    subgraph Core Services
        A[Validation] --> B[Rate Limiting]
        B --> C[Circuit Breaking]
        C --> D[Metrics]
    end
    
    subgraph External Dependencies
        E[Robinhood API]
        F[AI Services]
    end
    
    D --> G[(Database)]
    D --> H[(Cache)]
    
    style A fill:#cff,stroke:#333
    style D fill:#cfc,stroke:#333