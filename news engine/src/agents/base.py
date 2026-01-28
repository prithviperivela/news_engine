"""Base Agent class for the news engine."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AgentResult:
    """Standard result from an agent execution."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        self.metadata["timestamp"] = datetime.now().isoformat()


class Agent(ABC):
    """
    Base class for all agents in the news engine.
    
    Each agent has:
    - A name for identification
    - A run() method that processes input and returns AgentResult
    - Logging of execution
    """
    
    def __init__(self, name: str, verbose: bool = True):
        self.name = name
        self.verbose = verbose
    
    def log(self, message: str):
        """Log agent activity."""
        if self.verbose:
            print(f"[{self.name}] {message}")
    
    @abstractmethod
    def run(self, input_data: Any = None, **kwargs) -> AgentResult:
        """
        Execute the agent's task.
        
        Args:
            input_data: Input data for processing
            **kwargs: Additional parameters
            
        Returns:
            AgentResult with success status and data
        """
        pass
    
    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name}>"
