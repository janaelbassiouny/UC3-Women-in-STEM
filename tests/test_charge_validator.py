import unittest

from rules.charge_validator import validate_charge


class TestChargeValidator(unittest.TestCase):

    def test_missing_documentation(self):
        report = {
            "selected_charge": "8_USC_1325",
            "entry_event": "Attempted entry"
        }

        result = validate_charge(report)

        flag_types = [flag["type"] for flag in result["flags"]]

        self.assertIn("missing_documentation", flag_types)
        self.assertEqual(result["status"], "human_review_required")

    def test_possible_contradiction(self):
        report = {
            "selected_charge": "8_USC_1325",
            "entry_event": "Attempted entry",
            "entry_time_or_place": "Location documented",
            "entry_location": "Location A",
            "verified_entry_location": "Location B"
        }

        result = validate_charge(report)

        flag_types = [flag["type"] for flag in result["flags"]]

        self.assertIn("possible_contradiction", flag_types)

    def test_ambiguous_information(self):
        report = {
            "selected_charge": "8_USC_1325",
            "entry_event": "The individual may have attempted entry.",
            "entry_time_or_place": "Location documented"
        }

        result = validate_charge(report)

        flag_types = [flag["type"] for flag in result["flags"]]

        self.assertIn("ambiguous_information", flag_types)
        self.assertEqual(result["status"], "human_review_required")

    def test_matching_locations(self):
        report = {
            "selected_charge": "8_USC_1325",
            "entry_event": "Attempted entry",
            "entry_time_or_place": "Location documented",
            "entry_location": "Location A",
            "verified_entry_location": "Location A"
        }

        result = validate_charge(report)

        flag_types = [flag["type"] for flag in result["flags"]]

        self.assertNotIn("possible_contradiction", flag_types)

    def test_unknown_charge(self):
        report = {
            "selected_charge": "UNKNOWN_CHARGE",
            "entry_event": "Attempted entry"
        }

        result = validate_charge(report)

        self.assertEqual(result["status"], "human_review_required")
        self.assertTrue(result["flags"])

    def test_no_selected_charge(self):
        report = {
            "entry_event": "Attempted entry"
        }

        result = validate_charge(report)

        self.assertEqual(result["status"], "human_review_required")
        self.assertTrue(result["flags"])


if __name__ == "__main__":
    unittest.main()