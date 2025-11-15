from datetime import datetime
from . import connectSheet
import traceback

def _parse_expense_string(expense_string):

    date_str, value_str, category_str = None, None, None
    try:
        if '-' in expense_string:
            parts = [item.strip() for item in expense_string.split('-')]
            if len(parts) == 3: 
                date_str, value_str, category_str = parts
        else:
            parts = expense_string.split(' ', 2)
            if len(parts) == 3:
                date_str = parts[0].strip()
                value_str = parts[1].strip()
                category_str = parts[2].strip()
        
        if not date_str:
            return None, None, None

        # Completa o ano se necessário
        date_parts = date_str.split('/')
        if len(date_parts) == 2:
            current_year = datetime.now().year
            date_str = f"{date_str}/{current_year}"
        
        value_str = value_str.replace(',', '.')
        category_str = category_str.lower()
        
        return date_str, value_str, category_str
        
    except Exception as e:
        print(f"Erro ao analisar string de despesa: {e}")
        return None, None, None

def delete_expense_from_sheet(user_phone, expense_string):

    if not connectSheet.sheet:
        return "😕 Desculpe, estou com problemas para conectar à planilha."

    # Analisa e normaliza a entrada do usuário
    date_str, value_str, category_str = _parse_expense_string(expense_string)
    
    if not date_str:
        return (
            "❌ Formato inválido. Use:\n"
            "`apagar data valor categoria`\n\n"
            "Exemplo: `apagar 08/10 20 lanche`"
        )
    
    try:
        sheet = connectSheet.sheet
        
        user_cells = sheet.findall(str(user_phone))
        
        rows_to_delete = []
        
        user_value_float = float(value_str)
        
        for cell in user_cells:
            try:
                row_data = sheet.row_values(cell.row)
                
                sheet_date = str(row_data[1])
                sheet_value = str(row_data[2]).replace(',', '.')
                sheet_category = str(row_data[3]).lower()
                
                sheet_value_float = float(sheet_value)
                
                if (sheet_date == date_str and 
                    sheet_value_float == user_value_float and 
                    sheet_category == category_str):
                    
                    rows_to_delete.append(cell.row)
            except Exception:
                continue

        # Processa o resultado
        if not rows_to_delete:
            return "🤷 Despesa não encontrada. Verifique se a data, valor e categoria estão *exatamente* iguais."
        rows_to_delete.sort(reverse=True)
        
        for row_index in rows_to_delete:
            sheet.delete_rows(row_index)
        
        count = len(rows_to_delete)
        plural_s = "s" if count > 1 else ""
        foi_foram = "foram" if count > 1 else "foi"
        
        sheet.delete_rows(rows_to_delete[0])
        
        valor_formatado_br = f"{float(value_str):,.2f}".replace(',', '#').replace('.', ',').replace('#', '.')
        return f"✅ {count} despesa{plural_s} de {date_str} (R$ {valor_formatado_br}) {foi_foram} apagada{plural_s} com sucesso."

    except Exception as e:
        print(f"Erro ao apagar despesa: {e}\n{traceback.format_exc()}")
        return "😕 Ocorreu um erro interno ao tentar apagar a despesa."