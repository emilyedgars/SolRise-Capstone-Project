"""
pipeline.py — SolRise Analysis Pipeline
========================================
Entry point for the analysis backend. Imports the current pipeline
implementation so that app.py never needs to change when the pipeline
is updated.
"""

from pipelines.pipeline_v8 import SolRisePipeline

__all__ = ['SolRisePipeline']
