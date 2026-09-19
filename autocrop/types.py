"""Array typing shared by the cropper and detector, independent of feature results."""

from typing import Any, TypeAlias

from numpy.typing import NDArray

# Shape and dtype depend on input mode, including grayscale and alpha.
# This does not choose a new runtime input contract for #215.
ImageArray: TypeAlias = NDArray[Any]
