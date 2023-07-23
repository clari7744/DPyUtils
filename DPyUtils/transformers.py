from typing import List

from discord import Interaction
from discord.app_commands import Transformer, TransformerError

from .duration import Duration


class IntListTransformer(Transformer):
    async def transform(self, interaction: Interaction, value: str) -> List[int]:
        arguments: List[str] = " ".join(map(str.strip, value.split(","))).split(" ")
        intargs: List[int] = []
        for i in arguments:
            try:
                intargs.append(int(i))
            except ValueError as err:
                raise TransformerError(f"{i} is not an integer!") from err
        return intargs


class DurationTransformer(Transformer):
    async def transform(self, interaction: Interaction, value: str) -> Duration:
        return await Duration.convert(interaction, value)
