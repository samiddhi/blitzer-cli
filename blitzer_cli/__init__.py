# blitzer-cli: A CLI tool
# Copyright (C) 2025 Samiddhi
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Main blitzer-cli package"""
__version__ = "0.1.0"


def cleanup_resources():
    """Cleanup all resources used by the blitzer-cli package."""
    from blitzer_cli.processor import cleanup_db_connections
    # from blitzer_cli.data_manager import cleanup_language_data
    
    cleanup_db_connections()
    # Optionally clean up language data as well, though user might want to keep it
    # cleanup_language_data()  # Uncomment if you want to clean up all language data as well
