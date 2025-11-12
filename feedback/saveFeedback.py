from sheet import connectSheet
from message import sendMessage

#SALVA O FEEDBACK NA PLANILHA
def handle_feedback_submission(user_phone, feedback_text):
    if not connectSheet.sheet_ratings:
        sendMessage.send_whatsapp_message(user_phone, "Ocorreu um erro ao salvar seu feedback. Tente novamente mais tarde.")
        return
    try:
        # Encontra a última avaliação feita pelo usuário para adicionar o feedback
        user_cells = connectSheet.sheet_ratings.findall(str(user_phone))
        if user_cells:
            last_rating_row = user_cells[-1].row
            
            connectSheet.sheet_ratings.update_cell(last_rating_row, 4, feedback_text)
            sendMessage.send_whatsapp_message(user_phone, "Obrigado! Seu feedback foi registrado e nos ajudará a melhorar. 😊")
        else:
            sendMessage.send_whatsapp_message(user_phone, "Não encontrei uma avaliação recente para associar a este feedback.")
    except Exception as e:
        print(f"Erro ao salvar feedback de {user_phone}: {e}")
