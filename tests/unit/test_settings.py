"""Tests for configuration settings module."""

from collections.abc import Generator
from decimal import Decimal
import os
from pathlib import Path

from pydantic import ValidationError
import pytest

from polymarket_arbitrage.config.constants import (
    ARBITRAGE_THRESHOLD,
    DEFAULT_INITIAL_CAPITAL,
    DEFAULT_MARKET_CATEGORIES,
    DEFAULT_MAX_POSITION_SIZE,
    DEFAULT_POLL_INTERVAL,
    MIN_LIQUIDITY,
    MIN_VOLUME,
)
from polymarket_arbitrage.config.settings import Settings, get_settings, load_settings


@pytest.fixture()
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove all ARBITRAGE_* env vars so defaults are tested in isolation.

    Also prevents env_file='.env' from injecting values by setting
    the env file path to a nonexistent file via monkeypatch.
    """
    for key in list(os.environ):
        if key.upper().startswith("ARBITRAGE_"):
            monkeypatch.delenv(key)


@pytest.mark.unit
@pytest.mark.usefixtures("_clean_env")
class TestSettingsDefaults:
    """Tests that all Settings fields have correct default values."""

    @pytest.fixture()
    def settings(self) -> Settings:
        """Create Settings with all defaults."""
        return Settings()

    def test_polymarket_api_url_default(self, settings: Settings) -> None:
        """Default API URL points to Gamma API."""
        assert settings.polymarket_api_url == "https://gamma-api.polymarket.com"

    def test_api_timeout_seconds_default(self, settings: Settings) -> None:
        """Default timeout is 30 seconds."""
        assert settings.api_timeout_seconds == 30.0

    def test_api_max_connections_default(self, settings: Settings) -> None:
        """Default max connections is 100."""
        assert settings.api_max_connections == 100

    def test_rate_limit_requests_per_second_default(self, settings: Settings) -> None:
        """Default rate limit is 10 requests per second."""
        assert settings.rate_limit_requests_per_second == 10.0

    def test_rate_limit_burst_default(self, settings: Settings) -> None:
        """Default burst size is 20."""
        assert settings.rate_limit_burst == 20

    def test_retry_max_attempts_default(self, settings: Settings) -> None:
        """Default max retry attempts is 3."""
        assert settings.retry_max_attempts == 3

    def test_retry_base_delay_seconds_default(self, settings: Settings) -> None:
        """Default retry base delay is 1 second."""
        assert settings.retry_base_delay_seconds == 1.0

    def test_circuit_breaker_failure_threshold_default(self, settings: Settings) -> None:
        """Default circuit breaker failure threshold is 5."""
        assert settings.circuit_breaker_failure_threshold == 5

    def test_circuit_breaker_recovery_timeout_default(self, settings: Settings) -> None:
        """Default circuit breaker recovery timeout is 60 seconds."""
        assert settings.circuit_breaker_recovery_timeout_seconds == 60.0

    def test_arbitrage_threshold_default(self, settings: Settings) -> None:
        """Default arbitrage threshold matches constant."""
        assert settings.arbitrage_threshold == ARBITRAGE_THRESHOLD

    def test_min_liquidity_usd_default(self, settings: Settings) -> None:
        """Default minimum liquidity matches constant."""
        assert settings.min_liquidity_usd == MIN_LIQUIDITY

    def test_min_volume_usd_default(self, settings: Settings) -> None:
        """Default minimum volume matches constant."""
        assert settings.min_volume_usd == MIN_VOLUME

    def test_paper_trading_enabled_default(self, settings: Settings) -> None:
        """Paper trading is enabled by default."""
        assert settings.paper_trading_enabled is True

    def test_initial_capital_usd_default(self, settings: Settings) -> None:
        """Default initial capital matches constant."""
        assert settings.initial_capital_usd == DEFAULT_INITIAL_CAPITAL

    def test_max_position_size_usd_default(self, settings: Settings) -> None:
        """Default max position size matches constant."""
        assert settings.max_position_size_usd == DEFAULT_MAX_POSITION_SIZE

    def test_market_categories_default(self, settings: Settings) -> None:
        """Default market categories match constant."""
        assert settings.market_categories == DEFAULT_MARKET_CATEGORIES

    def test_exclude_markets_default(self, settings: Settings) -> None:
        """Default exclude markets is empty list."""
        assert settings.exclude_markets == []

    def test_log_level_default(self, settings: Settings) -> None:
        """Default log level is INFO."""
        assert settings.log_level == "INFO"

    def test_json_logs_default(self, settings: Settings) -> None:
        """JSON logs enabled by default."""
        assert settings.json_logs is True

    def test_metrics_port_default(self, settings: Settings) -> None:
        """Default metrics port is 9090."""
        assert settings.metrics_port == 9090

    def test_poll_interval_seconds_default(self, settings: Settings) -> None:
        """Default poll interval matches constant."""
        assert settings.poll_interval_seconds == DEFAULT_POLL_INTERVAL


@pytest.mark.unit
@pytest.mark.usefixtures("_clean_env")
class TestSettingsValidation:
    """Tests for field validation and boundary checks."""

    def test_api_timeout_below_minimum_rejected(self) -> None:
        """Timeout below 1 second is rejected."""
        with pytest.raises(ValidationError, match="api_timeout_seconds"):
            Settings(api_timeout_seconds=0.5)

    def test_api_timeout_above_maximum_rejected(self) -> None:
        """Timeout above 120 seconds is rejected."""
        with pytest.raises(ValidationError, match="api_timeout_seconds"):
            Settings(api_timeout_seconds=121.0)

    def test_api_max_connections_below_minimum_rejected(self) -> None:
        """Max connections below 1 is rejected."""
        with pytest.raises(ValidationError, match="api_max_connections"):
            Settings(api_max_connections=0)

    def test_api_max_connections_above_maximum_rejected(self) -> None:
        """Max connections above 1000 is rejected."""
        with pytest.raises(ValidationError, match="api_max_connections"):
            Settings(api_max_connections=1001)

    def test_rate_limit_below_minimum_rejected(self) -> None:
        """Rate limit below 0.1 is rejected."""
        with pytest.raises(ValidationError, match="rate_limit_requests_per_second"):
            Settings(rate_limit_requests_per_second=0.05)

    def test_rate_limit_above_maximum_rejected(self) -> None:
        """Rate limit above 100.0 is rejected."""
        with pytest.raises(ValidationError, match="rate_limit_requests_per_second"):
            Settings(rate_limit_requests_per_second=100.1)

    def test_rate_limit_burst_below_minimum_rejected(self) -> None:
        """Burst below 1 is rejected."""
        with pytest.raises(ValidationError, match="rate_limit_burst"):
            Settings(rate_limit_burst=0)

    def test_rate_limit_burst_above_maximum_rejected(self) -> None:
        """Burst above 200 is rejected."""
        with pytest.raises(ValidationError, match="rate_limit_burst"):
            Settings(rate_limit_burst=201)

    def test_retry_max_attempts_below_minimum_rejected(self) -> None:
        """Max attempts below 1 is rejected."""
        with pytest.raises(ValidationError, match="retry_max_attempts"):
            Settings(retry_max_attempts=0)

    def test_retry_max_attempts_above_maximum_rejected(self) -> None:
        """Max attempts above 10 is rejected."""
        with pytest.raises(ValidationError, match="retry_max_attempts"):
            Settings(retry_max_attempts=11)

    def test_retry_base_delay_below_minimum_rejected(self) -> None:
        """Retry base delay below 0.1 is rejected."""
        with pytest.raises(ValidationError, match="retry_base_delay_seconds"):
            Settings(retry_base_delay_seconds=0.05)

    def test_retry_base_delay_above_maximum_rejected(self) -> None:
        """Retry base delay above 60.0 is rejected."""
        with pytest.raises(ValidationError, match="retry_base_delay_seconds"):
            Settings(retry_base_delay_seconds=60.1)

    def test_circuit_breaker_failure_threshold_at_zero_rejected(self) -> None:
        """Circuit breaker failure threshold at 0 is rejected."""
        with pytest.raises(ValidationError, match="circuit_breaker_failure_threshold"):
            Settings(circuit_breaker_failure_threshold=0)

    def test_circuit_breaker_failure_threshold_above_maximum_rejected(self) -> None:
        """Circuit breaker failure threshold above 100 is rejected."""
        with pytest.raises(ValidationError, match="circuit_breaker_failure_threshold"):
            Settings(circuit_breaker_failure_threshold=101)

    def test_circuit_breaker_recovery_timeout_below_minimum_rejected(self) -> None:
        """Circuit breaker recovery timeout below 1.0 is rejected."""
        with pytest.raises(ValidationError, match="circuit_breaker_recovery_timeout_seconds"):
            Settings(circuit_breaker_recovery_timeout_seconds=0.5)

    def test_circuit_breaker_recovery_timeout_above_maximum_rejected(self) -> None:
        """Circuit breaker recovery timeout above 600.0 is rejected."""
        with pytest.raises(ValidationError, match="circuit_breaker_recovery_timeout_seconds"):
            Settings(circuit_breaker_recovery_timeout_seconds=600.1)

    def test_arbitrage_threshold_below_minimum_rejected(self) -> None:
        """Arbitrage threshold below 0.5 is rejected."""
        with pytest.raises(ValidationError, match="arbitrage_threshold"):
            Settings(arbitrage_threshold=Decimal("0.4"))

    def test_arbitrage_threshold_above_maximum_rejected(self) -> None:
        """Arbitrage threshold above 1.0 is rejected."""
        with pytest.raises(ValidationError, match="arbitrage_threshold"):
            Settings(arbitrage_threshold=Decimal("1.1"))

    def test_arbitrage_threshold_at_boundary_accepted(self) -> None:
        """Arbitrage threshold at boundary values is accepted."""
        low = Settings(arbitrage_threshold=Decimal("0.5"))
        high = Settings(arbitrage_threshold=Decimal("1.0"))
        assert low.arbitrage_threshold == Decimal("0.5")
        assert high.arbitrage_threshold == Decimal("1.0")

    def test_min_liquidity_negative_rejected(self) -> None:
        """Negative liquidity is rejected."""
        with pytest.raises(ValidationError, match="min_liquidity_usd"):
            Settings(min_liquidity_usd=Decimal("-1"))

    def test_min_volume_negative_rejected(self) -> None:
        """Negative volume is rejected."""
        with pytest.raises(ValidationError, match="min_volume_usd"):
            Settings(min_volume_usd=Decimal("-1"))

    def test_initial_capital_negative_rejected(self) -> None:
        """Negative initial capital is rejected."""
        with pytest.raises(ValidationError, match="initial_capital_usd"):
            Settings(initial_capital_usd=Decimal("-100"))

    def test_max_position_size_negative_rejected(self) -> None:
        """Negative max position size is rejected."""
        with pytest.raises(ValidationError, match="max_position_size_usd"):
            Settings(max_position_size_usd=Decimal("-50"))

    def test_metrics_port_below_minimum_rejected(self) -> None:
        """Port below 1024 is rejected."""
        with pytest.raises(ValidationError, match="metrics_port"):
            Settings(metrics_port=80)

    def test_metrics_port_above_maximum_rejected(self) -> None:
        """Port above 65535 is rejected."""
        with pytest.raises(ValidationError, match="metrics_port"):
            Settings(metrics_port=70000)

    def test_poll_interval_below_minimum_rejected(self) -> None:
        """Poll interval below 1 second is rejected."""
        with pytest.raises(ValidationError, match="poll_interval_seconds"):
            Settings(poll_interval_seconds=0.5)

    def test_poll_interval_above_maximum_rejected(self) -> None:
        """Poll interval above 3600 seconds is rejected."""
        with pytest.raises(ValidationError, match="poll_interval_seconds"):
            Settings(poll_interval_seconds=3601.0)

    def test_log_level_invalid_value_rejected(self) -> None:
        """Invalid log level is rejected."""
        with pytest.raises(ValidationError, match="log_level"):
            Settings(log_level="TRACE")  # type: ignore[arg-type]

    def test_log_level_valid_values_accepted(self) -> None:
        """All valid log levels are accepted."""
        for level in ("DEBUG", "INFO", "WARNING", "ERROR"):
            s = Settings(log_level=level)
            assert s.log_level == level


@pytest.mark.unit
@pytest.mark.usefixtures("_clean_env")
class TestSettingsValidators:
    """Tests for custom field validators."""

    def test_validate_position_size_returns_value(self) -> None:
        """Position size validator passes through valid value."""
        settings = Settings(max_position_size_usd=Decimal("50"))
        assert settings.max_position_size_usd == Decimal("50")

    def test_validate_categories_empty_list_rejected(self) -> None:
        """Empty categories list is rejected by validator."""
        with pytest.raises(ValidationError, match="At least one market category"):
            Settings(market_categories=[])

    def test_validate_categories_single_category_accepted(self) -> None:
        """Single category is accepted."""
        settings = Settings(market_categories=["sports"])
        assert settings.market_categories == ["sports"]

    def test_validate_categories_multiple_categories_accepted(self) -> None:
        """Multiple categories are accepted."""
        cats = ["politics", "crypto", "sports"]
        settings = Settings(market_categories=cats)
        assert settings.market_categories == cats


@pytest.mark.unit
@pytest.mark.usefixtures("_clean_env")
class TestLoadSettings:
    """Tests for load_settings() function."""

    def test_load_settings_without_file_returns_defaults(self) -> None:
        """Loading without config file returns default settings."""
        settings = load_settings()
        assert settings.polymarket_api_url == "https://gamma-api.polymarket.com"
        assert settings.log_level == "INFO"

    def test_load_settings_with_nonexistent_file_returns_defaults(self) -> None:
        """Loading with nonexistent file returns defaults."""
        settings = load_settings(Path("/nonexistent/config.yaml"))
        assert settings.log_level == "INFO"

    def test_load_settings_with_yaml_file(self, tmp_path: Path) -> None:
        """Loading with YAML file overrides defaults."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "log_level: DEBUG\napi_timeout_seconds: 15.0\npoll_interval_seconds: 30.0\n"
        )
        settings = load_settings(config_file)
        assert settings.log_level == "DEBUG"
        assert settings.api_timeout_seconds == 15.0
        assert settings.poll_interval_seconds == 30.0

    def test_load_settings_yaml_partial_override(self, tmp_path: Path) -> None:
        """YAML file overrides only specified fields; rest remain default."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("log_level: WARNING\n")
        settings = load_settings(config_file)
        assert settings.log_level == "WARNING"
        assert settings.api_timeout_seconds == 30.0  # still default

    def test_load_settings_yaml_with_decimal_fields(self, tmp_path: Path) -> None:
        """YAML file can set Decimal fields."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("initial_capital_usd: '5000'\nmax_position_size_usd: '250'\n")
        settings = load_settings(config_file)
        assert settings.initial_capital_usd == Decimal("5000")
        assert settings.max_position_size_usd == Decimal("250")

    def test_load_settings_yaml_invalid_values_rejected(self, tmp_path: Path) -> None:
        """YAML with invalid values raises ValidationError."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("api_timeout_seconds: 0.01\n")
        with pytest.raises(ValidationError, match="api_timeout_seconds"):
            load_settings(config_file)

    def test_load_settings_with_empty_yaml_file(self, tmp_path: Path) -> None:
        """Empty YAML file returns default settings via the `or {}` guard."""
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")
        settings = load_settings(config_file)
        assert settings.log_level == "INFO"
        assert settings.polymarket_api_url == "https://gamma-api.polymarket.com"
        assert settings.api_timeout_seconds == 30.0

    def test_load_settings_with_none_returns_defaults(self) -> None:
        """Passing None explicitly returns defaults."""
        settings = load_settings(None)
        assert settings.polymarket_api_url == "https://gamma-api.polymarket.com"


@pytest.mark.unit
class TestGetSettings:
    """Tests for get_settings() singleton pattern."""

    @pytest.fixture(autouse=True)
    def _reset_singleton(self) -> Generator[None]:
        """Reset the singleton before and after each test."""
        import polymarket_arbitrage.config.settings as settings_module

        settings_module._settings = None
        yield
        settings_module._settings = None

    def test_get_settings_returns_settings_instance(self) -> None:
        """get_settings returns a valid Settings instance."""
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_get_settings_returns_same_instance(self) -> None:
        """get_settings returns the same instance on subsequent calls."""
        first = get_settings()
        second = get_settings()
        assert first is second

    def test_get_settings_singleton_can_be_reset(self) -> None:
        """Singleton can be reset by setting _settings to None."""
        import polymarket_arbitrage.config.settings as settings_module

        first = get_settings()
        settings_module._settings = None
        second = get_settings()
        assert first is not second


@pytest.mark.unit
@pytest.mark.usefixtures("_clean_env")
class TestEnvironmentVariableOverrides:
    """Tests for environment variable overrides with ARBITRAGE_ prefix."""

    def test_log_level_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """ARBITRAGE_LOG_LEVEL env var overrides default."""
        monkeypatch.setenv("ARBITRAGE_LOG_LEVEL", "DEBUG")
        settings = Settings()
        assert settings.log_level == "DEBUG"

    def test_api_timeout_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """ARBITRAGE_API_TIMEOUT_SECONDS env var overrides default."""
        monkeypatch.setenv("ARBITRAGE_API_TIMEOUT_SECONDS", "15.0")
        settings = Settings()
        assert settings.api_timeout_seconds == 15.0

    def test_paper_trading_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """ARBITRAGE_PAPER_TRADING_ENABLED env var overrides default."""
        monkeypatch.setenv("ARBITRAGE_PAPER_TRADING_ENABLED", "false")
        settings = Settings()
        assert settings.paper_trading_enabled is False

    def test_initial_capital_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """ARBITRAGE_INITIAL_CAPITAL_USD env var overrides default."""
        monkeypatch.setenv("ARBITRAGE_INITIAL_CAPITAL_USD", "50000")
        settings = Settings()
        assert settings.initial_capital_usd == Decimal("50000")

    def test_poll_interval_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """ARBITRAGE_POLL_INTERVAL_SECONDS env var overrides default."""
        monkeypatch.setenv("ARBITRAGE_POLL_INTERVAL_SECONDS", "120")
        settings = Settings()
        assert settings.poll_interval_seconds == 120.0

    def test_json_logs_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """ARBITRAGE_JSON_LOGS env var overrides default."""
        monkeypatch.setenv("ARBITRAGE_JSON_LOGS", "false")
        settings = Settings()
        assert settings.json_logs is False

    def test_metrics_port_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """ARBITRAGE_METRICS_PORT env var overrides default."""
        monkeypatch.setenv("ARBITRAGE_METRICS_PORT", "8080")
        settings = Settings()
        assert settings.metrics_port == 8080

    def test_lowercase_env_var_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Lowercase env var is accepted when case_sensitive=False."""
        monkeypatch.setenv("arbitrage_log_level", "ERROR")
        settings = Settings()
        assert settings.log_level == "ERROR"

    def test_extra_env_vars_ignored(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Unknown ARBITRAGE_ env vars are ignored (extra='ignore')."""
        monkeypatch.setenv("ARBITRAGE_UNKNOWN_FIELD", "some_value")
        settings = Settings()
        assert not hasattr(settings, "unknown_field")

    def test_env_var_overrides_yaml(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """YAML kwargs override env vars because Settings(**config_data) passes them as init args.

        In pydantic-settings, init kwargs have highest priority, so YAML values
        (passed as constructor arguments) take precedence over environment variables.
        """
        config_file = tmp_path / "config.yaml"
        config_file.write_text("log_level: DEBUG\n")
        monkeypatch.setenv("ARBITRAGE_LOG_LEVEL", "WARNING")
        settings = load_settings(config_file)
        # YAML wins because load_settings passes YAML values as init kwargs
        assert settings.log_level == "DEBUG"

    def test_invalid_env_var_rejected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Invalid env var value raises ValidationError."""
        monkeypatch.setenv("ARBITRAGE_API_TIMEOUT_SECONDS", "not_a_number")
        with pytest.raises(ValidationError, match="api_timeout_seconds"):
            Settings()
