"""
pytest configuration file
Adds the oaback directory to sys.path and configures Django Settings.
"""
import sys
import os

# Add oaback directory to Python path so Django apps can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'oaback'))

# pytest-django reads this variable (can also be configured in pytest.ini)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oa.settings')
