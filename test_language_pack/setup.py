from setuptools import setup, find_packages

setup(
    name="blitzer-language-tst",
    version="0.1.0",
    description="Test language pack for Blitzer CLI",
    author="Test Author",
    author_email="test@example.com",
    packages=find_packages(),
    package_data={
        'blitzer_language_tst': ['tst_lexicon.db'],  # Include the specific database file in the package
    },
    include_package_data=True,
    install_requires=[
        "blitzer-cli",  # This ensures compatibility
    ],
    entry_points={
        'blitzer.languages': [
            'tst = blitzer_language_tst.tst_processor:get_processor',
        ]
    },
    python_requires='>=3.7',
)