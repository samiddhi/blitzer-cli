"""Main blitzer-cli package"""
__version__ = "0.0.6"


def cleanup_resources():
    """Cleanup all resources used by the blitzer-cli package."""
    from blitzer_cli.processor import cleanup_db_connections
    from blitzer_cli.data_manager import cleanup_language_data
    
    cleanup_db_connections()
    # Optionally clean up language data as well, though user might want to keep it
    # cleanup_language_data()  # Uncomment if you want to clean up all language data as well