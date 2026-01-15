import os
import string
from typing import Optional

from detect_secrets.plugins.base import BasePlugin
from detect_secrets.filters.base_secret_filter import BaseSecretFilter
from detect_secrets.plugins import PrivateKeyDetector
from gibberish_detector import serializer
from gibberish_detector.model import Model
from gibberish_detector.detector import Detector
from gibberish_detector.exceptions import ParsingError


class GibberishFilter(BaseSecretFilter):
    """
    Filter that uses a trained machine learning model to distinguish between
    random gibberish (actual secrets) and regular English words (false positives).

    Attributes:
        limit (float): Threshold for the detector.
        model (Model): The Gibberish Detector model.
        detector (Detector): The Gibberish Detector.
    """

    def __init__(self, model_path: str = "rfc.model", limit: float = 3.7) -> None:
        """
        Initializes the Gibberish Detector model.

        Args:
            model_path (str): Path to the trained 'rfc.model' file.
            limit (float): Threshold for the detector.
        """
        self.limit = limit
        self.model = Model(charset="")

        if not os.path.exists(model_path):
            current_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(current_dir, "rfc.model")

        try:
            with open(model_path, "r") as f:
                self.model.update(serializer.deserialize(f.read()))
        except (IOError, ParsingError) as e:
            raise ValueError(f"Could not load gibberish model from {model_path}: {e}")

        self.detector = Detector(model=self.model, threshold=self.limit)

    def should_exclude(self, secret: str, plugin: Optional[BasePlugin] = None) -> bool:
        """
        Returns True if the secret looks like a regular English word (not gibberish).
        Args:
            secret (str): The secret to check.
            plugin (Optional[BasePlugin]): The plugin used.

        Returns:
            bool: Whether the secret should be excluded.
        """
        if plugin and isinstance(plugin, PrivateKeyDetector):
            return False

        # Heuristic: Hex strings (0-9, A-F) often have low entropy and look like "words"
        # to the model, so we skip the check for them to avoid false negatives.
        # If the secret contains ONLY hex digits and dashes, we keep it (return False).
        if not (set(secret) - set(string.hexdigits + "-")):
            return False

        # The model is trained on lowercase strings.
        # If detector.is_gibberish returns False (it is NOT gibberish),
        # it means it is likely a regular word, so we should exclude it (return True).
        return not self.detector.is_gibberish(secret.lower())
