"""Tests for weight training description parser."""
import unittest

from scripts.parse_weight_training import (
    parse_set_line,
    parse_weight_training_description,
    get_weight_training_metrics,
)


class TestParseSetLine(unittest.TestCase):
    """Test parsing individual set lines."""

    def test_parse_basic_lbs(self):
        """Test parsing basic pounds format."""
        result = parse_set_line("Set 1: 175 lbs x 7")
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 175.0)
        self.assertEqual(result[1], 7)

    def test_parse_with_failure_annotation(self):
        """Test parsing with [Failure] annotation."""
        result = parse_set_line("Set 3: 170 lbs x 6 [Failure]")
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 170.0)
        self.assertEqual(result[1], 6)

    def test_parse_kg(self):
        """Test parsing kilograms (should convert to lbs)."""
        result = parse_set_line("Set 1: 80 kg x 10")
        self.assertIsNotNone(result)
        # 80 kg = 176.37 lbs
        self.assertAlmostEqual(result[0], 176.37, places=1)
        self.assertEqual(result[1], 10)

    def test_parse_no_unit(self):
        """Test parsing without explicit unit (assumes lbs)."""
        result = parse_set_line("Set 1: 100 x 10")
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 100.0)
        self.assertEqual(result[1], 10)

    def test_parse_lowercase_x(self):
        """Test parsing with lowercase 'x'."""
        result = parse_set_line("50 lbs x 8")
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 50.0)
        self.assertEqual(result[1], 8)

    def test_parse_capital_X(self):
        """Test parsing with capital 'X'."""
        result = parse_set_line("50 lbs X 8")
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 50.0)
        self.assertEqual(result[1], 8)

    def test_parse_decimal_weight(self):
        """Test parsing decimal weight."""
        result = parse_set_line("Set 1: 62.5 lbs x 8")
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 62.5)
        self.assertEqual(result[1], 8)

    def test_parse_invalid_line(self):
        """Test that invalid lines return None."""
        result = parse_set_line("Exercise Name")
        self.assertIsNone(result)

    def test_parse_empty_line(self):
        """Test that empty lines return None."""
        result = parse_set_line("")
        self.assertIsNone(result)


class TestParseWeightTrainingDescription(unittest.TestCase):
    """Test parsing full weight training descriptions."""

    def test_hevy_format(self):
        """Test parsing Hevy app export format."""
        description = """Logged with Hevy

Chest Press (Machine)
Set 1: 175 lbs x 7
Set 2: 175 lbs x 6
Set 3: 170 lbs x 6 [Failure]

Seated Shoulder Press (Machine)
Set 1: 125 lbs x 4
Set 2: 125 lbs x 5 [Failure]
Set 3: 120 lbs x 5 [Failure]

Lateral Raise (Dumbbell)
Set 1: 50 lbs x 8
Set 2: 50 lbs x 7
Set 3: 50 lbs x 5

Triceps Extension (Dumbbell)
Set 1: 55 lbs x 8
Set 2: 55 lbs x 8
Set 3: 55 lbs x 6"""
        
        metrics = parse_weight_training_description(description)
        
        # Calculate expected volume:
        # Chest Press: 175*7 + 175*6 + 170*6 = 1225 + 1050 + 1020 = 3295
        # Shoulder Press: 125*4 + 125*5 + 120*5 = 500 + 625 + 600 = 1725
        # Lateral Raise: 50*8 + 50*7 + 50*5 = 400 + 350 + 250 = 1000
        # Triceps: 55*8 + 55*8 + 55*6 = 440 + 440 + 330 = 1210
        # Total: 7230 lbs
        
        self.assertEqual(metrics['total_volume_lbs'], 7230.0)
        self.assertEqual(metrics['total_sets'], 12)
        self.assertEqual(metrics['total_reps'], 75)
        self.assertEqual(metrics['exercise_count'], 4)

    def test_empty_description(self):
        """Test parsing empty description returns zeros."""
        metrics = parse_weight_training_description("")
        self.assertEqual(metrics['total_volume_lbs'], 0.0)
        self.assertEqual(metrics['total_sets'], 0)
        self.assertEqual(metrics['total_reps'], 0)
        self.assertEqual(metrics['exercise_count'], 0)

    def test_none_description(self):
        """Test parsing None description returns zeros."""
        metrics = parse_weight_training_description(None)
        self.assertEqual(metrics['total_volume_lbs'], 0.0)
        self.assertEqual(metrics['total_sets'], 0)
        self.assertEqual(metrics['total_reps'], 0)
        self.assertEqual(metrics['exercise_count'], 0)

    def test_simple_workout(self):
        """Test parsing simple workout with one exercise."""
        description = """Bench Press
Set 1: 135 lbs x 10
Set 2: 135 lbs x 10
Set 3: 135 lbs x 10"""
        
        metrics = parse_weight_training_description(description)
        
        # 135 * 10 * 3 = 4050
        self.assertEqual(metrics['total_volume_lbs'], 4050.0)
        self.assertEqual(metrics['total_sets'], 3)
        self.assertEqual(metrics['total_reps'], 30)
        self.assertEqual(metrics['exercise_count'], 1)

    def test_mixed_kg_lbs(self):
        """Test parsing workout with mixed kg and lbs."""
        description = """Exercise A
Set 1: 100 kg x 5
Exercise B
Set 1: 100 lbs x 5"""
        
        metrics = parse_weight_training_description(description)
        
        # 100 kg = 220.462 lbs, 220.462*5 + 100*5 = 1102.31 + 500 = 1602.31
        self.assertAlmostEqual(metrics['total_volume_lbs'], 1602.31, places=1)
        self.assertEqual(metrics['total_sets'], 2)
        self.assertEqual(metrics['total_reps'], 10)
        self.assertEqual(metrics['exercise_count'], 2)

    def test_no_exercise_names(self):
        """Test parsing sets without exercise names."""
        description = """Set 1: 100 lbs x 10
Set 2: 100 lbs x 10"""
        
        metrics = parse_weight_training_description(description)
        
        self.assertEqual(metrics['total_volume_lbs'], 2000.0)
        self.assertEqual(metrics['total_sets'], 2)
        self.assertEqual(metrics['total_reps'], 20)
        # No exercise names identified
        self.assertEqual(metrics['exercise_count'], 0)


class TestGetWeightTrainingMetrics(unittest.TestCase):
    """Test extracting metrics from activity dict."""

    def test_activity_with_description(self):
        """Test extracting metrics from activity with description."""
        activity = {
            'description': """Exercise
Set 1: 100 lbs x 10
Set 2: 100 lbs x 10"""
        }
        
        metrics = get_weight_training_metrics(activity)
        self.assertEqual(metrics['total_volume_lbs'], 2000.0)
        self.assertEqual(metrics['total_sets'], 2)

    def test_activity_without_description(self):
        """Test extracting metrics from activity without description."""
        activity = {'name': 'Workout'}
        
        metrics = get_weight_training_metrics(activity)
        self.assertEqual(metrics['total_volume_lbs'], 0.0)
        self.assertEqual(metrics['total_sets'], 0)

    def test_activity_with_empty_description(self):
        """Test extracting metrics from activity with empty description."""
        activity = {'description': ''}
        
        metrics = get_weight_training_metrics(activity)
        self.assertEqual(metrics['total_volume_lbs'], 0.0)


if __name__ == '__main__':
    unittest.main()
