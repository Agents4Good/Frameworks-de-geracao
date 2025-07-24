from langchain_core.tools import tool


@tool
def add(a: int, b: int) -> int:
  """
    Realiza a soma de dois Números

    Args:
      a (int): Primeiro Número
      b (int): Segundo Número

    Returns:
      int: Resultado da Soma
  """
  return a + b
