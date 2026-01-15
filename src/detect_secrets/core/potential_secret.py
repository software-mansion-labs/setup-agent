from typing import Any, Optional


class PotentialSecret:
    """
    This custom data type represents a string that matches the plugin rules
    defined in SecretsCollection, which might be an important secret.

    The word "Potential" is used because there can be false positives.

    This custom class is used to easily generate data structures and compare
    with other PotentialSecrets objects without actually knowing what the secret is.

    Attributes:
        secret_type (str): Human-readable type of the secret, set by the plugin
                            that generated this PotentialSecret. e.g., "High Entropy String"
        secret_value (str): The identified secret
        is_secret (Optional[bool]): Indicates whether the secret is a true or false positive
        is_verified (bool): It tells whether the secret has been externally verified or not
        fields_to_compare (list[str]): List of field names that are considered while comparing,
                                        such as 'secret_value', 'secret_type'.
                                        Note that line numbers are not included in this,
                                        because line numbers can change.
    """

    def __init__(
        self,
        secret_type: str,
        secret: str,
        is_secret: Optional[bool] = None,
        is_verified: bool = False,
    ) -> None:
        """
        Args:
            secret_type (str): Human-readable type of the secret, set by the plugin
                               that generated this PotentialSecret. e.g., "High Entropy String"
            secret (str): The identified secret
            is_secret (Optional[bool], optional): Indicates whether the secret
                                                  is a true or false positive. Defaults to None.
            is_verified (bool, optional): It tells whether the secret
                                          has been externally verified or not. Defaults to False.
        """
        self.secret_type = secret_type
        self.secret_value = secret
        self.is_secret = is_secret
        self.is_verified = is_verified

        # If two PotentialSecrets have the same values for these fields,
        # they are considered equal.
        self.fields_to_compare = ["secret_value", "secret_type"]

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, PotentialSecret):
            return NotImplemented

        return all(
            getattr(self, field) == getattr(other, field)
            for field in self.fields_to_compare
        )

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(
            tuple(getattr(self, x) for x in self.fields_to_compare),
        )
