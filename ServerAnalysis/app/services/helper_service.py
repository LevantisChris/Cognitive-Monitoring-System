from datetime import time

class HelperService:
    """Helper service for parsing and formatting data."""

    @staticmethod
    def parse_time_field(session_data, field_name, session_id):
        """Parse time data from session_data.

        Args:
            session_data: Dictionary containing session data
            field_name: Name of the field containing time data
            session_id: ID of the session for logging purposes

        Returns:
            datetime.time object or None if parsing fails
        """
        if not session_data or field_name not in session_data:
            print(f"\033[93mWarning: {field_name} not found in data for session {session_id}\033[0m")
            return None

        time_data = session_data.get(field_name)
        if not time_data:
            print(f"\033[93mWarning: {field_name} is empty for session {session_id}\033[0m")
            return None

        try:
            return time(
                hour=int(time_data.get('hour', 0)),
                minute=int(time_data.get('minute', 0)),
                second=int(time_data.get('second', 0)),
                microsecond=int(time_data.get('nano', 0) / 1000)  # Convert nano to micro
            )
        except (TypeError, ValueError) as e:
            print(f"\033[93mWarning: Could not parse {field_name} for session {session_id}: {e}\033[0m")
            return None