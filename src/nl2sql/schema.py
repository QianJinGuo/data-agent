"""Data models for NL2SQL pipeline."""
from typing import Optional
from pydantic import BaseModel, Field


class Metric(BaseModel):
    """Business metric with expression."""

    name: str
    expr: str
    description: Optional[str] = None


class Dimension(BaseModel):
    """Business dimension with possible values."""

    name: str
    field: str
    values: Optional[list[str]] = None


class SemanticModel(BaseModel):
    """Semantic layer mapping business terms to physical schema."""

    metrics: list[Metric] = Field(default_factory=list)
    dimensions: list[Dimension] = Field(default_factory=list)
    tables: list[str] = Field(default_factory=list)
    business_terms: dict[str, str] = Field(default_factory=dict)


class Dataset(BaseModel):
    """A data source with semantic model."""

    id: str
    name: str
    db_type: str = "mock"
    tables: list[str] = Field(default_factory=list)
    semantic_model: SemanticModel = Field(default_factory=SemanticModel)

    def get_schema_text(self) -> str:
        """Return LLM-friendly schema description."""
        lines = [f"Dataset: {self.name} (id={self.id})"]
        if self.tables:
            lines.append(f"Tables: {', '.join(self.tables)}")
        if self.semantic_model.metrics:
            lines.append("Metrics:")
            for m in self.semantic_model.metrics:
                lines.append(f"  - {m.name}: {m.expr}  # {m.description or ''}")
        if self.semantic_model.dimensions:
            lines.append("Dimensions:")
            for d in self.semantic_model.dimensions:
                vals = f" ({', '.join(d.values)})" if d.values else ""
                lines.append(f"  - {d.name}: {d.field}{vals}")
        if self.semantic_model.business_terms:
            lines.append("Business Terms:")
            for term, expr in self.semantic_model.business_terms.items():
                lines.append(f"  - {term} => {expr}")
        return "\n".join(lines)


def get_sample_dataset() -> Dataset:
    """Return a sample sales dataset for demo purposes."""
    return Dataset(
        id="ds_sales",
        name="Sales Dataset",
        db_type="mock",
        tables=["sales", "orders", "products"],
        semantic_model=SemanticModel(
            tables=["sales", "orders", "products"],
            metrics=[
                Metric(name="Sales Amount", expr="SUM(sales.amount)", description="Total sales revenue"),
                Metric(name="Order Count", expr="COUNT(sales.order_id)", description="Number of orders"),
                Metric(name="Avg Order Value", expr="AVG(sales.amount)", description="Average order value"),
            ],
            dimensions=[
                Dimension(name="Region", field="sales.region", values=["North", "South", "East", "West"]),
                Dimension(name="Product Category", field="products.category", values=["Electronics", "Clothing", "Food"]),
                Dimension(name="Month", field="sales.month", values=None),
            ],
            business_terms={
                "this month sales": "SUM(sales.amount) WHERE sales.month = CURRENT_MONTH",
                "north region sales": "SUM(sales.amount) WHERE sales.region = 'North'",
            },
        ),
    )