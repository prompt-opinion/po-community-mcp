from dataclasses import dataclass


@dataclass
class FhirContext:
    url: str
    token: str | None = None
