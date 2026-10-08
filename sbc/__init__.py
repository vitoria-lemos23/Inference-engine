"""SBC — shell genérico de Sistemas Baseados em Conhecimento (Questão 5).

Módulos: modelo (representação), parser (formato .kb), motor (encadeamento), explicacao (Como?/Por quê?),
editor (edição e validação da base), nl (linguagem natural), dialogo (interface de terminal).
O shell não contém conhecimento de nenhum domínio: ele é carregado de arquivos .kb/.json.
"""
from .modelo import BaseConhecimento, Condicao, Conclusao, Regra, Variavel  # noqa: F401
from .motor import Motor  # noqa: F401
from .parser import carregar, salvar, ler_kb, escrever_kb  # noqa: F401
from .editor import Editor  # noqa: F401
from .dialogo import Dialogo  # noqa: F401
