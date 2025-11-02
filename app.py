import os
import json
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask, request, jsonify
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()

from sheet import connectSheet,sheetState,addExpense
from message import sendMessage as sendMessage
from report import generateReport as generateReport
from extract import generateExtract as generateExtract
from user import newUser as newUser
from feedback import saveFeedback as saveFeedback
from alert import checkAlert as checkAlert

app = Flask(__name__)

connectSheet.connect_to_sheets()

# WEBHOOK
@app.route("/webhook", methods=["POST"])
def webhook():

    try:
        data = request.get_json()

        if data.get("event") == "messages.upsert" and data.get("data", {}).get("key", {}).get("fromMe") is False:
            message_data = data["data"]
            user_phone = message_data["key"]["remoteJid"].split('@')[0]
            message_body = (message_data.get("message", {}).get("conversation") or \
                           message_data.get("message", {}).get("extendedTextMessage", {}).get("text") or \
                           "").strip().lower()
            
            state_info = sheetState.get_user_state(user_phone)

            today = datetime.now()


            # VARIAVEIS PARA VERIFICAR ENTRADAS
            greetings = ["oi", "oie", "lari","bot", "ola", "olá", "bom dia", "boa tarde", "boa noite", "eai", "opa", "menu","ajuda"]

            weeklyReport = ["relatorio semanal", "relatório semanal", "1", "01"]

            monthlyReport = ["relatorio mensal", "relatório mensal", "2", "02"]

            weeklyStatement = ["extrato semanal","3", "03"]

            monthlyStatement = ["extrato mensal", "4","04"]

            goal = ["definir meta", "meta", "atualizar meta", "meta de gastos", "5", "05"]

            assessment = ["avaliar", "avaliação", "6","06"]

            suggestion = ["sugestão", "sugestao", "feedback", "sugerir", "7", "07"]

            last_week = ["semana anterior", "passada", "semana passada", "anterior"]

            current_week = ["esta semana", "desta semana", "semana atual","dessa semana", "atual", "esta", "desta","dessa"]

            last_month = ["mês passado", "mes passado", "passado", "mês anterior", "mes anterior", "anterior"]

            current_month = ["este mês", "este mes", "este", "atual", "deste mes", "deste mês", "desse mês", "desse mes", "deste", "mês atual", "mes atual"]

            cancel_words = ["sair", "cancelar", "voltar", "volta", "cancela", "cancelamento", "pare", "interromper"]



            # --- LÓGICA DE ESTADO ---
            # O usuário está respondendo a uma pergunta do bot?
            if state_info:
                state = state_info.get('state')
                
                if message_body in cancel_words:
                    sendMessage.send_whatsapp_message(user_phone, "Ok, operação cancelada. 👍")
                    sheetState.clear_user_state(user_phone)
                    return

                if state == 'awaiting_suggestion':
                    if connectSheet.sheet_suggestions:
                        # Salva a sugestão na planilha
                        connectSheet.sheet_suggestions.append_row([user_phone, datetime.now().strftime('%d/%m/%Y'), message_body])
                        sendMessage.send_whatsapp_message(user_phone, "✅ Obrigado! Sua sugestão foi registrada com sucesso e será analisada pela nossa equipe.")
                    else:
                        sendMessage.send_whatsapp_message(user_phone, "😕 Desculpe, ocorreu um erro interno ao salvar sua sugestão. Tente novamente mais tarde.")
                    sheetState.clear_user_state(user_phone)


                elif state == 'awaiting_goal_amount':
                    try:
                        goal_value = float(message_body.replace(',', '.'))
                        if goal_value > 0:
                            user_cell = connectSheet.sheet_goals.find(str(user_phone))
                            current_month_str = datetime.now().strftime('%Y-%m')

                            if user_cell: # Se o usuário já tem uma meta, atualiza
                                row = user_cell.row
                                connectSheet.sheet_goals.update_cell(row, 2, goal_value) # Atualiza Meta
                                connectSheet.sheet_goals.update_cell(row, 3, current_month_str) # Atualiza Mês
                                connectSheet.sheet_goals.update_cell(row, 4, 'FALSE') # Reseta Alerta 50%
                                connectSheet.sheet_goals.update_cell(row, 5, 'FALSE') # Reseta Alerta 80%
                            else: # Se for novo, adiciona
                                connectSheet.sheet_goals.append_row([user_phone, goal_value, current_month_str, 'FALSE', 'FALSE'])

                            sendMessage.send_whatsapp_message(user_phone, f"✅ Sua nova meta de gastos mensais foi definida para *R$ {goal_value:,.2f}*.".replace(',', '.'))
                            sheetState.clear_user_state(user_phone)
                        else:
                            sendMessage.send_whatsapp_message(user_phone, "Por favor, envie um valor positivo para a meta.")
                    except ValueError:
                        sendMessage.send_whatsapp_message(user_phone, "Valor inválido. Por favor, envie apenas o número da sua meta (ex: 1500.50).")

                elif state == 'awaiting_week_choice':
                    start_date, end_date = None, None
                    if message_body in current_week:
                        start_date = (today - timedelta(days=today.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
                        end_date = today
                    elif message_body in last_week:
                        start_of_this_week = (today - timedelta(days=today.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
                        start_date = start_of_this_week - timedelta(days=7)
                        end_date = (start_date + timedelta(days=6)).replace(hour=23, minute=59, second=59)

                    if start_date and end_date:
                        title = f"📄 {state_info['title']} ({start_date.strftime('%d/%m')} a {end_date.strftime('%d/%m')})"
                        if state_info['type'] == 'summary':
                            generateReport.generate_summary_report(user_phone, start_date, end_date, title)
                        elif state_info['type'] == 'detailed':
                            generateExtract.generate_detailed_statement(user_phone, start_date, end_date, title)
                        sheetState.clear_user_state(user_phone)
                    else:
                        sendMessage.send_whatsapp_message(user_phone, "Opção inválida. Por favor, responda com 'esta semana' ou 'semana anterior'.")


                # --- FLUXO DE ESCOLHA DO MÊS ---
                elif state == 'awaiting_month_choice':
                    start_date, end_date = None, None
                    if message_body in current_month:
                        start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                        end_date = today
                    elif message_body in last_month:
                        end_of_last_month = today.replace(day=1) - timedelta(days=1)
                        start_date = end_of_last_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                        end_date = end_of_last_month.replace(hour=23, minute=59)

                    if start_date and end_date:
                        title = f"🗓️ {state_info['title']} ({start_date.strftime('%B de %Y')})"
                        if state_info['type'] == 'summary':
                            generateReport.generate_summary_report(user_phone, start_date, end_date, title)
                        elif state_info['type'] == 'detailed':
                            generateExtract.generate_detailed_statement(user_phone, start_date, end_date, title)
                        sheetState.clear_user_state(user_phone)
                    else:
                        sendMessage.send_whatsapp_message(user_phone, "Opção inválida. Por favor, responda com 'este mês' ou 'mês anterior'.")

                elif state == 'awaiting_rating':
                    try:
                        rating = int(message_body)
                        if 0 <= rating <= 5:
                            if not connectSheet.sheet_ratings:
                                raise Exception("A planilha de avaliações não foi conectada.")
                            # Salva a nota na planilha de avaliações
                            connectSheet.sheet_ratings.append_row([user_phone, datetime.now().strftime('%d/%m/%Y'), rating, ''])
                            if rating <= 3:
                                sendMessage.send_whatsapp_message(user_phone, "Obrigado pela sua nota. Gostaríamos de saber mais. Você gostaria de deixar um feedback para nos ajudar a melhorar? (Responda com seu feedback ou 'não')")
                                sheetState.set_user_state(user_phone, {'state': 'awaiting_feedback'}) # Muda o estado para aguardar o feedback
                            else:
                                sendMessage.send_whatsapp_message(user_phone, "Ficamos felizes com a sua nota! Obrigado por avaliar nosso sistema. 😄")
                                sheetState.clear_user_state(user_phone) # Finaliza o estado de avaliação
                        else:
                            sendMessage.send_whatsapp_message(user_phone, "Nota inválida. Por favor, envie um número de 0 a 5.")
                    except ValueError:
                        sendMessage.send_whatsapp_message(user_phone, "Por favor, envie apenas o número da sua nota (de 0 a 5).")

                elif state == 'awaiting_feedback':
                    if message_body not in ['nao', 'não', "n"]:
                        saveFeedback.handle_feedback_submission(user_phone, message_body)
                    else:
                        sendMessage.send_whatsapp_message(user_phone, "Entendido. Agradecemos sua avaliação mesmo assim!")
                    sheetState.clear_user_state(user_phone) # Finaliza o estado de avaliação

                return jsonify({"status": "OK"}), 200 # Finaliza o processamento aqui


            if  message_body in suggestion:
                sendMessage.send_whatsapp_message(user_phone, "Ficamos felizes em ouvir sua opinião! Por favor, envie sua sugestão de melhoria em uma única mensagem.")
                sheetState.set_user_state(user_phone, {'state': 'awaiting_suggestion'})

            elif  message_body in goal:
                sendMessage.send_whatsapp_message(user_phone, "Qual valor você gostaria de definir como sua meta de gastos mensais?")
                sheetState.set_user_state(user_phone, {'state': 'awaiting_goal_amount'})

            elif message_body in assessment:
                sendMessage.send_whatsapp_message(user_phone, "Que bom que você quer nos avaliar! Por favor, envie uma nota de 0 a 5 para o sistema.")
                sheetState.set_user_state(user_phone, {'state': 'awaiting_rating'})

            elif message_body in weeklyStatement:
                sendMessage.send_whatsapp_message(user_phone, "Você gostaria do extrato desta semana ou da semana anterior?")
                sheetState.set_user_state(user_phone, {'state': 'awaiting_week_choice', 'type': 'detailed', 'title': 'Extrato Semanal'})

            elif message_body in monthlyStatement:
                sendMessage.send_whatsapp_message(user_phone, "Você gostaria do extrato deste mês ou do mês anterior?")
                sheetState.set_user_state(user_phone, {'state': 'awaiting_month_choice', 'type': 'detailed', 'title': 'Extrato Mensal'})

            elif message_body in weeklyReport:
                sendMessage.send_whatsapp_message(user_phone, "Você gostaria do relatório desta semana ou da semana anterior?")
                sheetState.set_user_state(user_phone, {'state': 'awaiting_week_choice', 'type': 'summary', 'title': 'Relatório Semanal'})

            elif message_body in monthlyReport:
                sendMessage.send_whatsapp_message(user_phone, "Você gostaria do relatório deste mês ou do mês anterior?")
                sheetState.set_user_state(user_phone, {'state': 'awaiting_month_choice', 'type': 'summary', 'title': 'Relatório Mensal'})

            elif message_body in greetings:
                if newUser.is_new_user(user_phone):
                    # Mensagem para NOVOS usuários
                    welcome_text = (
                        "Olá! 👋 Bem-vindo(a) ao seu Gerenciador de Gastos Pessoal.\n\n"
                        "Eu armazeno seus gastos e gerencio para você. Para registrar uma despesa, é só me enviar uma mensagem no formato:\n\n"
                        "*Data - Valor - Categoria*\n\n"
                        "Exemplo: `29/09/2025 - 55,30 - Supermercado`\n\n"
                        "Pode começar quando quiser!\n"

                        "A opção de Categoria serve para separar o tipo de compra realizada, então você também pode substituir pelo nome do estabelecimento.\n\n"
                        "Menu de opções:\n\n"
                        "1 - Relatorio semanal\n"
                        "2 - Relatorio mensal\n"
                        "3 - Extrato semanal\n"
                        "4 - Extrato mensal\n"
                        "5 - Definir meta\n"
                        "6 - Avaliar\n"
                        "7 - Sugestão/Feedback\n\n"
                        "O sistema ainda está em teste então pode ocorrer alguns bugs."
                    )
                    sendMessage.send_whatsapp_message(user_phone, welcome_text)

                else:
                    # Mensagem para usuários EXISTENTES que mandam 'oi'
                    refresher_text = (
                        "Olá de novo! 😊\n\n"
                        "Lembrete: para registrar um gasto, use o formato:\n"
                        "*Data - Valor - Categoria*\n\n"
                        "Exemplo: `29/09/2025 - 55,30 - Supermercado`\n\n"
                        "Menu de opções:\n\n"
                        "1 - Relatorio semanal\n"
                        "2 - Relatorio mensal\n"
                        "3 - Extrato semanal\n"
                        "4 - Extrato mensal\n"
                        "5 - Definir meta\n"
                        "6 - Avaliar\n"
                        "7 - Sugestão/Feedback\n\n"

                    )
                    sendMessage.send_whatsapp_message(user_phone, refresher_text)

            elif message_body: # <<< Se não for saudação, processa como gasto
                response_text = addExpense.add_expense_to_sheet(user_phone, message_body)
                sendMessage.send_whatsapp_message(user_phone, response_text)

    except Exception as e:
        print(f"Erro ao processar webhook: Estrutura de dados inesperada. Erro: \n\n{e}")
        # Tenta notificar o usuário que algo deu errado, se possível
        try:
            user_phone = request.get_json()['data']['key']['remoteJid'].split('@')[0]
            sendMessage.send_whatsapp_message(user_phone, "😕 Ops! Ocorreu um erro interno ao processar sua mensagem. A equipe já foi notificada.")
        except:
            pass # Ignora se nem conseguir extrair o número do usuário

    return jsonify({"status": "OK"}), 200

#PÁGINA INICIAL
@app.route("/")
def index():
    return "<h1>Servidor do Chatbot de Gastos está no ar!</h1>"

#EXECUÇÃO DO APP
if __name__ == "__main__":
    # O Flask roda na porta 5000 por padrão.
    # O debug=True ajuda a ver erros, mas desative em produção.
    app.run(debug=True)
