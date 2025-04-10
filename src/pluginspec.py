import pluggy

hookspec = pluggy.HookspecMarker("ingestion")
hookimpl = pluggy.HookimplMarker("ingestion")


class IngestionSpec:
    @hookspec
    def pre_validate(self, trade_dict: dict) -> dict:
        """
        Modify or filter trade data before validation.
        Return None to drop the trade.
        """

    @hookspec
    def post_insert(self, batch: list):
        """
        Called after a batch insert into ClickHouse.
        Can trigger alerts, ML inference, etc.
        """

    @hookspec
    def anomaly_alert(self, trade_dict: dict, reason: str):
        """
        Called when an anomaly is detected.
        """

    @hookspec
    def before_retry(self, context: dict):
        """
        Called before retrying a failed operation.
        Can adjust retry delay or cancel retry.
        """

    @hookspec
    def on_circuit_open(self, context: dict):
        """
        Called when a circuit breaker trips.
        Can alert or adjust breaker params.
        """

    @hookspec
    def on_circuit_close(self, context: dict):
        """
        Called when a circuit breaker resets.
        """