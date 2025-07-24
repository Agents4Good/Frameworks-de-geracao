from deepeval import evaluate
from deepeval.test_case import LLMTestCase, LLMTestCaseParams, ToolCall
from deepeval.metrics import GEval, AnswerRelevancyMetric, TaskCompletionMetric, ToolCorrectnessMetric
import agent_codigo
import asyncio

API_KEY = ""  # Substitua pela sua chave real
agent = agent_codigo.LLMAgent(API_KEY)

input_text = "crie e registre um agente responsavel por somar numeros inteiros"
# Chamada do seu agente
def run_agent(input_text):
    return asyncio.run(agent.process_message(input_text))

agent_output = run_agent(input_text)

# Métrica GEval: clareza
g_eval = GEval(
    name="clarity",
    criteria="The response must be clear and directly answer the question.",
    model="gpt-4o",
    evaluation_params=[
        LLMTestCaseParams.ACTUAL_OUTPUT,
        LLMTestCaseParams.EXPECTED_OUTPUT,
        LLMTestCaseParams.RETRIEVAL_CONTEXT 
    ]
)

# Métrica de relevância
relevancy = AnswerRelevancyMetric()

# Métrica de completude de tarefa
task_completion = TaskCompletionMetric(
    threshold=0.7,
    model="gpt-4o",
    include_reason=True
)

# Métrica de ferramentas (simulando uma chamada de ferramenta)
tool_correctness = ToolCorrectnessMetric(
    should_consider_ordering=False
)

filename = "agent_example.py"
expected_output = ""
with open(filename, "r", encoding="utf-8") as file:
    expected_output = file.read()

filename = "agent_generated.py"
actual_output = ""
with open(filename, "r", encoding="utf-8") as file:
    actual_output = file.read()

tools_called = [call['tool'] for call in agent_output['tool_calls']]
retrieval_context = """
Este agente deve ser capaz de gerar código do agente solicitado pelo usuário utilizando o template especificado no seu system prompt e salvar em um arquivo chamado agent_generated.py
É utilizada a ferramenta registerAgent para esse propósito.
"""

# Criação do test case com ferramentas usadas
test_case = LLMTestCase(
    input=input_text,
    actual_output=actual_output,
    expected_output=expected_output,
    tools_called=[ToolCall(name=t) for t in tools_called],
    expected_tools=[ToolCall(name="registerAgent")],
    retrieval_context=[retrieval_context]
)

# Avaliação
evaluate(
    test_cases=[test_case],
    metrics=[g_eval, relevancy, task_completion, tool_correctness]
)
