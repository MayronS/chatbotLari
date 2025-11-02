from sheet import connectSheet, dataPreparation
from message import sendMessage
from datetime import datetime


#FUNÇÃO PARA VERIFICAR ALERTA
def check_spending_goal(user_phone):
    print(f"Verificando alertas de meta para {user_phone}...")
    try:
<<<<<<< HEAD
        # Busca a meta e o status dos alertas do usuário
=======
        # 1. Busca a meta e o status dos alertas do usuário
>>>>>>> 1b0fec1 (Mudando de local função check_spending_goal)
        cell = connectSheet.sheet_goals.find(str(user_phone))
        if not cell:
            print("Usuário não possui meta definida. Alertas não serão verificados.")
            return

        goal_row_index = cell.row
        goal_row_values = connectSheet.sheet_goals.row_values(goal_row_index)

        goal_amount = float(goal_row_values[1])
        # Garante que temos todos os valores, mesmo que a coluna tenha sido adicionada agora
        alert_50_sent = goal_row_values[2] if len(goal_row_values) > 2 else 'FALSE'
        alert_80_sent = goal_row_values[3] if len(goal_row_values) > 3 else 'FALSE'
        alert_month = goal_row_values[4] if len(goal_row_values) > 4 else ''
        alert_100_sent = goal_row_values[5] if len(goal_row_values) > 5 else 'FALSE'

<<<<<<< HEAD
        # Reseta os alertas se o mês mudou
=======
        # 2. Reseta os alertas se o mês mudou
>>>>>>> 1b0fec1 (Mudando de local função check_spending_goal)
        current_month_str = datetime.now().strftime('%Y-%m')
        if alert_month != current_month_str:
            print(f"Novo mês detectado. Resetando todos os alertas para {user_phone}.")
            connectSheet.sheet_goals.update_cell(goal_row_index, 3, 'FALSE') # Alerta 50%
            connectSheet.sheet_goals.update_cell(goal_row_index, 4, 'FALSE') # Alerta 80%
            connectSheet.sheet_goals.update_cell(goal_row_index, 5, current_month_str) # Mês do Alerta
<<<<<<< HEAD
            connectSheet.sheet_goals.update_cell(goal_row_index, 6, 'FALSE') #Reseta o alerta de 100%
=======
            connectSheet.sheet_goals.update_cell(goal_row_index, 6, 'FALSE') # <<< ADICIONADO: Reseta o alerta de 100%
>>>>>>> 1b0fec1 (Mudando de local função check_spending_goal)
            alert_50_sent = 'FALSE'
            alert_80_sent = 'FALSE'
            alert_100_sent = 'FALSE'

<<<<<<< HEAD
        # Calcula o total de gastos do mês
=======
        # 3. Calcula o total de gastos do mês
>>>>>>> 1b0fec1 (Mudando de local função check_spending_goal)
        user_df = dataPreparation.get_user_data(user_phone)
        if user_df is None: return

        today = datetime.now()
        start_of_month = today.replace(day=1, hour=0, minute=0)
        month_df = user_df[(user_df['Data'] >= start_of_month) & (user_df['Data'] <= today)]
        total_spent = month_df['Valor'].sum()

<<<<<<< HEAD
        # Verifica e envia os alertas na ordem correta (100%, 80%, 50%)
=======
        # 4. Verifica e envia os alertas na ordem correta (100%, 80%, 50%)
>>>>>>> 1b0fec1 (Mudando de local função check_spending_goal)
        percentage = (total_spent / goal_amount) * 100

        # Verifica o alerta de 100% primeiro
        if percentage >= 100 and alert_100_sent == 'FALSE':
            alert_text = (
                f"🚨 ATENÇÃO: META ATINGIDA! 🚨\n\n"
                f"Você atingiu *100%* da sua meta mensal de R$ {goal_amount:,.2f}!\n\n"
                f"Total gasto no mês: *R$ {total_spent:,.2f}*".replace(',', '.')
            )
            sendMessage.send_whatsapp_message(user_phone, alert_text)
<<<<<<< HEAD
            connectSheet.sheet_goals.update_cell(goal_row_index, 6, 'TRUE')
=======
            connectSheet.sheet_goals.update_cell(goal_row_index, 6, 'TRUE') # Atualiza a coluna F
>>>>>>> 1b0fec1 (Mudando de local função check_spending_goal)

        # Se o de 100% não foi enviado, verifica o de 80%
        elif percentage >= 80 and alert_80_sent == 'FALSE':
            alert_text = (
                f"‼️ ALERTA DE GASTOS ‼️\n\n"
                f"Você já ultrapassou *80%* da sua meta mensal de R$ {goal_amount:,.2f}!\n\n"
                f"Total gasto no mês: *R$ {total_spent:,.2f}*".replace(',', '.')
            )
            sendMessage.send_whatsapp_message(user_phone, alert_text)
            connectSheet.sheet_goals.update_cell(goal_row_index, 4, 'TRUE')

        # Se os outros não foram enviados, verifica o de 50%
        elif percentage >= 50 and alert_50_sent == 'FALSE':
            alert_text = (
                f"⚠️ Alerta de Gastos ⚠️\n\n"
                f"Você já ultrapassou *50%* da sua meta mensal de R$ {goal_amount:,.2f}!\n\n"
                f"Total gasto no mês: *R$ {total_spent:,.2f}*".replace(',', '.')
            )
            sendMessage.send_whatsapp_message(user_phone, alert_text)
            connectSheet.sheet_goals.update_cell(goal_row_index, 3, 'TRUE')

    except Exception as e:
        print(f"Erro ao verificar alertas de meta para {user_phone}: {e}")
