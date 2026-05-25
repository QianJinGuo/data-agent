"""Multi-dataset manager for cross-dataset queries."""
from typing import Optional
from nl2sql.schema import Dataset


class MultiDatasetManager:
    """Manages multiple datasets and supports cross-dataset querying."""

    def __init__(self):
        self.datasets: dict[str, Dataset] = {}

    def add_dataset(self, ds: Dataset) -> None:
        """Add a dataset to the manager."""
        self.datasets[ds.id] = ds

    def get_dataset(self, id: str) -> Optional[Dataset]:
        """Retrieve a dataset by its ID."""
        return self.datasets.get(id)

    def cross_dataset_query(self, question: str) -> list[str]:
        """Determine which datasets are involved in answering the question.
        
        Returns a list of dataset IDs that are relevant to the question.
        This is a simple keyword-based detection; in production, 
        use LLM-based detection for better accuracy.
        """
        question_lower = question.lower()
        involved_ids = []

        for ds_id, ds in self.datasets.items():
            # Check if any table names or semantic model terms appear in the question
            schema_text = ds.get_schema_text().lower()
            
            # Simple heuristic: check for dataset name or table names in question
            if ds.name.lower() in question_lower:
                involved_ids.append(ds_id)
                continue
                
            for table in ds.tables:
                if table.lower() in question_lower:
                    if ds_id not in involved_ids:
                        involved_ids.append(ds_id)
                    break
                    
            # Also check semantic model terms
            for metric in ds.semantic_model.metrics:
                if metric.name.lower() in question_lower or metric.expr.lower() in question_lower:
                    if ds_id not in involved_ids:
                        involved_ids.append(ds_id)
                    break
                    
            for dim in ds.semantic_model.dimensions:
                if dim.name.lower() in question_lower or dim.field.lower() in question_lower:
                    if ds_id not in involved_ids:
                        involved_ids.append(ds_id)
                    break

        return involved_ids

    def merge_schema_text(self) -> str:
        """Combine schema text from all datasets for LLM consumption."""
        schema_parts = []
        for ds_id, ds in self.datasets.items():
            schema_parts.append(ds.get_schema_text())
        return "\n\n---\n\n".join(schema_parts)