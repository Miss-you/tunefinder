"""tunefinder: universal music recognition tool."""
from .pipeline import recognize_from_url, recognize_from_file, RecognitionResult

__all__ = ["recognize_from_url", "recognize_from_file", "RecognitionResult"]
__version__ = "0.1.0"
