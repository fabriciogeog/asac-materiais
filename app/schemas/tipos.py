from decimal import Decimal
from typing import Annotated

from pydantic import PlainSerializer

# O SQLite não tem tipo decimal nativo: o SQLAlchemy devolve Numeric como
# Decimal com 10 casas (ex.: Decimal('0E-10') para zero) e o Pydantic
# serializaria isso como string no JSON ("0E-10"), o que vaza notação
# científica para o frontend. Este tipo garante que quantidades cheguem
# ao cliente como número JSON (ex.: 0, 1.5).
NumeroJSON = Annotated[Decimal, PlainSerializer(float, return_type=float, when_used="json")]
