import yaml
from dataclasses import dataclass


@dataclass
class Config:
    raw: dict

    @classmethod
    def load(cls, path: str = "config.yaml") -> "Config":
        with open(path, "r", encoding="utf-8") as f:
            return cls(yaml.safe_load(f))

    def __getitem__(self, key: str):
        return self.raw[key]
