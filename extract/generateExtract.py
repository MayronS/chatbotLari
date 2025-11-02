from sheet import dataPreparation
from message import sendMessage


#GERA OS EXTRATOS
def generate_detailed_statement(user_phone, start_date, end_date, title):
    print(f"Iniciando geração de extrato detalhado para {user_phone}...")
    try:
        user_df = dataPreparation.get_user_data(user_phone)
        if user_df is None:
            sendMessage.send_whatsapp_message(user_phone, "Não encontrei gastos registrados para o período solicitado.")
            return

        statement_df = user_df[(user_df['Data'] >= start_date) & (user_df['Data'] <= end_date)]

        if statement_df.empty:
            sendMessage.send_whatsapp_message(user_phone, "Você não teve nenhum gasto registrado no período solicitado.")
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
        sendMessage.send_whatsapp_message(user_phone, final_report)
        print(f"Extrato detalhado enviado para {user_phone}.")
    except Exception as e:
        print(f"Erro ao gerar extrato detalhado: {e}")
        sendMessage.send_whatsapp_message(user_phone, "Desculpe, não consegui gerar seu extrato.")

