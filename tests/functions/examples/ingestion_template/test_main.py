"""
Unit tests for the example Ingestion Cloud Function.
"""

import json
import unittest
from unittest.mock import MagicMock

# Import the function to test
from functions.examples.ingestion_template.main import main


class TestIngestionFunction(unittest.TestCase):
    """Test suite for the Bronze layer ingestion template."""

    def test_main_success(self):
        """
        Verifies that the function processes a valid JSON payload correctly.
        """
        # Create a mock request object
        mock_request = MagicMock()
        mock_request.get_json.return_value = {"id": "evt_123", "key": "value"}

        # Call the function
        response = main(mock_request)

        # Assertions
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["event_id"], "evt_123")

    def test_main_no_data(self):
        """
        Verifies that the function returns 400 when no data is provided.
        """
        mock_request = MagicMock()
        mock_request.get_json.return_value = None

        response = main(mock_request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_data(as_text=True), "No data received")

    def test_main_internal_error(self):
        """
        Verifies that the function handles unexpected errors gracefully.
        """
        mock_request = MagicMock()
        # Simulate an error during JSON parsing
        mock_request.get_json.side_effect = Exception("System Failure")

        response = main(mock_request)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.get_data(as_text=True), "Internal Error")


if __name__ == "__main__":
    unittest.main()
