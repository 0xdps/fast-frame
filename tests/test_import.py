def test_version() -> None:
    import fastframe

    assert fastframe.__version__ == "0.1.0"


def test_schema_reexports_are_pydantic() -> None:
    from pydantic import BaseModel as PydanticBaseModel
    from pydantic import Field as PydanticField

    from fastframe.schemas import BaseModel, Field

    assert BaseModel is PydanticBaseModel
    assert Field is PydanticField
