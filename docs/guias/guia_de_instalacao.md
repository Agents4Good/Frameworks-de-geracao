# **Guia de uso do OpenHands**

## **Pré-requisitos**

1. ## Sistemas operacionais Linux, Mac ou [WSL](https://learn.microsoft.com/en-us/windows/wsl/install) (Windows);

2. Ter o [Docker Desktop](https://docs.docker.com/engine/install/) instalado na máquina.

## **Início Rápido**

### Instalação

###  Passo a Passo Linux/Mac:

1. Abra o Docker Desktop, vá para `Settings > Advanced` e assegure que `Allow the default Docker socket to be used` está habilitado; (Mac)  
2. Execute o Docker.

### Passo a Passo Windows:

1. Instale WSL;  
2. Execute o Docker Desktop;  
3. Execute o WSL;  
4. Dentro do WSL siga os passos abaixo.

### Executar:

Com o Docker Desktop ativo:

1. Execute os comandos:
```bash
    docker pull docker.all-hands.dev/all-hands-ai/runtime:0.21-nikolaik

    docker run -it --rm --pull=always \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.21-nikolaik \
    -e LOG_ALL_EVENTS=true \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v ~/.openhands-state:/.openhands-state \
    -p 3000:3000 \
    --add-host host.docker.internal:host-gateway \
    --name openhands-app \
    docker.all-hands.dev/all-hands-ai/openhands:0.21
``` 
2. Acessar o  [http://localhost:3000](http://localhost:3000/).  
3. Escolher Modelo e adicionar Key.  
   1. **Em caso de erro na primeira conexão, verifique a formatação da key e insira novamente.**

## **Modo desenvolvedor**

### Instalação

### Passo a Passo Linux/Mac:

1. Abra o Docker Desktop, vá para `Settings > Advanced` e assegure que `Allow the default Docker socket to be used` está habilitado; (Mac)  
2. Execute o Docker;  
3. Instale o build-essential \=\> sudo apt-get install build-essential.

### Passo a Passo Windows:

1. Execute o Docker Desktop;  
2. Execute o WSL;  
3. Instale o netcat dentro do WSL \=\> sudo apt-get install netcat.

### Passo a Passo Geral:

1. Instale o [Python](https://www.python.org/downloads/) \>= 3.12;  
2. Instale o [NodeJS](https://www.python.org/downloads/) \>= 20.x;  
3. Instale o [Poetry](https://python-poetry.org/docs/#installing-with-the-official-installer) \>= 1.8.  
4. Clone o [repositório do OpenHands](https://github.com/All-Hands-AI/OpenHands/tree/main)

### Se você deseja desenvolver em um sistema sem permissão de administrador:

Você pode usar o conda ou o mamba para gerenciamento de pacotes:
```bash
    # Download and install Mamba (a faster version of conda)
    curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
    bash Miniforge3-$(uname)-$(uname -m).sh
    # Install Python 3.12, nodejs, and poetry
    mamba install python=3.12
    mamba install conda-forge::nodejs
    mamba install conda-forge::poetry
```

### Execução:

1. Configurando ambiente:
```bash
    make build
```

2. Configurando modelo de linguagem:  
```bash
    make setup-config
```

Este comando solicitará que você insira a chave API do LLM, o nome do modelo e outras variáveis, garantindo que o OpenHands seja adaptado às suas necessidades específicas. Se você usa a UI, defina o modelo na UI.

3. Executar a aplicação:
```bash  
   make run
```
   

