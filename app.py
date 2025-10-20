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

import sheet.connect_sheet as connect_sheet
import sheet.user_state as user_state


app = Flask(__name__)

#CHAVES
EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")
EVOLUTION_INSTANCE = os.getenv("EVOLUTION_INSTANCE")

connect_sheet.sheets()

    #BUSCA OS DADOS E PREPARA
def get_user_data(user_phone):
    records = sheet.get_all_records(value_render_option='UNFORMATTED_VALUE')
    if not records:
        return None # Retorna None se não houver registros

    df = pd.DataFrame(records)

    # Converte a coluna 'Identificador' para string para uma comparação segura
    df['Identificador'] =pd.to_numeric(df['Identificador'], errors='coerce').astype('Int64').astype(str)

    user_phone_str = str(user_phone).strip()
    user_df = df[df['Identificador'] == user_phone_str].copy()

    if user_df.empty:
        return None # Retorna None se o usuário não tiver registros

    # Limpeza e preparação dos dados
    user_df['Valor'] = user_df['Valor'].astype(str).str.replace(',', '.', regex=False)
    user_df['Valor'] = pd.to_numeric(user_df['Valor'], errors='coerce')
    user_df.dropna(subset=['Valor'], inplace=True)
    user_df['Data'] = pd.to_datetime(user_df['Data'], dayfirst=True, errors='coerce')
    user_df.dropna(subset=['Data'], inplace=True)

    return user_df


#FUNÇÃO PARA GERAR O RELATORIO
def generate_summary_report(user_phone, start_date, end_date, title):
    print(f"Iniciando geração de relatório resumido para {user_phone}...")
    try:
        user_df = get_user_data(user_phone)
        if user_df is None:
            send_whatsapp_message(user_phone, "Não encontrei gastos registrados para o período solicitado.")
            return

        period_df = user_df[(user_df['Data'] >= start_date) & (user_df['Data'] <= end_date)]

        if period_df.empty:
            send_whatsapp_message(user_phone, "Você não teve nenhum gasto registrado no período solicitado.")
            return

        expenses_by_category = period_df.groupby('Categoria')['Valor'].sum()
        total_spent = expenses_by_category.sum()

        report_lines = [f"*{title}*"]
        for category, total in expenses_by_category.sort_values(ascending=False).items():
            valor_formatado_br = f"{total:,.2f}".replace(',', '#').replace('.', ',').replace('#', '.')
            report_lines.append(f"• {category.capitalize()}: *R$ {valor_formatado_br}*")

        total_spent_br = f"{total_spent:,.2f}".replace(',', '#').replace('.', ',').replace('#', '.')
        report_lines.append("\n-----------------------------------")
        report_lines.append(f"*Total Gasto no Período: R$ {total_spent_br}*")

        final_report = "\n".join(report_lines)
        send_whatsapp_message(user_phone, final_report)
        print(f"Relatório resumido enviado para {user_phone}.")
    except Exception as e:
        print(f"Erro ao gerar relatório resumido: {e}")
        send_whatsapp_message(user_phone, "Desculpe, não consegui gerar seu relatório.")


#GERA OS EXTRATOS
def generate_detailed_statement(user_phone, start_date, end_date, title):
    print(f"Iniciando geração de extrato detalhado para {user_phone}...")
    try:
        user_df = get_user_data(user_phone)
        if user_df is None:
            send_whatsapp_message(user_phone, "Não encontrei gastos registrados para o período solicitado.")
            return

        statement_df = user_df[(user_df['Data'] >= start_date) & (user_df['Data'] <= end_date)]

        if statement_df.empty:
            send_whatsapp_message(user_phone, "Você não teve nenhum gasto registrado no período solicitado.")
            return

        statement_df = statement_df.sort_values(by='Data')
        report_lines = [f"*{title}*"]

        for index, row in statement_df.iterrows():
            date_str = row['Data'].strftime('%d/%m/%Y')
            category = row['Categoria']
            value = row['Valor']
            valor_formatado_br = f"{row['Valor']:,.2f}".replace(',', '#').replace('.', ',').replace('#', '.')
            report_lines.append(f"• {date_str} - {category.capitalize()}: *R$ {valor_formatado_br}*")

        total_spent = statement_df['Valor'].sum()
        total_spent_br = f"{total_spent:,.2f}".replace(',', '#').replace('.', ',').replace('#', '.')
        report_lines.append("\n-----------------------------------")
        report_lines.append(f"*Total do Período: R$ {total_spent_br}*")

        final_report = "\n".join(report_lines)
        send_whatsapp_message(user_phone, final_report)
        print(f"Extrato detalhado enviado para {user_phone}.")
    except Exception as e:
        print(f"Erro ao gerar extrato detalhado: {e}")
        send_whatsapp_message(user_phone, "Desculpe, não consegui gerar seu extrato.")

