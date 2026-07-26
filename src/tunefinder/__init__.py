"""tunefinder: universal music recognition tool."""

from .pipeline import RecognitionResult, recognize_from_file, recognize_from_url

__all__ = ["recognize_from_url", "recognize_from_file", "RecognitionResult"]
__version__ = "0.1.0"
