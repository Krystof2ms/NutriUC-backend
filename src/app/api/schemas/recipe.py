from datetime import datetime

from pydantic import BaseModel, Field

from app.api.schemas.user import UserSummary
from app.models import CursorDirection
from app.models import recipe as model


class Instruction(BaseModel):
    step: int
    instruction: str

    def to_model(self) -> model.Instruction:
        return model.Instruction(step=self.step, instruction=self.instruction)


class Ingredient(BaseModel):
    name: str
    quantity: str

    def to_model(self) -> model.Ingredient:
        return model.Ingredient(name=self.name, quantity=self.quantity)


class RecipeBase(BaseModel):
    name: str
    origin: str
    instructions: list[Instruction]
    ingredients: list[Ingredient]
    description: str


class RecipeCreate(RecipeBase):
    category: str

    def to_create(self, image_key: str | None = None) -> model.RecipeCreate:
        return model.RecipeCreate(
            name=self.name,
            origin=self.origin,
            instructions=[instruction.to_model() for instruction in self.instructions],
            ingredients=[ingredient.to_model() for ingredient in self.ingredients],
            description=self.description,
            image_key=image_key,
        )


class RecipeUpdate(BaseModel):
    name: str | None = None
    origin: str | None = None
    instructions: list[Instruction] | None = None
    ingredients: list[Ingredient] | None = None
    description: str | None = None
    category: str | None = None

    def to_update(self, category_id: int | None = None) -> model.RecipeUpdate:
        data = self.model_dump(exclude_unset=True)

        if "category" in data:
            del data["category"]
            data["category_id"] = category_id

        return model.RecipeUpdate.model_construct(**data)


class RecipeDTO(RecipeBase):
    id: int
    category: str
    has_image: bool
    owner: UserSummary
    created_at: datetime


class RecipeQueryDTO(BaseModel):
    name: str | None = None
    category: str | None = None
    cursor: int | None = None
    limit: int = Field(default=12, gt=3, le=30)
    direction: CursorDirection = Field(alias="dir", default=CursorDirection.NEXT)
    mine: bool = False


RecipeCreateDTO = RecipeCreate
