from datetime import datetime
from . import connectSheet
import traceback
import pandas as pd

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
        
        if not value_str or not date_str or not category_str:
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
        return "😕 Desculpe, estou com problemas para conectar aos gastos, tente novamente mais tarde."

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
        
        all_data = sheet.get_all_records()
        
        df = pd.DataFrame(all_data)

        user_phone_str = str(user_phone)
        user_value_float = float(value_str)
        df['Identificador'] = pd.to_numeric(df['Identificador'], errors='coerce').astype('Int64').astype(str)
        df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce')
        df['Categoria'] = df['Categoria'].astype(str).str.lower()
        df['Data'] = df['Data'].astype(str)
        
        match_criteria = (
            (df['Identificador'] == user_phone_str) &
            (df['Data'] == date_str) &
            (df['Valor'] == user_value_float) &
            (df['Categoria'] == category_str)
        )
        
        rows_to_delete = df[match_criteria]
        if rows_to_delete.empty:
            return "🤷 Despesa não encontrada. Verifique se a data, valor e categoria estão *exatamente* iguais."
        sheet_row_indices = [idx + 2 for idx in rows_to_delete.index]
        sheet_row_indices.sort(reverse=True)
        for row_index in sheet_row_indices:
            sheet.delete_rows(row_index)
        count = len(sheet_row_indices)
        
        count = len(sheet_row_indices)
        plural_s = "s" if count > 1 else ""
        foi_foram = "foram" if count > 1 else "foi"
        
        valor_formatado_br = f"{float(value_str):,.2f}".replace(',', '#').replace('.', ',').replace('#', '.')
        return f"✅ {count} despesa{plural_s} de {date_str} (R$ {valor_formatado_br}) {foi_foram} apagada{plural_s} com sucesso."

    except Exception as e:
        print(f"Erro ao apagar despesa: {e}\n{traceback.format_exc()}")
        return "😕 Ocorreu um erro interno ao tentar apagar a despesa. Tente novamente mais tarde!"