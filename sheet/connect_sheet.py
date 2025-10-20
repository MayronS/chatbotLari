from oauth2client.service_account import ServiceAccountCredentials
import gspread

sheet_states = None
sheet = None
sheet_ratings = None
sheet_goals = None
sheet_suggestions = None

def sheets():
  global sheet, sheet_ratings, sheet_goals, sheet_suggestions, sheet_states
  
  try:
      SCOPE = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/drive']
      CREDS = ServiceAccountCredentials.from_json_keyfile_name("/credentials.json", SCOPE)
      gclient = gspread.authorize(CREDS)

      # Conecta à planilha de gastos
      workbook_expenses = gclient.open("Planilha_gastos")
      sheet = workbook_expenses.worksheet("Gastos")

      # Conecta à planilha de avaliações
      workbook_ratings = gclient.open("Avaliações")
      sheet_ratings = workbook_ratings.sheet1

      # Conecta à planilha de metas
      workbook_goals = gclient.open("Metas")
      sheet_goals = workbook_goals.sheet1

      # Conecta à planilha de sugestoes
      workbook_suggestions = gclient.open("Sugestoes")
      sheet_suggestions = workbook_suggestions.sheet1
      
      # Conecta a planilha de estados
      workbook_states = gclient.open("UserStates")
      sheet_states = workbook_states.sheet1


      print("Conexão com todas as planilhas bem-sucedida!")
  except Exception as e:
      print(f"Ocorreu um erro ao conectar com o Google Sheets: {e}")
