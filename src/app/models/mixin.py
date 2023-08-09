from fastapi import HTTPException, status
from typeguard import typechecked


@typechecked
class GetOr404Mixin:
    @classmethod
    def get_or_404(cls, **kwargs):
        result = cls.filter(**kwargs)
        if result is None:
            raise HTTPException(
                detail=f"{cls.__name__} with {kwargs} not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return result[0]

    @classmethod
    def get_or_none(cls, **kwargs):
        return cls.filter(**kwargs)


@typechecked
class UniqueSlugMixin:
    @classmethod
    def unique_slug(cls, field: str, value: str, i=0):
        possible_value = value if i == 0 else f"{value}-{i}"
        if cls.filter(**{field: possible_value}):
            return cls.unique_slug(field, value, i + 1)
        return value
