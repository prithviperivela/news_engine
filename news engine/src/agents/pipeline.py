"""Pipeline orchestrator for agent-based execution."""

from typing import List, Optional, Tuple
from dataclasses import dataclass

from src.agents.base import AgentResult
from src.agents.ingestion import IngestionAgent
from src.agents.processing import ProcessingAgent
from src.agents.classification import ClassificationAgent
from src.agents.ranking import RankingAgent
from src.agents.query import QueryAgent
from src.models import Article


@dataclass
class PipelineConfig:
    """Configuration for pipeline execution."""
    collect: bool = False
    classify: bool = False
    keyword: Optional[str] = None
    domain: Optional[str] = None
    rank: bool = False
    limit: int = 10
    verbose: bool = True


class Pipeline:
    """
    Orchestrates agent execution for the news engine.
    
    Determines which agents to run based on the request
    and manages data flow between them.
    """
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        
        # Initialize agents
        self.ingestion = IngestionAgent(verbose=verbose)
        self.processing = ProcessingAgent(verbose=verbose)
        self.classification = ClassificationAgent(verbose=verbose)
        self.ranking = RankingAgent(verbose=verbose)
        self.query = QueryAgent(verbose=verbose)
    
    def log(self, message: str):
        """Log pipeline activity."""
        if self.verbose:
            print(f"[Pipeline] {message}")
    
    def run(self, config: PipelineConfig) -> AgentResult:
        """
        Execute the pipeline based on configuration.
        
        Args:
            config: PipelineConfig with execution options
            
        Returns:
            Final AgentResult from the pipeline
        """
        self.log("Starting pipeline execution...")
        articles = []
        
        # Step 1: Ingestion (if collecting)
        if config.collect:
            self.log("=" * 50)
            result = self.ingestion.run()
            if not result.success:
                return result
            articles = result.data
            
            # Step 2: Processing (save new articles)
            self.log("=" * 50)
            result = self.processing.run(articles, mode="save")
            if not result.success:
                return result
            articles = result.data
        else:
            # Load existing articles
            self.log("=" * 50)
            result = self.processing.run(None)
            if not result.success:
                return result
            articles = result.data
        
        # Step 3: Classification (if requested)
        if config.classify:
            self.log("=" * 50)
            result = self.classification.run(articles)
            if not result.success:
                return result
            articles = result.data
            
            # Save classified articles
            result = self.processing.run(articles, mode="update")
            if not result.success:
                return result
        
        # Step 4: Query/Filter (if keyword or domain specified)
        if config.keyword or config.domain:
            self.log("=" * 50)
            result = self.query.run(
                articles,
                keyword=config.keyword,
                domain=config.domain
            )
            if not result.success:
                return result
            articles = result.data
        
        # Step 5: Ranking (if requested)
        if config.rank:
            self.log("=" * 50)
            result = self.ranking.run(articles, limit=config.limit)
            if not result.success:
                return result
            # Return ranked tuples
            return result
        
        # Return filtered articles (not ranked)
        self.log("=" * 50)
        self.log(f"Pipeline complete. {len(articles)} articles ready.")
        
        return AgentResult(
            success=True,
            data=articles[:config.limit],
            metadata={"total": len(articles), "returned": min(len(articles), config.limit)}
        )


def run_pipeline(
    collect: bool = False,
    classify: bool = False,
    keyword: str = None,
    domain: str = None,
    rank: bool = False,
    limit: int = 10,
    verbose: bool = True
) -> AgentResult:
    """
    Convenience function to run the pipeline.
    """
    config = PipelineConfig(
        collect=collect,
        classify=classify,
        keyword=keyword,
        domain=domain,
        rank=rank,
        limit=limit,
        verbose=verbose
    )
    pipeline = Pipeline(verbose=verbose)
    return pipeline.run(config)
