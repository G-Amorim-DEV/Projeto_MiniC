"""MiniC semantic analysis over the parser's AST."""
from .analyzer import Diagnostic, SemanticAnalyzer, Symbol

__all__ = ['Diagnostic', 'SemanticAnalyzer', 'Symbol']
