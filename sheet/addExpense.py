from . import connectSheet
from datetime import datetime
from alert import checkAlert

# PROCESSA A MENSAGEM E ADICIONA OS DADOS A PLANILHA
def add_expense_to_sheet(user_phone, message_body):
    if not connectSheet.sheet:
        return "Desculpe, estou com problemas para acessar a planilha no momento."
    try:
        date_str = None
        value_str = None
        category_str = None
        
        # Detecta o formato da mensagem
        if '-' in message_body:

            parts = [item.strip() for item in message_body.split('-')]
            # FORMATO: "data - valor - categoria"
            if len(parts) == 3:
                date_str, value_str, category_str = parts
                
            # FORMATO: "Valor - Categoria"
            elif len(parts) == 2:
                date_str = "auto"
                value_str, category_str = parts
            
        else:
            # Divide no máximo 2 vezes, para permitir categorias com espaços
            parts = message_body.split(' ', 2) 
            
            if len(parts) == 3:
                # FORMATO: "data valor categoria"
                date_str = parts[0].strip()
                value_str = parts[1].strip()
                category_str = parts[2].strip()
            
            elif len(parts) == 2:
                # FORMATO: "valor categoria"
                date_str = "auto"
                value_str = parts[0].strip()
                category_str = parts[1].strip()

        #FORMATAÇÃO DA DATA
        if date_str == "auto":
            date_obj = datetime.now()
            date_str = date_obj.strftime('%d/%m/%Y')
        else:
            date_parts = date_str.split('/')
            if len(date_parts) == 2: # Usuário digitou apenas dia e mês (ex: 01/10)
                current_year = datetime.now().year
                date_str = f"{date_str}/{current_year}"

            try:
                expense_date = datetime.strptime(date_str, '%d/%m/%Y')
                # Pega a data de hoje, mas zera a hora para comparar apenas os dias
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

                if expense_date > today:
                    return f"🗓️ Erro: A data {date_str} é no futuro. Por favor, registre apenas despesas de hoje ou de dias anteriores."
            except ValueError:
                return f"❌ Formato de data inválido: '{date_str}'. Use DD/MM ou DD/MM/AAAA."

        try:
            value = float(value_str.replace(',', '.'))
        except ValueError:
            return f"❌ Valor inválido: '{value_str}'. O valor deve vir antes da categoria."
        
        if not category_str:
            return "❌ Categoria não informada. Por favor, informe uma categoria."
        
        new_row = [user_phone, date_str, value, category_str, datetime.now().strftime('%Y-%m-%d')]
        connectSheet.sheet.append_row(new_row)

        checkAlert.check_spending_goal(user_phone)

        # Retorna a data completa, valor e categoria para o usuário saber que o ano foi adicionado
        return f"✅ Gasto de R$ {value:.2f} na categoria '{category_str}' registrado para {date_str}!"

    except ValueError:
        # Retorna um alerta para o usuário caso o formato esteja incorreto
        return "❌ Formato inválido. Use um dos formatos abaixo:\n Data - Valor - Categoria\n Data Valor Categoria\n para compras de hoje, use:\n Valor Categoria\nValor - Categoria"
    except Exception as e:
        print(f"Erro inesperado ao processar a despesa: {e}")
        return "😕 Ocorreu um erro interno. Tente novamente."

