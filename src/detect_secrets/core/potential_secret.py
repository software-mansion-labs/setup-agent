from typing import Any
from typing import Optional

class PotentialSecret:
    """This custom data type represents a string found, matching the
    plugin rules defined in SecretsCollection, that has the potential
    to be a secret that we actually care about.

    "Potential" is the operative word here, because of the nature of
    false positives.

    We use this custom class so that we can more easily generate data
    structures and do object-based comparisons with other PotentialSecrets,
    without actually knowing what the secret is.
    """

    def __init__(
        self,
        secret_type: str,
        secret: str,
        is_secret: Optional[bool] = None,
        is_verified: bool = False,
    ) -> None:
        """
        :param type: human-readable secret type, defined by the plugin
            that generated this PotentialSecret. e.g. "High Entropy String"
        :param secret: the actual secret identified
        :param is_secret: whether or not the secret is a true- or false- positive
        :param is_verified: whether the secret has been externally verified
        """
        self.secret_type = secret_type
        self.secret_value = secret
        self.is_secret = is_secret
        self.is_verified = is_verified

        # If two PotentialSecrets have the same values for these fields,
        # they are considered equal. Note that line numbers aren't included
        # in this, because line numbers are subject to change.
        self.fields_to_compare = ['secret_value', 'secret_type']

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
            tuple(
                getattr(self, x)
                for x in self.fields_to_compare
            ),
        )
