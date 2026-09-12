class ResearchFeatureError(Exception):
    """Base error for evidence-driven research features."""


class RepositoryNotFoundError(ResearchFeatureError):
    pass


class UnsupportedDatasetError(ResearchFeatureError):
    pass


class ProviderUnavailableError(ResearchFeatureError):
    pass
