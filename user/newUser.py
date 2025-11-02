from sheet import connectSheet

#Função para verificar se é um novo usuário.
def is_new_user(user_phone):
    try:
        # findall procura por uma string em toda a planilha.
        # Se não encontrar nada, a lista estará vazia.
        found_cells = connectSheet.sheet.findall(user_phone)
        return len(found_cells) == 0
    except Exception as e:
        print(f"Erro ao verificar se o usuário é novo: {e}")
        return False
