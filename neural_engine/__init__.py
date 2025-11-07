"""
Neural-CONI: Neural Network Architecture for CONI

This package implements neural network principles in the CONI framework:
- Vector embeddings for information representation
- Attention mechanisms for selective input processing
- Weight learning for automatic optimization
- Backpropagation for continuous improvement
"""

__version__ = "1.0.0"
__author__ = "CONI Team"

# Import core components
from .embedding_engine import EmbeddingEngine
from .neural_task import NeuralTask
from .validator import NeuralValidator
from .weight_manager import WeightManager
from .attention import AttentionMechanism

__all__ = [
    'EmbeddingEngine',
    'NeuralTask',
    'NeuralValidator',
    'WeightManager',
    'AttentionMechanism',
]
