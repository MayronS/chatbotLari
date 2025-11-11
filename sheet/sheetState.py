import json
from . import connectSheet

    #FUNÇÕES PARA GERENCIAR O ESTADO NA PLANILHA
def set_user_state(user_phone, state_data):
    try:
        cell = connectSheet.sheet_states.find(str(user_phone))
        state_str = json.dumps(state_data)
        if cell:
            connectSheet.sheet_states.update_cell(cell.row, 2, state_str)
        else:
            connectSheet.sheet_states.append_row([str(user_phone), state_str])
        print(f"Estado de {user_phone} salvo: {state_str}")
    except Exception as e:
        print(f"Erro ao salvar estado para {user_phone}: {e}")

def get_user_state(user_phone):
    try:
        cell = connectSheet.sheet_states.find(str(user_phone))
        if cell:
            state_str = connectSheet.sheet_states.cell(cell.row, 2).value
            if state_str:
                print(f"Estado de {user_phone} encontrado: {state_str}")
                return json.loads(state_str)
        return None
    except Exception as e:
        print(f"Erro ao buscar estado para {user_phone}: {e}")
        return None

def clear_user_state(user_phone):
    try:
        cell = connectSheet.sheet_states.find(str(user_phone))
        if cell:
            connectSheet.sheet_states.update_cell(cell.row, 2, "") # Limpa a célula do estado
            print(f"Estado de {user_phone} limpo.")
    except Exception as e:
        print(f"Erro ao limpar estado para {user_phone}: {e}")
