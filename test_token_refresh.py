#!/usr/bin/env python3
"""Test script to verify token refresh and retry mechanism."""

import asyncio
import logging
import sys
from unittest.mock import Mock
import datetime

# Add the src directory to the Python path
sys.path.insert(0, '/workspaces/hyundai_mqtt')

# Import directly from the module path
from src.hyundai.api_client import HyundaiAPIClient
from hyundai_kia_connect_api import VehicleManager
from src.config.settings import HyundaiConfig, Region, Brand
from src.utils.logger import get_logger

logger = get_logger(__name__)

def setup_logging():
    """Set up logging for testing."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

async def test_token_refresh_mechanism():
    """Test the token refresh and retry mechanism."""
    print("Testing token refresh and retry mechanism...")
    
    # Create test configuration
    config = HyundaiConfig(
        region=Region.EUROPE,
        brand=Brand.HYUNDAI,
        username="test@example.com",
        password="test_password",
        pin="1234"
    )
    
    # Create API client
    client = HyundaiAPIClient(config)
    
    # Mock the vehicle manager
    mock_vm = Mock(spec=VehicleManager)
    client.vehicle_manager = mock_vm
    
    # Mock successful token refresh
    mock_vm.check_and_refresh_token = Mock()
    
    # Test 1: Token expiration detection
    print("\n1. Testing token expiration detection...")
    
    # Test various token expiration error messages
    test_cases = [
        ("Token is expired", True),
        ("key not authorized: token is expired", True),
        ("Unknown error in API response: Key not authorized: token has expired", True),
        ("Authentication failed", True),
        ("Unauthorized", True),
        ("Some other error", False),
        ("Network timeout", False),
    ]
    
    for error_msg, expected in test_cases:
        error = Exception(error_msg)
        result = await client._is_token_expired_error(error)
        status = "✓" if result == expected else "✗"
        print(f"   {status} '{error_msg}' -> {result} (expected {expected})")
    
    # Test 2: Token refresh with concurrency protection
    print("\n2. Testing token refresh with concurrency protection...")
    
    # Mock successful token refresh
    mock_vm.reset_mock()
    
    # Test single refresh
    try:
        await client._refresh_token_safely()
        print("   ✓ Token refresh completed successfully")
    except Exception as e:
        print(f"   ✗ Token refresh failed: {e}")
    
    # Test that check_and_refresh_token was called
    if mock_vm.check_and_refresh_token.called:
        print("   ✓ check_and_refresh_token was called")
    else:
        print("   ✗ check_and_refresh_token was not called")
    
    # Test 3: Retry mechanism with mock failures
    print("\n3. Testing retry mechanism...")
    
    # Mock a method that will fail with token expiration and then succeed
    call_count = 0
    async def mock_operation():
        nonlocal call_count
        call_count += 1
        
        if call_count == 1:
            # First call fails with the production token expiration message
            raise Exception("Unknown error in API response: Key not authorized: token has expired")
        else:
            # Subsequent calls succeed
            return "success"
    
    # Reset call count
    call_count = 0
    
    try:
        result = await client._execute_with_retry(mock_operation)
        if result == "success" and call_count == 2:
            print("   ✓ Retry mechanism works correctly")
        else:
            print(f"   ✗ Retry mechanism failed: call_count={call_count}, result={result}")
    except Exception as e:
        print(f"   ✗ Retry mechanism failed: {e}")
    
    # Test 4: Non-token errors are not retried
    print("\n4. Testing non-token error handling...")
    
    async def mock_operation_non_token():
        raise Exception("Network timeout")
    
    try:
        await client._execute_with_retry(mock_operation_non_token)
        print("   ✗ Non-token error was incorrectly retried")
    except Exception as e:
        if str(e) == "Network timeout":
            print("   ✓ Non-token errors are not retried")
        else:
            print(f"   ✗ Unexpected error: {e}")
    
    print("\nToken refresh and retry mechanism tests completed!")

async def test_api_client_methods():
    """Test that all API client methods have token refresh integration."""
    print("\nTesting API client methods with token refresh...")
    
    # Create test configuration
    config = HyundaiConfig(
        region=Region.EUROPE,
        brand=Brand.HYUNDAI,
        username="test@example.com",
        password="test_password",
        pin="1234"
    )
    
    # Create API client
    client = HyundaiAPIClient(config)
    
    # Mock the vehicle manager
    mock_vm = Mock(spec=VehicleManager)
    client.vehicle_manager = mock_vm
    
    # Mock successful operations
    mock_vm.check_and_refresh_token = Mock()
    mock_vm.update_vehicle_with_cached_state = Mock()
    mock_vm.force_refresh_vehicle_state = Mock()
    mock_vm.check_and_force_update_vehicle = Mock()
    mock_vehicle = Mock()
    mock_vehicle.last_updated_at = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
    mock_vm.get_vehicle = Mock(return_value=mock_vehicle)
    
    # Test methods that should have token refresh
    test_methods = [
        ("refresh_cached", ("test_vehicle_id",)),
        ("refresh_force", ("test_vehicle_id",)),
        ("refresh_smart", ("test_vehicle_id", 60)),
    ]
    
    for method_name, args in test_methods:
        print(f"\n   Testing {method_name}...")
        
        # Reset mock
        mock_vm.check_and_refresh_token.reset_mock()
        
        client._last_refresh_time = None
        mock_vehicle.last_updated_at = datetime.datetime(
            2026, 1, 1, tzinfo=datetime.timezone.utc
        )

        # Mock first call to fail with token expiration, second to succeed
        call_count = 0
        def mock_operation_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Unknown error in API response: Key not authorized: token has expired")
            if method_name == "refresh_smart":
                mock_vehicle.last_updated_at = mock_vehicle.last_updated_at + datetime.timedelta(
                    minutes=5
                )
            return None
        
        # Set up the appropriate mock based on method
        if method_name == "refresh_cached":
            mock_vm.update_vehicle_with_cached_state.side_effect = mock_operation_side_effect
        elif method_name == "refresh_force":
            mock_vm.force_refresh_vehicle_state.side_effect = mock_operation_side_effect
        elif method_name == "refresh_smart":
            mock_vm.check_and_force_update_vehicle.side_effect = mock_operation_side_effect
        
        try:
            # Call the method
            method = getattr(client, method_name)
            await method(*args)
            
            # Check if token refresh was called
            if mock_vm.check_and_refresh_token.called:
                print(f"     ✓ {method_name} triggered token refresh on failure")
            else:
                print(f"     ✗ {method_name} did not trigger token refresh")
                
        except Exception as e:
            print(f"     ✗ {method_name} failed: {e}")
    
    print("\nAPI client methods tests completed!")

def test_is_token_expired_error_detects_observed_message():
    config = HyundaiConfig(
        region=Region.EUROPE,
        brand=Brand.HYUNDAI,
        username="test@example.com",
        password="test_password",
        pin="1234"
    )
    client = HyundaiAPIClient(config)

    error = Exception(
        "Unknown error in API response: Key not authorized: token has expired"
    )

    assert asyncio.run(client._is_token_expired_error(error)) is True

def test_execute_with_retry_reauths_on_observed_message():
    config = HyundaiConfig(
        region=Region.EUROPE,
        brand=Brand.HYUNDAI,
        username="test@example.com",
        password="test_password",
        pin="1234"
    )
    client = HyundaiAPIClient(config)

    mock_vm = Mock(spec=VehicleManager)
    mock_vm.check_and_refresh_token = Mock()
    client.vehicle_manager = mock_vm

    call_count = 0

    async def operation():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception(
                "Unknown error in API response: Key not authorized: token has expired"
            )
        return "success"

    result = asyncio.run(client._execute_with_retry(operation))

    assert result == "success"
    assert call_count == 2
    mock_vm.check_and_refresh_token.assert_called_once()


async def main():
    """Main test function."""
    setup_logging()
    
    print("=" * 60)
    print("HYUNDAI API CLIENT - TOKEN REFRESH AND RETRY TESTS")
    print("=" * 60)
    
    try:
        await test_token_refresh_mechanism()
        await test_api_client_methods()
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())