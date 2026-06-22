from typing import Protocol, TypeVar

OutputT = TypeVar("OutputT", covariant=True)


class StructuredModel(Protocol[OutputT]):
    """Anything exposing an async ainvoke(prompt) -> OutputT.

    This is the shape returned by `chat_model.with_structured_output(SomeSchema)`.
    Depending on this Protocol instead of a concrete LangChain class is what lets
    node functions be unit tested with a fake model, no network call or API key needed.
    """

    async def ainvoke(self, prompt: str) -> OutputT: ...
