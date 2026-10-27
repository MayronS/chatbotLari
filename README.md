# 🤖 chatbotLari – Gerenciador de Gastos pelo WhatsApp

Chatbot em Python que permite registrar e acompanhar gastos pessoais direto pelo WhatsApp, sem instalar nenhum app. Os dados ficam salvos em planilhas do Google Sheets.

## Funcionalidades
- Registro de despesas por mensagem (ex.: `29/09/2025 - 55,30 - Supermercado` ou `30,00 Restaurante`)
- Relatório resumido por categoria (semanal e mensal)
- Extrato detalhado (semanal e mensal)
- Meta de gastos mensal com alertas automáticos ao atingir 50%, 80% e 100%
- Exclusão de despesas (`apagar 08/10 20,00 lanche`)
- Avaliação (0 a 5) e envio de sugestões/feedback
- Menu interativo por mensagem, com fluxo de conversa por estado

## Tecnologias
Python · Flask · Gunicorn · pandas · gspread (Google Sheets API) · Evolution API (WhatsApp) · python-dotenv

## Como funciona
1. A Evolution API recebe a mensagem no WhatsApp e envia um evento ao endpoint `POST /webhook`.
2. O app identifica o comando ou o estado da conversa do usuário.
3. Os dados são lidos e gravados nas planilhas do Google (gastos, metas, avaliações, sugestões e estados).
4. O bot responde ao usuário pela Evolution API.

## Estrutura

- app.py # webhook e roteamento dos comandos
- sheet/ # conexão com o Google Sheets, despesas e estado do usuário
- report/ # relatórios resumidos
- extract/ # extratos detalhados
- alert/ # alertas de meta de gastos
- message/ # envio de mensagens
- feedback/ # sugestões e avaliações
- user/ # cadastro de novos usuários
