"""
Unit tests for the example Post-Processing Trigger Cloud Function.
"""

import unittest
from unittest.mock import MagicMock

# Import the function to test
from functions.examples.trigger_template.main import main


class TestTriggerFunction(unittest.TestCase):
    """Test suite for the GCS Event trigger template (Pattern C)."""

    def test_main_success(self):
        """
        Verifies that the function processes a CloudEvent correctly.
        """
        # Create a mock CloudEvent
        mock_event = MagicMock()
        mock_event.data = {
            "bucket": "test-bucket",
            "name": "test-file.json",
            "metageneration": "1",
            "timeCreated": "2024-01-01T00:00:00.000Z",
        }
        mock_event.__getitem__.side_effect = lambda key: {
            "id": "evt_456",
            "type": "google.storage.object.v1.finalized",
        }[key]

        # Call the function (CloudEvent functions don't return a Response)
        try:
            main(mock_event)
            success = True
        except Exception:
            success = False

        self.assertTrue(success)


if __name__ == "__main__":
    unittest.main()
