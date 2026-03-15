"""Tests for monitoring.metrics module."""

import asyncio

from prometheus_client import REGISTRY
import pytest

from polymarket_arbitrage.monitoring.metrics import (
    record_opportunity_detected,
    record_trade_executed,
    track_detection_cycle,
    update_capital_metrics,
    update_circuit_breaker_state,
    update_position_count,
)


def _get(name: str, labels: dict[str, str] | None = None) -> float:
    """Read a metric sample value from the default registry.

    Returns 0.0 when the metric/label combination has not been observed yet,
    which is the correct semantic for counters and histograms before first use.
    """
    value = REGISTRY.get_sample_value(name, labels or {})
    return value if value is not None else 0.0


@pytest.mark.unit
class TestAppInfo:
    """Tests for APP_INFO metric set at module initialization."""

    def test_app_info_has_correct_labels(self) -> None:
        """APP_INFO metric has expected app_name and mode labels."""
        value = _get(
            "arbitrage_detector_info_info",
            {"app_name": "polymarket-arbitrage-detector", "mode": "paper_trading"},
        )
        assert value == 1.0


@pytest.mark.unit
class TestRecordOpportunityDetected:
    """Tests for record_opportunity_detected."""

    def test_increments_counter_for_strategy(self) -> None:
        """Test that calling the function increments the counter for the given strategy."""
        before = _get("arbitrage_opportunities_detected_total", {"strategy": "test_strat"})
        record_opportunity_detected("test_strat", 0.05)
        after = _get("arbitrage_opportunities_detected_total", {"strategy": "test_strat"})
        assert after == before + 1

    def test_observes_profit_histogram(self) -> None:
        """Test that profit per dollar is observed in the histogram."""
        before_count = _get("arbitrage_profit_per_dollar_sum")
        record_opportunity_detected("hist_strat", 0.03)
        after_count = _get("arbitrage_profit_per_dollar_sum")
        assert after_count == pytest.approx(before_count + 0.03)

    def test_multiple_calls_accumulate(self) -> None:
        """Test that multiple calls increment the counter each time."""
        before = _get("arbitrage_opportunities_detected_total", {"strategy": "accum_strat"})
        record_opportunity_detected("accum_strat", 0.01)
        record_opportunity_detected("accum_strat", 0.02)
        record_opportunity_detected("accum_strat", 0.04)
        after = _get("arbitrage_opportunities_detected_total", {"strategy": "accum_strat"})
        assert after == before + 3


@pytest.mark.unit
class TestRecordTradeExecuted:
    """Tests for record_trade_executed."""

    def test_success_increments_success_counter(self) -> None:
        """Test that success=True increments the success label."""
        before = _get("trades_executed_total", {"status": "success"})
        record_trade_executed(success=True)
        after = _get("trades_executed_total", {"status": "success"})
        assert after == before + 1

    def test_failure_increments_failure_counter(self) -> None:
        """Test that success=False increments the failure label."""
        before = _get("trades_executed_total", {"status": "failure"})
        record_trade_executed(success=False)
        after = _get("trades_executed_total", {"status": "failure"})
        assert after == before + 1

    def test_success_does_not_increment_failure(self) -> None:
        """Test that success=True does not affect the failure counter."""
        before_failure = _get("trades_executed_total", {"status": "failure"})
        record_trade_executed(success=True)
        after_failure = _get("trades_executed_total", {"status": "failure"})
        assert after_failure == before_failure


@pytest.mark.unit
class TestUpdateCapitalMetrics:
    """Tests for update_capital_metrics."""

    def test_sets_all_five_gauges(self) -> None:
        """Test that all five capital/PnL gauges are set correctly."""
        update_capital_metrics(
            available=8000.0,
            deployed=2000.0,
            total_pnl=150.0,
            unrealized_pnl=100.0,
            realized_pnl=50.0,
        )
        assert _get("available_capital_usd") == 8000.0
        assert _get("capital_deployed_usd") == 2000.0
        assert _get("total_pnl_usd") == 150.0
        assert _get("unrealized_pnl_usd") == 100.0
        assert _get("realized_pnl_usd") == 50.0

    def test_overwrites_previous_values(self) -> None:
        """Test that calling again overwrites previous gauge values."""
        update_capital_metrics(
            available=5000.0,
            deployed=5000.0,
            total_pnl=0.0,
            unrealized_pnl=0.0,
            realized_pnl=0.0,
        )
        update_capital_metrics(
            available=7000.0,
            deployed=3000.0,
            total_pnl=200.0,
            unrealized_pnl=120.0,
            realized_pnl=80.0,
        )
        assert _get("available_capital_usd") == 7000.0
        assert _get("capital_deployed_usd") == 3000.0
        assert _get("total_pnl_usd") == 200.0
        assert _get("unrealized_pnl_usd") == 120.0
        assert _get("realized_pnl_usd") == 80.0

    def test_negative_capital_values(self) -> None:
        """Test that negative PnL values are set correctly on gauges."""
        update_capital_metrics(
            available=9000.0,
            deployed=1000.0,
            total_pnl=-250.0,
            unrealized_pnl=-300.0,
            realized_pnl=50.0,
        )
        assert _get("available_capital_usd") == 9000.0
        assert _get("capital_deployed_usd") == 1000.0
        assert _get("total_pnl_usd") == -250.0
        assert _get("unrealized_pnl_usd") == -300.0
        assert _get("realized_pnl_usd") == 50.0


