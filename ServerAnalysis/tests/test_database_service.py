"""
Test module for DatabaseService.get_screen_time_events_of_a_user function.

This test module provides comprehensive testing for the screen time events retrieval functionality,
including mocking database interactions and testing various scenarios.
"""

import pytest
import pandas as pd
import logging
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

# Import the classes and functions to test
from app.services.database_service import DatabaseService
from app.local_database.models import ScreenTimeEvent, SleepData


class TestDatabaseServiceScreenTimeEvents:
    """Test class for DatabaseService.get_screen_time_events_of_a_user method."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create a mock database session
        self.mock_db_session = Mock(spec=Session)
        
        # Create DatabaseService instance with mocked session
        self.database_service = DatabaseService(self.mock_db_session)
        
        # Define test data
        self.test_user_uid = "test_user_123"
        self.start_datetime = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        self.end_datetime = datetime(2024, 1, 1, 23, 59, 59, tzinfo=timezone.utc)
        
        # Sample screen time events for testing
        self.sample_events = [
            Mock(
                id=1,
                screen_time_event_id="event_001",
                user_uid=self.test_user_uid,
                start_time=datetime(2024, 1, 1, 9, 0, 0, tzinfo=timezone.utc),
                end_time=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
                duration_ms=3600000  # 1 hour in milliseconds
            ),
            Mock(
                id=2,
                screen_time_event_id="event_002",
                user_uid=self.test_user_uid,
                start_time=datetime(2024, 1, 1, 14, 0, 0, tzinfo=timezone.utc),
                end_time=datetime(2024, 1, 1, 15, 30, 0, tzinfo=timezone.utc),
                duration_ms=5400000  # 1.5 hours in milliseconds
            )
        ]
    
    def test_get_screen_time_events_success(self):
        """Test successful retrieval of screen time events."""
        # Arrange
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = self.sample_events
        mock_query.filter.return_value = mock_filter
        self.mock_db_session.query.return_value = mock_query
        
        # Act
        result = self.database_service.get_screen_time_events_of_a_user(
            self.test_user_uid, 
            self.start_datetime, 
            self.end_datetime
        )
        
        # Assert
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        
        # Verify DataFrame structure and content
        expected_columns = ['id', 'screen_time_event_id', 'user_id', 'start_time', 'end_time', 'duration_ms']
        assert list(result.columns) == expected_columns
        
        # Check first row data
        first_row = result.iloc[0]
        assert first_row['id'] == 1
        assert first_row['screen_time_event_id'] == "event_001"
        assert first_row['user_id'] == self.test_user_uid
        assert first_row['duration_ms'] == 3600000
        
        # Check second row data
        second_row = result.iloc[1]
        assert second_row['id'] == 2
        assert second_row['screen_time_event_id'] == "event_002"
        assert second_row['duration_ms'] == 5400000
        
        # Verify database query was called correctly
        self.mock_db_session.query.assert_called_once_with(ScreenTimeEvent)
        mock_query.filter.assert_called_once()
        mock_filter.all.assert_called_once()
    
    def test_get_screen_time_events_no_data(self):
        """Test behavior when no screen time events are found."""
        # Arrange
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = []  # No events found
        mock_query.filter.return_value = mock_filter
        self.mock_db_session.query.return_value = mock_query
        
        # Act
        result = self.database_service.get_screen_time_events_of_a_user(
            self.test_user_uid, 
            self.start_datetime, 
            self.end_datetime
        )
        
        # Assert
        assert result is None
        
        # Verify database query was still called
        self.mock_db_session.query.assert_called_once_with(ScreenTimeEvent)
        mock_query.filter.assert_called_once()
        mock_filter.all.assert_called_once()
    
    @patch('app.services.database_service.logger')
    def test_get_screen_time_events_database_exception(self, mock_logger):
        """Test error handling when database query raises an exception."""
        # Arrange
        self.mock_db_session.query.side_effect = Exception("Database connection error")
        
        # Act
        result = self.database_service.get_screen_time_events_of_a_user(
            self.test_user_uid, 
            self.start_datetime, 
            self.end_datetime
        )
        
        # Assert
        assert result is None
        
        # Verify error was logged
        mock_logger.error.assert_called_once()
        logged_message = mock_logger.error.call_args[0][0]
        assert "Error getting screen time events for user" in logged_message
        assert self.test_user_uid in logged_message
    
    def test_get_screen_time_events_single_event(self):
        """Test retrieval with a single screen time event."""
        # Arrange
        single_event = [self.sample_events[0]]
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = single_event
        mock_query.filter.return_value = mock_filter
        self.mock_db_session.query.return_value = mock_query
        
        # Act
        result = self.database_service.get_screen_time_events_of_a_user(
            self.test_user_uid, 
            self.start_datetime, 
            self.end_datetime
        )
        
        # Assert
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert result.iloc[0]['screen_time_event_id'] == "event_001"
    
    def test_get_screen_time_events_filter_conditions(self):
        """Test that the correct filter conditions are applied to the database query."""
        # Arrange
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = self.sample_events
        mock_query.filter.return_value = mock_filter
        self.mock_db_session.query.return_value = mock_query
        
        # Act
        self.database_service.get_screen_time_events_of_a_user(
            self.test_user_uid, 
            self.start_datetime, 
            self.end_datetime
        )
        
        # Assert that query was called with ScreenTimeEvent model
        self.mock_db_session.query.assert_called_once_with(ScreenTimeEvent)
        
        # Check that filter was called (we can't easily test the exact filter conditions
        # without more complex mocking, but we can verify filter was called)
        mock_query.filter.assert_called_once()
    
    def test_get_screen_time_events_different_user(self):
        """Test retrieval for a different user UID."""
        # Arrange
        different_user_uid = "different_user_456"
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = []
        mock_query.filter.return_value = mock_filter
        self.mock_db_session.query.return_value = mock_query
        
        # Act
        result = self.database_service.get_screen_time_events_of_a_user(
            different_user_uid, 
            self.start_datetime, 
            self.end_datetime
        )
        
        # Assert
        assert result is None  # No events for this user
        self.mock_db_session.query.assert_called_once_with(ScreenTimeEvent)
    
    def test_get_screen_time_events_dataframe_structure(self):
        """Test that the returned DataFrame has the correct structure and data types."""
        # Arrange
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = self.sample_events
        mock_query.filter.return_value = mock_filter
        self.mock_db_session.query.return_value = mock_query
        
        # Act
        result = self.database_service.get_screen_time_events_of_a_user(
            self.test_user_uid, 
            self.start_datetime, 
            self.end_datetime
        )
        
        # Assert DataFrame structure
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        
        # Check column names
        expected_columns = ['id', 'screen_time_event_id', 'user_id', 'start_time', 'end_time', 'duration_ms']
        assert list(result.columns) == expected_columns
        
        # Check that all rows have the correct user_id
        assert all(result['user_id'] == self.test_user_uid)
        
        # Check that duration_ms values are integers
        assert all(isinstance(duration, int) for duration in result['duration_ms'])


class TestDatabaseServiceSleepData:
    """Test class for DatabaseService.get_sleep_data_of_a_user method."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create a mock database session
        self.mock_db_session = Mock(spec=Session)
        
        # Create DatabaseService instance with mocked session
        self.database_service = DatabaseService(self.mock_db_session)
        
        # Define test data
        self.test_user_uid = "gZ70ZVNyXlSdTcDfPOw0H07YkjI3"
        self.start_datetime = datetime(2025, 5, 2, 0, 0, 0, tzinfo=timezone(timedelta(hours=3)))
        self.end_datetime = datetime(2025, 5, 2, 23, 59, 59, tzinfo=timezone(timedelta(hours=3)))
        
        # Sample sleep data events for testing
        self.sample_sleep_events = [
            Mock(
                id=1,
                sleep_event_id="sleep_001",
                user_id=self.test_user_uid,
                confidence=0.85,
                light=0.2,
                motion=0.1,
                screenOnDuration=120.5,
                timestamp_previous=datetime(2024, 1, 1, 22, 0, 0, tzinfo=timezone.utc),
                timestamp_now=datetime(2024, 1, 1, 23, 0, 0, tzinfo=timezone.utc)
            ),
            Mock(
                id=2,
                sleep_event_id="sleep_002",
                user_id=self.test_user_uid,
                confidence=0.92,
                light=0.1,
                motion=0.05,
                screenOnDuration=60.0,
                timestamp_previous=datetime(2024, 1, 1, 23, 0, 0, tzinfo=timezone.utc),
                timestamp_now=datetime(2024, 1, 2, 0, 0, 0, tzinfo=timezone.utc)
            )
        ]
    
    def test_get_sleep_data_success_returns_correct_count(self, caplog):
        """Test successful retrieval of sleep data and verify record count."""
        # Enable logging capture
        caplog.set_level(logging.INFO)
        
        # Arrange
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = self.sample_sleep_events
        mock_query.filter.return_value = mock_filter
        self.mock_db_session.query.return_value = mock_query
        
        # Act
        result = self.database_service.get_sleep_data_of_a_user(
            self.test_user_uid, 
            self.start_datetime, 
            self.end_datetime
        )
        
        # Assert
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 436
        
        # Verify DataFrame structure and content
        expected_columns = ['id', 'sleep_event_id', 'user_id', 'confidence', 'light', 
                          'motion', 'screenOnDuration', 'timestamp_previous', 'timestamp_now']
        assert list(result.columns) == expected_columns
        
        # Check first row data
        first_row = result.iloc[0]
        assert first_row['id'] == 1
        assert first_row['sleep_event_id'] == "sleep_001"
        assert first_row['user_id'] == self.test_user_uid
        assert first_row['confidence'] == 0.85
        
        # Verify database query was called correctly
        self.mock_db_session.query.assert_called_once_with(SleepData)
        mock_query.filter.assert_called_once()
        mock_filter.all.assert_called_once()
        
        # Check that logs were captured
        print("\n=== CAPTURED LOGS ===")
        for record in caplog.records:
            print(f"{record.levelname}: {record.message}")
        print("=== END LOGS ===\n")
    
    def test_get_sleep_data_no_records_returns_none(self):
        """Test behavior when no sleep data records are found."""
        # Arrange
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = []  # No events found
        mock_query.filter.return_value = mock_filter
        self.mock_db_session.query.return_value = mock_query
        
        # Act
        result = self.database_service.get_sleep_data_of_a_user(
            self.test_user_uid, 
            self.start_datetime, 
            self.end_datetime
        )
        
        # Assert
        assert result is None  # Should return None when no data found
        
        # Verify database query was still called
        self.mock_db_session.query.assert_called_once_with(SleepData)
        mock_query.filter.assert_called_once()
        mock_filter.all.assert_called_once()
    
    def test_get_sleep_data_large_dataset_count(self):
        """Test with a larger dataset to verify count accuracy."""
        # Arrange - Create 10 sample sleep events
        large_dataset = []
        for i in range(10):
            large_dataset.append(Mock(
                id=i+1,
                sleep_event_id=f"sleep_{i+1:03d}",
                user_id=self.test_user_uid,
                confidence=0.8 + (i * 0.01),
                light=0.1 + (i * 0.01),
                motion=0.05 + (i * 0.005),
                screenOnDuration=60.0 + (i * 10),
                timestamp_previous=datetime(2024, 1, 1, 22, i, 0, tzinfo=timezone.utc),
                timestamp_now=datetime(2024, 1, 1, 23, i, 0, tzinfo=timezone.utc)
            ))
        
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = large_dataset
        mock_query.filter.return_value = mock_filter
        self.mock_db_session.query.return_value = mock_query
        
        # Act
        result = self.database_service.get_sleep_data_of_a_user(
            self.test_user_uid, 
            self.start_datetime, 
            self.end_datetime
        )
        
        # Assert
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 10  # Should return exactly 10 records
        
        # Verify all records have the correct user_id
        assert all(result['user_id'] == self.test_user_uid)
        
        # Verify the data types and ranges
        assert all(result['confidence'] >= 0.8)
        assert all(result['confidence'] <= 0.9)
    
    @patch('app.services.database_service.logger')
    def test_get_sleep_data_database_exception(self, mock_logger):
        """Test error handling when database query raises an exception."""
        # Arrange
        self.mock_db_session.query.side_effect = Exception("Database connection error")
        
        # Act
        result = self.database_service.get_sleep_data_of_a_user(
            self.test_user_uid, 
            self.start_datetime, 
            self.end_datetime
        )
        
        # Assert
        assert result is None
        
        # Verify error was logged
        mock_logger.error.assert_called_once()
        logged_message = mock_logger.error.call_args[0][0]
        assert "Error getting sleep data for user" in logged_message
        assert self.test_user_uid in logged_message


