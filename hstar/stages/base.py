"""Base class for pipeline stages."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from hstar.config import Config
from hstar.generation.generator import Generator
from hstar.generation.prompt_builder import PromptBuilder
from hstar.nsql.database import NeuralDB


class BaseStage(ABC):
    """
    Abstract base class for H-STAR pipeline stages.
    """
    
    def __init__(self, config: Config, generator: Generator):
        """
        Initialize stage with configuration and generator.
        
        Args:
            config: Configuration object
            generator: LLM generator instance
        """
        self.config = config
        self.generator = generator
        self.prompt_builder = PromptBuilder(
            prompt_style=config.prompt_style,
            max_rows=config.max_table_rows
        )
    
    @abstractmethod
    def run(
        self,
        db: NeuralDB,
        question: str,
        previous_results: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the stage.
        
        Args:
            db: NeuralDB instance with the current table
            question: Question to answer
            previous_results: Results from previous stages
            
        Returns:
            Dictionary with stage results
        """
        pass
    
    @abstractmethod
    def get_stage_name(self) -> str:
        """Get the name of this stage."""
        pass
    
    def log(self, message: str) -> None:
        """Log a message with stage name prefix."""
        print(f"[{self.get_stage_name()}] {message}")