# FUNÇÃO DE ENVIO DE MENSAGEM
def send_whatsapp_message(to_number, message_text):
    """Envia uma mensagem de texto via Evolution API."""
    url = f"{EVOLUTION_API_URL}/message/sendText/{EVOLUTION_INSTANCE}"
    headers = {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json",
    }
    # Formato do corpo da mensagem
    data = {
        "number": to_number,
        "textMessage": {
            "text": message_text
        }
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        print(f"Mensagem enviada para {to_number}: {response.json()}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Erro ao enviar mensagem via Evolution API: {e}")
        if e.response is not None:
            print(f"Detalhes do erro: {e.response.text}")
        return False

#Função para verificar se é um novo usuário.
def is_new_user(user_phone):
    try:
        # findall procura por uma string em toda a planilha.
        # Se não encontrar nada, a lista estará vazia.
        found_cells = sheet.findall(user_phone)
        return len(found_cells) == 0
    except Exception as e:
        print(f"Erro ao verificar se o usuário é novo: {e}")
        return False

# PROCESSA A MENSAGEM E ADICIONA OS DADOS A PLANILHA
def add_expense_to_sheet(user_phone, message_body):
    if not sheet:
        return "Desculpe, estou com problemas para acessar a planilha no momento."
    try:
        parts = [item.strip() for item in message_body.split('-')]
        date_str, value_str, category_str = parts

        #FORMATAÇÃO DA DATA
        date_parts = date_str.split('/')
        if len(date_parts) == 2: # Usuário digitou apenas dia e mês (ex: 01/10)
            current_year = datetime.now().year
            date_str = f"{date_str}/{current_year}" # Adiciona o ano atual

        try:
            # Converte a data do usuário para um objeto de data
            expense_date = datetime.strptime(date_str, '%d/%m/%Y')
            # Pega a data de hoje, mas zera a hora para comparar apenas os dias
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            if expense_date > today:
                return f"🗓️ Erro: A data {date_str} é no futuro. Por favor, registre apenas despesas de hoje ou de dias anteriores."
        except ValueError:
            return f"❌ Formato de data inválido: '{date_str}'. Use DD/MM ou DD/MM/AAAA."

        value = float(value_str.replace(',', '.'))
        new_row = [user_phone, date_str, value, category_str, datetime.now().strftime('%Y-%m-%d')]
        sheet.append_row(new_row)

        check_spending_goal(user_phone)

        # Retorna a data completa para o usuário saber que o ano foi adicionado
        return f"✅ Gasto de R$ {value:.2f} na categoria '{category_str}' registrado para {date_str}!"

    except ValueError:
        return "❌ Formato inválido. Use: Data - Valor - Categoria\nExemplo: 02/10 - 15,50 - Lanche"
    except Exception as e:
        print(f"Erro inesperado ao processar a despesa: {e}")
        return "😕 Ocorreu um erro interno. Tente novamente."


#SALVA O FEEDBACK NA PLANILHA
def handle_feedback_submission(user_phone, feedback_text):
    if not sheet_ratings:
        send_whatsapp_message(user_phone, "Ocorreu um erro ao salvar seu feedback. Tente novamente mais tarde.")
        return
    try:
        # Encontra a última avaliação feita pelo usuário para adicionar o feedback
        user_cells = sheet_ratings.findall(str(user_phone))
        if user_cells:
            last_rating_row = user_cells[-1].row
            # A coluna 'Feedback' é a 4ª coluna (D)
            sheet_ratings.update_cell(last_rating_row, 4, feedback_text)
            send_whatsapp_message(user_phone, "Obrigado! Seu feedback foi registrado e nos ajudará a melhorar. 😊")
        else:
            send_whatsapp_message(user_phone, "Não encontrei uma avaliação recente para associar a este feedback.")
    except Exception as e:
        print(f"Erro ao salvar feedback de {user_phone}: {e}")

#FUNÇÃO PARA VERIFICAR ALERTA
def check_spending_goal(user_phone):
    print(f"Verificando alertas de meta para {user_phone}...")
    try:
        # 1. Busca a meta e o status dos alertas do usuário
        cell = sheet_goals.find(str(user_phone))
        if not cell:
            print("Usuário não possui meta definida. Alertas não serão verificados.")
            return

        goal_row_index = cell.row
        goal_row_values = sheet_goals.row_values(goal_row_index)

        goal_amount = float(goal_row_values[1])
        # Garante que temos todos os valores, mesmo que a coluna tenha sido adicionada agora
        alert_50_sent = goal_row_values[2] if len(goal_row_values) > 2 else 'FALSE'
        alert_80_sent = goal_row_values[3] if len(goal_row_values) > 3 else 'FALSE'
        alert_month = goal_row_values[4] if len(goal_row_values) > 4 else ''
        alert_100_sent = goal_row_values[5] if len(goal_row_values) > 5 else 'FALSE'

        # 2. Reseta os alertas se o mês mudou
        current_month_str = datetime.now().strftime('%Y-%m')
        if alert_month != current_month_str:
            print(f"Novo mês detectado. Resetando todos os alertas para {user_phone}.")
            sheet_goals.update_cell(goal_row_index, 3, 'FALSE') # Alerta 50%
            sheet_goals.update_cell(goal_row_index, 4, 'FALSE') # Alerta 80%
            sheet_goals.update_cell(goal_row_index, 5, current_month_str) # Mês do Alerta
            sheet_goals.update_cell(goal_row_index, 6, 'FALSE') # <<< ADICIONADO: Reseta o alerta de 100%
            alert_50_sent = 'FALSE'
            alert_80_sent = 'FALSE'
            alert_100_sent = 'FALSE'

        # 3. Calcula o total de gastos do mês
        user_df = get_user_data(user_phone)
        if user_df is None: return

        today = datetime.now()
        start_of_month = today.replace(day=1, hour=0, minute=0)
        month_df = user_df[(user_df['Data'] >= start_of_month) & (user_df['Data'] <= today)]
        total_spent = month_df['Valor'].sum()

        # 4. Verifica e envia os alertas na ordem correta (100%, 80%, 50%)
        percentage = (total_spent / goal_amount) * 100

        # Verifica o alerta de 100% primeiro
        if percentage >= 100 and alert_100_sent == 'FALSE':
            alert_text = (
                f"🚨 ATENÇÃO: META ATINGIDA! 🚨\n\n"
                f"Você atingiu *100%* da sua meta mensal de R$ {goal_amount:,.2f}!\n\n"
                f"Total gasto no mês: *R$ {total_spent:,.2f}*".replace(',', '.')
            )
            send_whatsapp_message(user_phone, alert_text)
            sheet_goals.update_cell(goal_row_index, 6, 'TRUE') # Atualiza a coluna F

        # Se o de 100% não foi enviado, verifica o de 80%
        elif percentage >= 80 and alert_80_sent == 'FALSE':
            alert_text = (
                f"‼️ ALERTA DE GASTOS ‼️\n\n"
                f"Você já ultrapassou *80%* da sua meta mensal de R$ {goal_amount:,.2f}!\n\n"
                f"Total gasto no mês: *R$ {total_spent:,.2f}*".replace(',', '.')
            )
            send_whatsapp_message(user_phone, alert_text)
            sheet_goals.update_cell(goal_row_index, 4, 'TRUE')

        # Se os outros não foram enviados, verifica o de 50%
        elif percentage >= 50 and alert_50_sent == 'FALSE':
            alert_text = (
                f"⚠️ Alerta de Gastos ⚠️\n\n"
                f"Você já ultrapassou *50%* da sua meta mensal de R$ {goal_amount:,.2f}!\n\n"
                f"Total gasto no mês: *R$ {total_spent:,.2f}*".replace(',', '.')
            )
            send_whatsapp_message(user_phone, alert_text)
            sheet_goals.update_cell(goal_row_index, 3, 'TRUE')

    except Exception as e:
        print(f"Erro ao verificar alertas de meta para {user_phone}: {e}")


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
            
            state_info = user_state.get_user_state(user_phone)

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

            current_week = ["esta semana", "desta semana", "semana atual", "atual", "esta", "desta","dessa"]

            last_month = ["mês passado", "mes passado", "passado", "mês anterior", "mes anterior", "anterior"]

            current_month = ["este mês", "este mes", "este", "atual", "deste mes", "deste mês", "deste", "mês atual", "mes atual"]




            # --- LÓGICA DE ESTADO ---
            # O usuário está respondendo a uma pergunta do bot?
            if state_info:
                state = state_info.get('state')

                if state == 'awaiting_suggestion':
                    if sheet_suggestions:
                        # Salva a sugestão na planilha
                        sheet_suggestions.append_row([user_phone, datetime.now().strftime('%d/%m/%Y'), message_body])
                        send_whatsapp_message(user_phone, "✅ Obrigado! Sua sugestão foi registrada com sucesso e será analisada pela nossa equipe.")
                    else:
                        send_whatsapp_message(user_phone, "😕 Desculpe, ocorreu um erro interno ao salvar sua sugestão. Tente novamente mais tarde.")
                    user_state.clear_user_state(user_phone)


                elif state == 'awaiting_goal_amount':
                    try:
                        goal_value = float(message_body.replace(',', '.'))
                        if goal_value > 0:
                            user_cell = sheet_goals.find(str(user_phone))
                            current_month_str = datetime.now().strftime('%Y-%m')

                            if user_cell: # Se o usuário já tem uma meta, atualiza
                                row = user_cell.row
                                sheet_goals.update_cell(row, 2, goal_value) # Atualiza Meta
                                sheet_goals.update_cell(row, 3, current_month_str) # Atualiza Mês
                                sheet_goals.update_cell(row, 4, 'FALSE') # Reseta Alerta 50%
                                sheet_goals.update_cell(row, 5, 'FALSE') # Reseta Alerta 80%
                            else: # Se for novo, adiciona
                                sheet_goals.append_row([user_phone, goal_value, current_month_str, 'FALSE', 'FALSE'])

                            send_whatsapp_message(user_phone, f"✅ Sua nova meta de gastos mensais foi definida para *R$ {goal_value:,.2f}*.".replace(',', '.'))
                            user_state.clear_user_state(user_phone)
                        else:
                            send_whatsapp_message(user_phone, "Por favor, envie um valor positivo para a meta.")
                    except ValueError:
                        send_whatsapp_message(user_phone, "Valor inválido. Por favor, envie apenas o número da sua meta (ex: 1500.50).")

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
                            generate_summary_report(user_phone, start_date, end_date, title)
                        elif state_info['type'] == 'detailed':
                            generate_detailed_statement(user_phone, start_date, end_date, title)
                        user_state.clear_user_state(user_phone)
                    else:
                        send_whatsapp_message(user_phone, "Opção inválida. Por favor, responda com 'esta semana' ou 'semana anterior'.")


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
                            generate_summary_report(user_phone, start_date, end_date, title)
                        elif state_info['type'] == 'detailed':
                            generate_detailed_statement(user_phone, start_date, end_date, title)
                        user_state.clear_user_state(user_phone)
                    else:
                        send_whatsapp_message(user_phone, "Opção inválida. Por favor, responda com 'este mês' ou 'mês anterior'.")

                elif state == 'awaiting_rating':
                    try:
                        rating = int(message_body)
                        if 0 <= rating <= 5:
                            if not sheet_ratings:
                                raise Exception("A planilha de avaliações não foi conectada.")
                            # Salva a nota na planilha de avaliações
                            sheet_ratings.append_row([user_phone, datetime.now().strftime('%d/%m/%Y'), rating, ''])
                            if rating <= 3:
                                send_whatsapp_message(user_phone, "Obrigado pela sua nota. Gostaríamos de saber mais. Você gostaria de deixar um feedback para nos ajudar a melhorar? (Responda com seu feedback ou 'não')")
                                user_state.set_user_state(user_phone, {'state': 'awaiting_feedback'}) # Muda o estado para aguardar o feedback
                            else:
                                send_whatsapp_message(user_phone, "Ficamos felizes com a sua nota! Obrigado por avaliar nosso sistema. 😄")
                                user_state.clear_user_state(user_phone) # Finaliza o estado de avaliação
                        else:
                            send_whatsapp_message(user_phone, "Nota inválida. Por favor, envie um número de 0 a 5.")
                    except ValueError:
                        send_whatsapp_message(user_phone, "Por favor, envie apenas o número da sua nota (de 0 a 5).")

                elif state == 'awaiting_feedback':
                    if message_body not in ['nao', 'não', "n"]:
                        handle_feedback_submission(user_phone, message_body)
                    else:
                        send_whatsapp_message(user_phone, "Entendido. Agradecemos sua avaliação mesmo assim!")
                    user_state.clear_user_state(user_phone) # Finaliza o estado de avaliação

                return jsonify({"status": "OK"}), 200 # Finaliza o processamento aqui


            if  message_body in suggestion:
                send_whatsapp_message(user_phone, "Ficamos felizes em ouvir sua opinião! Por favor, envie sua sugestão de melhoria em uma única mensagem.")
                user_state.set_user_state(user_phone, {'state': 'awaiting_suggestion'})

            elif  message_body in goal:
                send_whatsapp_message(user_phone, "Qual valor você gostaria de definir como sua meta de gastos mensais?")
                user_state.set_user_state(user_phone, {'state': 'awaiting_goal_amount'})

            elif message_body in assessment:
                send_whatsapp_message(user_phone, "Que bom que você quer nos avaliar! Por favor, envie uma nota de 0 a 5 para o sistema.")
                user_state.set_user_state(user_phone, {'state': 'awaiting_rating'})

            elif message_body in weeklyStatement:
                send_whatsapp_message(user_phone, "Você gostaria do extrato desta semana ou da semana anterior?")
                user_state.set_user_state(user_phone, {'state': 'awaiting_week_choice', 'type': 'detailed', 'title': 'Extrato Semanal'})

            elif message_body in monthlyStatement:
                send_whatsapp_message(user_phone, "Você gostaria do extrato deste mês ou do mês anterior?")
                user_state.set_user_state(user_phone, {'state': 'awaiting_month_choice', 'type': 'detailed', 'title': 'Extrato Mensal'})

            elif message_body in weeklyReport:
                send_whatsapp_message(user_phone, "Você gostaria do relatório desta semana ou da semana anterior?")
                user_state.set_user_state(user_phone, {'state': 'awaiting_week_choice', 'type': 'summary', 'title': 'Relatório Semanal'})

            elif message_body in monthlyReport:
                send_whatsapp_message(user_phone, "Você gostaria do relatório deste mês ou do mês anterior?")
                user_state.set_user_state(user_phone, {'state': 'awaiting_month_choice', 'type': 'summary', 'title': 'Relatório Mensal'})

            elif message_body in greetings:
                if is_new_user(user_phone):
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
                    send_whatsapp_message(user_phone, welcome_text)

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
                    send_whatsapp_message(user_phone, refresher_text)

            elif message_body: # <<< Se não for saudação, processa como gasto
                response_text = add_expense_to_sheet(user_phone, message_body)
                send_whatsapp_message(user_phone, response_text)

    except Exception as e:
        print(f"Erro ao processar webhook: Estrutura de dados inesperada. Erro: \n\n{e}")
        # Tenta notificar o usuário que algo deu errado, se possível
        try:
            user_phone = request.get_json()['data']['key']['remoteJid'].split('@')[0]
            send_whatsapp_message(user_phone, "😕 Ops! Ocorreu um erro interno ao processar sua mensagem. A equipe já foi notificada.")
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


