"""Tests for multi-endpoint fallback strategy."""

import pytest

from polymarket_arbitrage.api.endpoints import EndpointStrategy, PolymarketEndpoints


@pytest.mark.unit
class TestEndpointStrategy:
    """Tests for EndpointStrategy.build_url()."""

    def test_build_url_path_param(self) -> None:
        """Test path parameter replaces {id} in pattern."""
        strategy = EndpointStrategy(
            pattern="/markets/{id}",
            param_location="path",
            param_name="id",
        )
        url, params = strategy.build_url("0x123")
        assert url == "/markets/0x123"
        assert params is None

    def test_build_url_query_param(self) -> None:
        """Test query parameter returns pattern unchanged with params dict."""
        strategy = EndpointStrategy(
            pattern="/markets",
            param_location="query",
            param_name="condition_id",
        )
        url, params = strategy.build_url("0x123")
        assert url == "/markets"
        assert params == {"condition_id": "0x123"}

    def test_build_url_path_param_nested_pattern(self) -> None:
        """Test path parameter in nested URL pattern."""
        strategy = EndpointStrategy(
            pattern="/markets/condition/{id}",
            param_location="path",
            param_name="id",
        )
        url, params = strategy.build_url("0xabc")
        assert url == "/markets/condition/0xabc"
        assert params is None

    def test_build_url_empty_identifier(self) -> None:
        """Test build_url with empty string identifier."""
        strategy = EndpointStrategy(
            pattern="/markets/{id}",
            param_location="path",
            param_name="id",
        )
        url, params = strategy.build_url("")
        assert url == "/markets/"
        assert params is None

    def test_build_url_query_empty_identifier(self) -> None:
        """Test query param build_url with empty string identifier."""
        strategy = EndpointStrategy(
            pattern="/markets",
            param_location="query",
            param_name="condition_id",
        )
        url, params = strategy.build_url("")
        assert url == "/markets"
        assert params == {"condition_id": ""}

    def test_build_url_special_characters_in_identifier(self) -> None:
        """Test identifiers with special characters are passed through."""
        strategy = EndpointStrategy(
            pattern="/markets/{id}",
            param_location="path",
            param_name="id",
        )
        url, params = strategy.build_url("0x123+abc&foo=bar")
        assert url == "/markets/0x123+abc&foo=bar"
        assert params is None

    def test_build_url_query_special_characters(self) -> None:
        """Test query param with special characters in identifier."""
        strategy = EndpointStrategy(
            pattern="/markets",
            param_location="query",
            param_name="id",
        )
        url, params = strategy.build_url("0x123&evil=true")
        assert url == "/markets"
        assert params == {"id": "0x123&evil=true"}

    def test_frozen_dataclass(self) -> None:
        """Test that EndpointStrategy is immutable."""
        strategy = EndpointStrategy(
            pattern="/markets/{id}",
            param_location="path",
            param_name="id",
        )
        with pytest.raises(AttributeError):
            strategy.pattern = "/other/{id}"  # type: ignore[misc]

    def test_equality(self) -> None:
        """Test that two identical strategies are equal."""
        s1 = EndpointStrategy("/markets/{id}", "path", "id")
        s2 = EndpointStrategy("/markets/{id}", "path", "id")
        assert s1 == s2

    def test_hashable(self) -> None:
        """Test that frozen dataclass is hashable (usable as dict key)."""
        strategy = EndpointStrategy("/markets/{id}", "path", "id")
        d = {strategy: "primary"}
        assert d[strategy] == "primary"

    def test_build_url_does_not_encode_path_params(self) -> None:
        """URL encoding is handled by the HTTP client (httpx), not by endpoint building.

        This test documents that build_url passes identifiers through as-is.
        """
        strategy = EndpointStrategy(
            pattern="/markets/{id}",
            param_location="path",
            param_name="id",
        )
        url, params = strategy.build_url("../../admin")
        assert url == "/markets/../../admin"
        assert params is None

    def test_build_url_path_param_mismatched_name_no_replacement(self) -> None:
        """Mismatched param_name leaves the placeholder unreplaced."""
        strategy = EndpointStrategy(
            pattern="/markets/{id}",
            param_location="path",
            param_name="wrong",
        )
        url, params = strategy.build_url("0x123")
        assert url == "/markets/{id}"
        assert params is None

    def test_build_url_path_param_uses_param_name(self) -> None:
        """Test path replacement uses param_name, not hardcoded 'id'."""
        strategy = EndpointStrategy(
            pattern="/conditions/{condition_id}",
            param_location="path",
            param_name="condition_id",
        )
        url, params = strategy.build_url("0xabc")
        assert url == "/conditions/0xabc"
        assert params is None


