from delivery_route_api.models.base import Base


def test_initial_model_tables_are_registered() -> None:
    expected_tables = {
        "routes",
        "stops",
        "optimization_jobs",
        "route_sequences",
        "route_metrics",
    }

    assert expected_tables.issubset(Base.metadata.tables.keys())
