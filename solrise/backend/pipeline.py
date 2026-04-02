"""
SolRise - Stable Pipeline Interface
====================================
This is the main entry point for the backend.
It allows us to swap pipeline implementations without changing the API code.
"""

# Switch this import to change versions
from pipelines.pipeline_v8 import SolRisePipeline

# Export for use in app.py
__all__ = ['SolRisePipeline']