@pytest.mark.unit
class TestUpdatePositionCount:
    """Tests for update_position_count."""

    def test_sets_gauge_value(self) -> None:
        """Test that the open positions gauge is set."""
        update_position_count(7)
        assert _get("open_positions") == 7

    def test_overwrites_previous_value(self) -> None:
        """Test that calling again overwrites the gauge."""
        update_position_count(3)
        update_position_count(10)
        assert _get("open_positions") == 10

    def test_zero_positions(self) -> None:
        """Test setting zero open positions."""
        update_position_count(0)
        assert _get("open_positions") == 0


@pytest.mark.unit
class TestUpdateCircuitBreakerState:
    """Tests for update_circuit_breaker_state."""

    def test_closed_state_maps_to_zero(self) -> None:
        """Test that 'closed' maps to 0."""
        update_circuit_breaker_state("api_cb", "closed")
        assert _get("circuit_breaker_state", {"circuit_breaker": "api_cb"}) == 0

    def test_half_open_state_maps_to_one(self) -> None:
        """Test that 'half_open' maps to 1."""
        update_circuit_breaker_state("api_cb", "half_open")
        assert _get("circuit_breaker_state", {"circuit_breaker": "api_cb"}) == 1

    def test_open_state_maps_to_two(self) -> None:
        """Test that 'open' maps to 2."""
        update_circuit_breaker_state("api_cb", "open")
        assert _get("circuit_breaker_state", {"circuit_breaker": "api_cb"}) == 2

    def test_unknown_state_maps_to_negative_one(self) -> None:
        """Test that an unrecognized state maps to -1."""
        update_circuit_breaker_state("api_cb", "broken")
        assert _get("circuit_breaker_state", {"circuit_breaker": "api_cb"}) == -1

    def test_case_insensitive(self) -> None:
        """Test that state matching is case-insensitive."""
        update_circuit_breaker_state("api_cb", "CLOSED")
        assert _get("circuit_breaker_state", {"circuit_breaker": "api_cb"}) == 0

        update_circuit_breaker_state("api_cb", "Half_Open")
        assert _get("circuit_breaker_state", {"circuit_breaker": "api_cb"}) == 1

    def test_different_circuit_breakers_independent(self) -> None:
        """Test that different circuit breaker names maintain independent state."""
        update_circuit_breaker_state("cb_alpha", "closed")
        update_circuit_breaker_state("cb_beta", "open")
        assert _get("circuit_breaker_state", {"circuit_breaker": "cb_alpha"}) == 0
        assert _get("circuit_breaker_state", {"circuit_breaker": "cb_beta"}) == 2


@pytest.mark.unit
class TestTrackDetectionCycle:
    """Tests for track_detection_cycle decorator."""

    @pytest.mark.asyncio
    async def test_observes_duration_in_histogram(self) -> None:
        """Test that the decorator observes a duration in the histogram."""
        before_sum = _get("detection_cycle_duration_seconds_sum")

        @track_detection_cycle
        async def dummy_cycle() -> str:
            await asyncio.sleep(0.01)
            return "done"

        result = await dummy_cycle()
        assert result == "done"
        after_sum = _get("detection_cycle_duration_seconds_sum")
        assert after_sum > before_sum

    @pytest.mark.asyncio
    async def test_records_duration_on_exception(self) -> None:
        """Test that duration is recorded even when the function raises."""
        before_sum = _get("detection_cycle_duration_seconds_sum")

        @track_detection_cycle
        async def failing_cycle() -> None:
            await asyncio.sleep(0.01)
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            await failing_cycle()

        after_sum = _get("detection_cycle_duration_seconds_sum")
        assert after_sum > before_sum

    @pytest.mark.asyncio
    async def test_preserves_return_value(self) -> None:
        """Test that the decorator returns the wrapped function's value."""

        @track_detection_cycle
        async def cycle_with_result() -> int:
            return 42

        result = await cycle_with_result()
        assert result == 42
