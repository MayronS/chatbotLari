from . import connectSheet
from datetime import datetime
from alert import checkAlert

# PROCESSA A MENSAGEM E ADICIONA OS DADOS A PLANILHA
def add_expense_to_sheet(user_phone, message_body):
    if not connectSheet.sheet:
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
        connectSheet.sheet.append_row(new_row)

        checkAlert.check_spending_goal(user_phone)

        # Retorna a data completa para o usuário saber que o ano foi adicionado
        return f"✅ Gasto de R$ {value:.2f} na categoria '{category_str}' registrado para {date_str}!"

    except ValueError:
        return "❌ Formato inválido. Use: Data - Valor - Categoria\nExemplo: 02/10 - 15,50 - Lanche"
    except Exception as e:
        print(f"Erro inesperado ao processar a despesa: {e}")
        return "😕 Ocorreu um erro interno. Tente novamente."

