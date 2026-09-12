"""Prometheus exposition over ReproProof's existing metric registry."""

from .exporter import PrometheusExporter

__all__ = ["PrometheusExporter"]
