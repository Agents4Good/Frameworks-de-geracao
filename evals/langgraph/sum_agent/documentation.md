# Template de Agente

### Definição do contexto

Papel do agente (System prompt): Descrição da persona que o agente deve assumir e quais tarefas ele deve executar com exemplos e passo-a-passo.

```
Você é um assistente muito útil que responde as perguntas de matemática do usuário.
Utilize a tool quando necessário, apenas uma tool call por vez e retorne uma mensagem para ele quando a resposta for alcançada.
Responda em Português - BR.

Exemplo:
*Quanto é 5+5+2?*

Resposta esperada: 5 + 5 + 2 é igual a 12.
```

Entrada do usuário (User prompt): Mensagem que o usuário vai passar diretamente para o agente.

### Definição de ações

Um agente pode executar ações baseado na lista de ferramentas que ele possui ou nas ferramentas cadastradas pelo usuário do sistema.

Add:
```
Função Python que retorna a soma de dois números passados por parâmetro.
```

### Escolha do modelo

O usuário deve escolher qual modelo deve ser usado para ser executado no agente.

É necessário que o modelo seja capaz de utilizar ferramentas. Modelo utilizado em testes:
- Qwen/Qwen2.5-72B-Instruct

### Teste e validação

Foi utilizado para a realização dos testes a biblioteca Deepeval do Python