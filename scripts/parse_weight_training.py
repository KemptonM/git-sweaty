"""Parse weight training data from activity descriptions.

Supports formats like:
- Hevy app exports: "Exercise Name\nSet 1: 175 lbs x 7\nSet 2: 175 lbs x 6"
- Generic formats with weight and reps
"""
import re
from typing import Dict, List, Optional, Tuple


def parse_set_line(line: str) -> Optional[Tuple[float, int]]:
    """Parse a single set line to extract weight and reps.
    
    Args:
        line: A line like "Set 1: 175 lbs x 7" or "175 kg x 10"
    
    Returns:
        Tuple of (weight_lbs, reps) or None if parsing fails
    """
    # Match patterns like "175 lbs x 7", "80 kg x 10", "175x7", etc.
    # Also handles "[Failure]" or other annotations
    pattern = r'(\d+(?:\.\d+)?)\s*(?:lbs?|pounds?|kg|kilograms?)?\s*[xX×]\s*(\d+)'
    match = re.search(pattern, line)
    
    if not match:
        return None
    
    weight = float(match.group(1))
    reps = int(match.group(2))
    
    # Convert kg to lbs if needed
    if 'kg' in line.lower() or 'kilogram' in line.lower():
        weight = weight * 2.20462
    
    return (weight, reps)


def parse_weight_training_description(description: str) -> Dict[str, float]:
    """Parse weight training description to extract metrics.
    
    Args:
        description: Activity description text, potentially containing workout data
    
    Returns:
        Dict with keys:
        - total_volume_lbs: Total weight × reps across all sets
        - total_sets: Total number of sets performed
        - total_reps: Total number of reps performed
        - exercise_count: Number of unique exercises identified
    """
    if not description:
        return {
            'total_volume_lbs': 0.0,
            'total_sets': 0,
            'total_reps': 0,
            'exercise_count': 0,
        }
    
    lines = description.split('\n')
    total_volume = 0.0
    total_sets = 0
    total_reps = 0
    exercises = set()
    current_exercise = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Try to parse as a set line
        set_data = parse_set_line(line)
        
        if set_data:
            weight, reps = set_data
            total_volume += weight * reps
            total_sets += 1
            total_reps += reps
            if current_exercise:
                exercises.add(current_exercise)
        else:
            # Check if this looks like an exercise name
            # Exercise names typically:
            # - Don't start with "Set" or contain "x" with numbers
            # - Are not just metadata like "Logged with Hevy"
            # - Don't match common non-exercise patterns
            if not re.search(r'\d+\s*[xX×]\s*\d+', line) and \
               not line.lower().startswith('set ') and \
               not line.lower().startswith('logged with') and \
               not line.lower().startswith('rep ') and \
               len(line) > 3:
                # Likely an exercise name
                current_exercise = line
    
    return {
        'total_volume_lbs': round(total_volume, 2),
        'total_sets': total_sets,
        'total_reps': total_reps,
        'exercise_count': len(exercises),
    }


def get_weight_training_metrics(activity: Dict) -> Dict[str, float]:
    """Extract weight training metrics from an activity dict.
    
    Args:
        activity: Activity dict that may contain a 'description' field
    
    Returns:
        Dict with weight training metrics (all zeros if no description or not parseable)
    """
    description = activity.get('description', '') or ''
    return parse_weight_training_description(description)