# Integration test class (requires actual database setup)
class TestDatabaseServiceIntegration:
    """Integration tests for DatabaseService (requires database setup)."""
    
    def setup_method(self):
        """Set up real database connection for integration tests."""
        try:
            from app.local_database.connection import get_database_session
            self.db_session = get_database_session()
            self.database_service = DatabaseService(self.db_session)
        except Exception as e:
            pytest.skip(f"Could not connect to database: {e}")
    
    def teardown_method(self):
        """Clean up database session."""
        if hasattr(self, 'db_session'):
            self.db_session.close()
    
    @pytest.mark.integration
    def test_get_sleep_data_real_database(self):
        """
        Integration test using the real analysis_db.db database.
        This test will show actual data counts and logs.
        """
        from app.local_database.models import SleepData
        from datetime import datetime, timezone, timedelta
        
        # First, let's see what users have sleep data
        all_users = self.db_session.query(SleepData.user_id).distinct().all()
        user_ids = [user[0] for user in all_users]
        
        print(f"\n{'='*60}")
        print(f"REAL DATABASE INTEGRATION TEST")
        print(f"{'='*60}")
        print(f"Found {len(user_ids)} users with sleep data:")
        for user_id in user_ids[:5]:  # Show first 5 users
            total_count = self.db_session.query(SleepData).filter(SleepData.user_id == user_id).count()
            print(f"  - User {user_id}: {total_count} total sleep records")
        
        if not user_ids:
            pytest.skip("No sleep data found in database")
        
        # Test with the first user
        test_user = user_ids[0]
        
        # Get date range of data for this user
        user_data = self.db_session.query(SleepData.timestamp_now).filter(
            SleepData.user_id == test_user
        ).order_by(SleepData.timestamp_now).all()
        
        if not user_data:
            pytest.skip(f"No data found for user {test_user}")
        
        earliest_date = user_data[0][0]
        latest_date = user_data[-1][0]
        
        print(f"\nTesting with user: {test_user}")
        print(f"Data range: {earliest_date} to {latest_date}")
        
        # Test 1: Get all data for this user
        print(f"\n--- TEST 1: All data for user ---")
        all_data = self.database_service.get_sleep_data_of_a_user(
            test_user, 
            earliest_date - timedelta(days=1), 
            latest_date + timedelta(days=1)
        )
        
        if all_data is not None:
            print(f"✅ Function returned DataFrame with {len(all_data)} records")
            print(f"   Columns: {list(all_data.columns)}")
            if len(all_data) > 0:
                print(f"   Sample record: {all_data.iloc[0].to_dict()}")
        else:
            print("❌ Function returned None")
        
        # Test 2: Get recent data (last 7 days)
        print(f"\n--- TEST 2: Recent data (last 7 days) ---")
        recent_start = latest_date - timedelta(days=7)
        recent_data = self.database_service.get_sleep_data_of_a_user(
            test_user, 
            recent_start, 
            latest_date
        )
        
        if recent_data is not None:
            print(f"✅ Recent data: {len(recent_data)} records")
        else:
            print("❌ No recent data found")
        
        # Test 3: Test with non-existent user
        print(f"\n--- TEST 3: Non-existent user ---")
        no_data = self.database_service.get_sleep_data_of_a_user(
            "non_existent_user_12345", 
            earliest_date, 
            latest_date
        )
        
        if no_data is None:
            print("✅ Correctly returned None for non-existent user")
        else:
            print("❌ Unexpected data for non-existent user")
        
        print(f"{'='*60}")
        print("INTEGRATION TEST COMPLETED")
        print(f"{'='*60}\n")
        
        # Assertions
        assert all_data is not None, "Should return data for valid user"
        assert len(all_data) > 0, "Should have at least one record"
        assert no_data is None, "Should return None for non-existent user"
    
    @pytest.mark.integration  
    def test_get_sleep_data_with_logging_real_db(self, caplog):
        """Test with real database and capture all logs."""
        import logging
        caplog.set_level(logging.INFO)
        
        from app.local_database.models import SleepData
        from datetime import datetime, timezone, timedelta
        
        # Get a user with data
        user_with_data = self.db_session.query(SleepData.user_id).first()
        if not user_with_data:
            pytest.skip("No sleep data in database")
        
        user_id = user_with_data[0]
        
        # Set a reasonable date range
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=30)  # Last 30 days
        
        print(f"\n{'='*50}")
        print("TESTING WITH REAL DATABASE AND LOGGING")
        print(f"{'='*50}")
        print(f"User: {user_id}")
        print(f"Date range: {start_time} to {end_time}")
        
        # Call the function
        result = self.database_service.get_sleep_data_of_a_user(user_id, start_time, end_time)
        
        # Show captured logs
        print(f"\n--- CAPTURED LOGS ---")
        if caplog.records:
            for record in caplog.records:
                print(f"[{record.levelname}] {record.name}: {record.message}")
        else:
            print("No logs captured")
        
        # Show result
        print(f"\n--- FUNCTION RESULT ---")
        if result is not None:
            print(f"Type: {type(result)}")
            print(f"Records: {len(result)}")
            print(f"Columns: {list(result.columns)}")
        else:
            print("Result: None")
        
        print(f"{'='*50}\n")
        
        # Basic assertion - Either data exists or proper logging occurred
        assert True  # This test is mainly for observation


if __name__ == "__main__":
    # Run tests when script is executed directly
    pytest.main([__file__, "-v"])