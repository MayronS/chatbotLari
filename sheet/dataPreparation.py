from . import connectSheet
import pandas as pd

    #BUSCA OS DADOS E PREPARA
def get_user_data(user_phone):
    records = connectSheet.sheet.get_all_records(value_render_option='UNFORMATTED_VALUE')
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