@pytest.mark.unit
class TestPolymarketEndpointsGetMarketUrls:
    """Tests for PolymarketEndpoints.get_market_urls()."""

    def test_returns_all_strategies_by_default(self) -> None:
        """Test that all three strategies are returned with include_query=True."""
        urls = PolymarketEndpoints.get_market_urls("0x123")
        assert len(urls) == 3

    def test_first_url_is_direct_market_path(self) -> None:
        """Test primary strategy is direct market ID lookup."""
        urls = PolymarketEndpoints.get_market_urls("0x123")
        url, params = urls[0]
        assert url == "/markets/0x123"
        assert params is None

    def test_second_url_is_condition_path(self) -> None:
        """Test second strategy is condition-based path."""
        urls = PolymarketEndpoints.get_market_urls("0x123")
        url, params = urls[1]
        assert url == "/markets/condition/0x123"
        assert params is None

    def test_third_url_is_query_param(self) -> None:
        """Test third strategy is query parameter lookup."""
        urls = PolymarketEndpoints.get_market_urls("0x123")
        url, params = urls[2]
        assert url == "/markets"
        assert params == {"condition_id": "0x123"}

    def test_exclude_query_strategies(self) -> None:
        """Test include_query=False filters out query param strategies."""
        urls = PolymarketEndpoints.get_market_urls("0x123", include_query=False)
        assert len(urls) == 2
        for _url, params in urls:
            assert params is None

    def test_identifier_propagated_to_all_urls(self) -> None:
        """Test that the identifier appears in all generated URLs."""
        identifier = "0xdeadbeef"
        urls = PolymarketEndpoints.get_market_urls(identifier)
        for url, params in urls:
            if params is None:
                assert identifier in url
            else:
                assert identifier in params.values()


@pytest.mark.unit
class TestPolymarketEndpointsGetConditionUrls:
    """Tests for PolymarketEndpoints.get_condition_urls()."""

    def test_returns_two_strategies(self) -> None:
        """Test that both condition strategies are returned."""
        urls = PolymarketEndpoints.get_condition_urls("0xabc")
        assert len(urls) == 2

    def test_first_url_is_by_condition(self) -> None:
        """Test primary condition strategy uses by-condition path."""
        urls = PolymarketEndpoints.get_condition_urls("0xabc")
        url, params = urls[0]
        assert url == "/markets/by-condition/0xabc"
        assert params is None

    def test_second_url_is_condition_path(self) -> None:
        """Test fallback condition strategy uses condition path."""
        urls = PolymarketEndpoints.get_condition_urls("0xabc")
        url, params = urls[1]
        assert url == "/markets/condition/0xabc"
        assert params is None

    def test_all_condition_urls_are_path_params(self) -> None:
        """Test that all condition strategies use path parameters (no query params)."""
        urls = PolymarketEndpoints.get_condition_urls("0x999")
        for _url, params in urls:
            assert params is None


@pytest.mark.unit
class TestPolymarketEndpointsGetMarketsListUrl:
    """Tests for PolymarketEndpoints.get_markets_list_url()."""

    def test_no_params(self) -> None:
        """Test with no optional parameters returns empty params dict."""
        url, params = PolymarketEndpoints.get_markets_list_url()
        assert url == "/markets"
        assert params == {}

    def test_limit_only(self) -> None:
        """Test with limit parameter only."""
        url, params = PolymarketEndpoints.get_markets_list_url(limit=10)
        assert url == "/markets"
        assert params == {"limit": "10"}

    def test_offset_only(self) -> None:
        """Test with offset parameter only."""
        url, params = PolymarketEndpoints.get_markets_list_url(offset=50)
        assert url == "/markets"
        assert params == {"offset": "50"}

    def test_category_only(self) -> None:
        """Test with category parameter only."""
        url, params = PolymarketEndpoints.get_markets_list_url(category="politics")
        assert url == "/markets"
        assert params == {"category": "politics"}

    def test_all_params(self) -> None:
        """Test with all parameters provided."""
        url, params = PolymarketEndpoints.get_markets_list_url(
            limit=25, offset=100, category="crypto"
        )
        assert url == "/markets"
        assert params == {"limit": "25", "offset": "100", "category": "crypto"}

    def test_limit_converted_to_string(self) -> None:
        """Test that integer limit is converted to string in params."""
        _url, params = PolymarketEndpoints.get_markets_list_url(limit=42)
        assert isinstance(params["limit"], str)

    def test_offset_converted_to_string(self) -> None:
        """Test that integer offset is converted to string in params."""
        _url, params = PolymarketEndpoints.get_markets_list_url(offset=0)
        assert params["offset"] == "0"

    def test_zero_limit(self) -> None:
        """Test limit=0 is included (not treated as falsy)."""
        _url, params = PolymarketEndpoints.get_markets_list_url(limit=0)
        assert params == {"limit": "0"}

    def test_zero_offset(self) -> None:
        """Test offset=0 is included (not treated as falsy)."""
        _url, params = PolymarketEndpoints.get_markets_list_url(offset=0)
        assert params == {"offset": "0"}

    def test_url_is_always_markets(self) -> None:
        """Test that the URL path is always /markets regardless of params."""
        url1, _ = PolymarketEndpoints.get_markets_list_url()
        url2, _ = PolymarketEndpoints.get_markets_list_url(limit=10, category="sports")
        assert url1 == "/markets"
        assert url2 == "/markets"
