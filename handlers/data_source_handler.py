from models.schemas import DataSourceList, DataSourceInfo
from core.backtest_runner import get_available_data_sources

def handle_get_data_sources() -> DataSourceList:
    """Retrieves the list of available data sources and formats it."""
    sources = get_available_data_sources()
    
    source_list = [
        DataSourceInfo(
            name=source["name"],
            description=source["description"],
            symbols=source["symbols"]
        )
        for key, source in sources.items()
    ]
    
    return DataSourceList(sources=source_list)
