from sheet import dataPreparation
from message import sendMessage

#FUNÇÃO PARA GERAR O RELATORIO
def generate_summary_report(user_phone, start_date, end_date, title):
    print(f"Iniciando geração de relatório resumido para {user_phone}...")
    try:
        user_df = dataPreparation.get_user_data(user_phone)
        if user_df is None:
            sendMessage.send_whatsapp_message(user_phone, "Não encontrei gastos registrados para o período solicitado.")
            return

        period_df = user_df[(user_df['Data'] >= start_date) & (user_df['Data'] <= end_date)]

        if period_df.empty:
            sendMessage.send_whatsapp_message(user_phone, "Você não teve nenhum gasto registrado no período solicitado.")
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
        sendMessage.send_whatsapp_message(user_phone, final_report)
        print(f"Relatório resumido enviado para {user_phone}.")
    except Exception as e:
        print(f"Erro ao gerar relatório resumido: {e}")
        sendMessage.send_whatsapp_message(user_phone, "Desculpe, não consegui gerar seu relatório.\nTente novamente mais tarde.")
