import asyncio
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval.metrics import GEval, AnswerRelevancyMetric, TaskCompletionMetric
from deepeval.evaluate import evaluate
from deepeval.evaluate.configs import DisplayConfig
from main import execute_graph


# Define the SystemMessage content for GEval criteria
# A SystemMessage de um agente define qual o seu papel e qual sua função, por isso os critérios GEval irão se basear na SystemMessage
SYSTEM_MESSAGE_CONTENT = "Você é um assistente que utiliza ferramentas do GitHub"

# Function to run the agent asynchronously


async def run_agent(input_text: str) -> str:
    result = await execute_graph(input_text)
    # The execute_graph returns a list of messages, we need the content of the last AIMessage
    for message in reversed(result):
        if message.type == "ai":
            return message.content
    return ""

# Define GEval metrics based on the SystemMessage
# GEval para clareza: Avalia se a resposta é clara, bem organizada e fácil de entender, usando terminologia educacional apropriada.
clarity_metric = GEval(
    name="Clareza",
    criteria="A resposta deve ser clara, bem organizada e fácil de entender.",
    evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT]
)

# GEval para relevância: Avalia se a resposta aborda diretamente a solicitação do usuário para objetivo do {agent_name}.
relevance_metric_geval = GEval(
    name="Relevância da resposta",
    criteria="A resposta deve abordar diretamente a solicitação do usuário de acordo com a função do {agent_name}",
    evaluation_params=[LLMTestCaseParams.INPUT,
                       LLMTestCaseParams.ACTUAL_OUTPUT]
)

# GEval para completude: Avalia se a resposta inclui todos os componentes de acordo com a função e o papel do {agent_name}
completeness_metric_geval = GEval(
    name="Completude da resposta",
    criteria="A resposta deve incluir todos os componentes solicitados de um plano de aula estruturado: introdução, atividades e sugestões de avaliação. Deve utilizar plenamente as informações de entrada (tema, nível, objetivos, recursos) para gerar um plano abrangente.",
    evaluation_params=[LLMTestCaseParams.INPUT,
                       LLMTestCaseParams.ACTUAL_OUTPUT]
)

# Standard metrics
answer_relevancy_metric = AnswerRelevancyMetric(threshold=0.7)

inputs_expected = [
    (
        "resuma os meus repositórios",
        '''content='{"total_count":9,"incomplete_results":false,"items":[{"id":829206451,"name":"programacao-para-web","full_name":"AndreFelipeAlmeida/programacao-para-web","description":"Repositório dedicado para as atividades da disciplina de Programação para Web","html_url":"https: // github.com/AndreFelipeAlmeida/programacao-para-web","language":"JavaScript","stargazers_count":0,"forks_count":0,"open_issues_count":0,"updated_at":"2024-09-27T02: 34: 59Z","created_at":"2024-07-16T01: 23: 11Z","private":false,"fork":false,"archived":false,"default_branch":"main"},{"id":903786040,"name":"AiSystem","full_name":"AndreFelipeAlmeida/AiSystem","description":"Repositório dedicado para criação de um exemplo em LangGraph para o projeto Agents4Good da Universidade Federal de Campina Grande","html_url":"https: // github.com/AndreFelipeAlmeida/AiSystem","language":"Python","stargazers_count":0,"forks_count":0,"open_issues_count":0,"updated_at":"2024-12-19T06: 07: 37Z","created_at":"2024-12-15T15: 03: 23Z","private":true,"fork":false,"archived":false,"default_branch":"main"},{"id":644850149,"name":"Test","full_name":"AndreFelipeAlmeida/Test","html_url":"https: // github.com/AndreFelipeAlmeida/Test","stargazers_count":0,"forks_count":0,"open_issues_count":0,"updated_at":"2023-05-24T11: 41: 40Z","created_at":"2023-05-24T11: 41: 40Z","private":true,"fork":false,"archived":false,"default_branch":"main"},{"id":935070994,"name":"resumos","full_name":"AndreFelipeAlmeida/resumos","description":"Repositório dedicado aos meus estudos.","html_url":"https: // github.com/AndreFelipeAlmeida/resumos","stargazers_count":0,"forks_count":0,"open_issues_count":0,"updated_at":"2025-08-18T17: 54: 46Z","created_at":"2025-02-18T21: 21: 30Z","private":false,"fork":false,"archived":false,"default_branch":"main"},{"id":960050487,"name":"concurrent-store","full_name":"AndreFelipeAlmeida/concurrent-store","html_url":"https: // github.com/AndreFelipeAlmeida/concurrent-store","language":"Java","stargazers_count":0,"forks_count":0,"open_issues_count":0,"updated_at":"2025-04-08T03: 13: 54Z","created_at":"2025-04-03T19: 24: 49Z","private":false,"fork":false,"archived":false,"default_branch":"main"}]}' name='search_repositories' id='8b393dad-790f-4b74-a7eb-c1e6829c2903' tool_call_id='call_SYIoOibE7CteM4X9r1v70Nhi'''
    )
]


test_cases = []
for i, expected in inputs_expected:
    actual = asyncio.run(run_agent(i))  # chama o agente e aguarda a resposta
    test_cases.append(LLMTestCase(
        input=i, actual_output=actual, expected_output=expected))


results = evaluate(test_cases, metrics=[
    clarity_metric,
    relevance_metric_geval,
    completeness_metric_geval,
    answer_relevancy_metric
],
    display_config=DisplayConfig(
    show_indicator=False,
    print_results=False,
)
)

# código necessário para exibição dos resultados de teste
for case, test_result in zip(test_cases, results.test_results):
    print(f"\nTestCase: {case.input[:80]}...")
    for metric in test_result.metrics_data:
        status = "✅" if metric.success else "❌"
        print(f" - {metric.name}: {metric.score:.2f} {status}")
        if metric.reason:
            print(f"   ↳ Reason: {metric.reason}")
