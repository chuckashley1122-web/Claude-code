"""Lead sources. Each returns a list[Lead]; the pipeline does not care which."""

from .apollo import ApolloSource
from .brightdata import BrightDataSource
from .nmls import NMLSSource
from .sales_navigator_csv import SalesNavigatorCSVSource

REGISTRY = {
    "sales-nav-csv": SalesNavigatorCSVSource,
    "apollo": ApolloSource,
    "brightdata": BrightDataSource,
    "nmls": NMLSSource,
}

__all__ = ["REGISTRY", "ApolloSource", "BrightDataSource", "NMLSSource", "SalesNavigatorCSVSource"]
