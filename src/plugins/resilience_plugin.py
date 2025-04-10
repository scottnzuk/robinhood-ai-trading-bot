from src.pluginspec import hookimpl

class ResiliencePlugin:
    @hookimpl
    def before_retry(self, context):
        attempt = context.get("attempt", 0)
        delay = min(2 ** attempt, 30)
        print(f"[RETRY] Attempt {attempt+1}, delaying {delay}s")
        context["delay"] = delay  # can be used to adjust sleep time

    @hookimpl
    def on_circuit_open(self, context):
        print(f"[CIRCUIT OPEN] Circuit breaker tripped for {context.get('component')}")

    @hookimpl
    def on_circuit_close(self, context):
        print(f"[CIRCUIT CLOSE] Circuit breaker reset for {context.get('component')}")