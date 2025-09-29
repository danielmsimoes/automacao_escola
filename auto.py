import os
import time
import threading
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import customtkinter as ctk
from tkinter import filedialog
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

USUARIO = os.getenv("USUARIO_ESCOLA")
SENHA = os.getenv("SENHA_ESCOLA")


def criar_driver_visivel():
    options = Options()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    return driver

class AutomacaoINSS:
    def __init__(self, pasta, usuario, senha, app):
        self.pasta = pasta
        self.usuario = usuario
        self.senha = senha
        self.driver = criar_driver_visivel()
        self.app = app

        self.nome_base = os.path.basename(pasta.rstrip("/\\"))
        self.pasta_sucessos = f"sucesso{self.nome_base}"
        self.pasta_erros = f"erros{self.nome_base}"

        os.makedirs(self.pasta_sucessos, exist_ok=True)
        os.makedirs(self.pasta_erros, exist_ok=True)

        self.processados = 0
        self.sucessos = 0
        self.erros = 0
        self.parar = False

    def log(self, mensagem):
        def inserir_log():
            self.app.label_logs.configure(state="normal")
            self.app.label_logs.insert("end", mensagem + "\n")
            self.app.label_logs.see("end")
            self.app.label_logs.configure(state="disabled")
        self.app.after(0, inserir_log)

    def salvar_erro(self, codigo):
        nome_arquivo = f"{codigo}_erro.png"
        caminho_print = os.path.join(self.pasta_erros, nome_arquivo)
        self.driver.save_screenshot(caminho_print)
        print(f"❌ Print de erro salvo: {nome_arquivo}")

    def salvar_sucesso(self, codigo):
        caminho_arquivo = os.path.join(self.pasta_sucessos, "sucessos.txt")
        with open(caminho_arquivo, "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{codigo} - Importação concluída com sucesso em {timestamp}\n")

    def login(self):
        tentativas = 3
        for tentativa in range(1, tentativas + 1):
            try:
                self.log(f"🔑 Tentativa {tentativa} de login...")
                self.driver.get("https://escola.inss.gov.br/login/index.php")

                self.log("⏳ Preenchendo usuário...")
                WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.ID, 'username'))).send_keys(self.usuario)

                self.log("⏳ Preenchendo senha...")
                WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.ID, 'password'))).send_keys(self.senha)

                self.log("⏳ Clicando no botão de login...")
                WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, 'loginbtn'))).click()

                self.log("⏳ Aguardando carregamento da página principal...")
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'page-header')))
                
                self.log("✅ Login realizado com sucesso na Escola INSS")
                return True
            except Exception as e:
                self.log(f"❌ Erro ao fazer login na tentativa {tentativa}: {e}")
                if tentativa < tentativas:
                    self.log("🔁 Tentando novamente em 3 segundos...")
                    time.sleep(3)
                else:
                    self.log("⛔ Todas as tentativas de login falharam.")
                    return False

    def atualizar_labels(self):
        def update():
            self.app.label_processados.configure(text=f"Processados: {self.processados}")
            self.app.label_sucessos.configure(text=f"Sucessos: {self.sucessos}")
            self.app.label_erros.configure(text=f"Erros: {self.erros}")
        self.app.after(0, update)

    def executar(self):
        inicio = time.time()

        if not self.login():
            self.app.label_status.configure(text="❌ Falha no login. Verifique credenciais.")
            return
        
        arquivos_csv = [f for f in os.listdir(self.pasta) if f.endswith('.csv')]
        total = len(arquivos_csv)
        self.app.label_status.configure(text=f"Iniciando processamento de {total} arquivos...")

        for arquivo in arquivos_csv:
            if self.parar:
                self.app.label_status.configure(text="⛔ Execução interrompida pelo usuário.")
                self.log("⛔ Execução interrompida pelo usuário.")
                break

            codigo = os.path.splitext(arquivo)[0]
            caminho_arquivo = os.path.abspath(os.path.join(self.pasta, arquivo))
            url = f"https://escola.inss.gov.br/course/search.php?areaids=core_course-course&q={codigo}"
            self.log(f"\n🔎 Acessando curso: {codigo}")
            self.driver.get(url)

            try:
                self.log("⏳ Clicando no nome do curso...")
                WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.coursename"))).click()
                time.sleep(0.5)

                self.log("⏳ Clicando no link 'Notas'...")
                WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, "Notas"))).click()
                time.sleep(0.5)

                self.log("⏳ Clicando em 'Relatório de notas'...")
                WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Relatório de notas')]"))).click()
                time.sleep(0.5)

                self.log("⏳ Procurando opção 'Importar'...")
                elemento_importar = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//li[contains(text(), 'Importar')]")))
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elemento_importar)
                elemento_importar.click()
                time.sleep(0.5)

                self.log("⏳ Clicando no botão para escolher arquivo...")
                botao_escolher_arquivo = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input.fp-btn-choose"))).click()
                time.sleep(0.5)

                self.log(f"⏳ Selecionando arquivo CSV: {caminho_arquivo}")
                input_file = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file'][name='repo_upload_file']")))
                self.driver.execute_script("arguments[0].style.display = 'block'; arguments[0].style.visibility = 'visible';", input_file)
                input_file.send_keys(caminho_arquivo)
                time.sleep(0.5)

                self.log("⏳ Confirmando upload...")
                WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.fp-upload-btn.btn-primary.btn"))).click()
                time.sleep(0.5)

                self.log("⏳ Confirmando envio do arquivo...")
                WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "id_submitbutton"))).click()
                time.sleep(0.5)

                self.log("⏳ Mapeando campos do arquivo...")

                # Selecionar o campo de origem: email
                dropdown_mapear_de = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "id_mapfrom"))
                )
                Select(dropdown_mapear_de).select_by_visible_text("email")
                time.sleep(0.5)

                # Selecionar o campo de destino: Endereço de e-mail
                dropdown_mapear_para = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "id_mapto"))
                )
                Select(dropdown_mapear_para).select_by_visible_text("Endereço de e-mail")
                time.sleep(0.5)

                # Selecionar o campo de nota
                dropdown_nota_final = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "id_mapping_3"))
                )
                Select(dropdown_nota_final).select_by_visible_text("Questionário: Avaliação da Aprendizagem")
                time.sleep(1)

                self.log("⏳ Confirmando importação...")
                WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "id_submitbutton"))).click()

                self.log("⏳ Aguardando mensagem de sucesso...")
                WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".alert-success")))

                self.sucessos += 1
                self.salvar_sucesso(codigo)
                self.log(f"🎉 Importação de notas bem-sucedida para o curso {codigo}!\n")

            except Exception as e:
                self.log(f"❌ Erro ao processar {codigo}: {e}")
                self.erros += 1
                self.salvar_erro(codigo)

            self.processados += 1
            self.atualizar_labels()

        fim = time.time()
        tempo_formatado = time.strftime("%H:%M:%S", time.gmtime(fim - inicio))
        self.app.label_status.configure(text=f"✅ Processo finalizado. {self.sucessos} sucesso(s), {self.erros} erro(s).")
        self.log(f"✅ Processo finalizado. {self.sucessos} sucesso(s), {self.erros} erro(s).")
        self.log(f"🕒 Duração total: {tempo_formatado}")
        self.driver.quit()

# --- Interface ---
def iniciar_automacao():
    pasta_selecionada = filedialog.askdirectory(title="Selecione a pasta com os arquivos CSV")
    if not pasta_selecionada:
        label_status.configure(text="❌ Nenhuma pasta selecionada.")
        return

    bot_iniciar.configure(state="disabled")
    bot_parar.configure(state="normal")
    label_status.configure(text="🔄 Executando automação...")

    def run():
        app.automacao = AutomacaoINSS(pasta_selecionada, USUARIO, SENHA, app)
        app.automacao.executar()
        bot_iniciar.configure(state="normal")
        bot_parar.configure(state="disabled")

    threading.Thread(target=run, daemon=True).start()

def parar_automacao():
    if hasattr(app, "automacao"):
        app.automacao.parar = True
    label_status.configure(text="⏸ Tentando parar...")

# --- Interface Gráfica ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
app = ctk.CTk()
app.title("Automação Escola INSS")
app.geometry("420x500")

label_titulo = ctk.CTkLabel(app, text="Automação Escola INSS", font=ctk.CTkFont(size=20, weight="bold"))
label_titulo.pack(pady=12)

bot_iniciar = ctk.CTkButton(app, text="Iniciar Automação", command=iniciar_automacao)
bot_iniciar.pack(pady=8)

bot_parar = ctk.CTkButton(app, text="Parar Automação", command=parar_automacao, state="disabled")
bot_parar.pack(pady=8)

label_status = ctk.CTkLabel(app, text="Status: Aguardando início...", font=ctk.CTkFont(size=14))
label_status.pack(pady=8)

frame_contadores = ctk.CTkFrame(app)
frame_contadores.pack(pady=8)

label_processados = ctk.CTkLabel(frame_contadores, text="Processados: 0")
label_processados.grid(row=0, column=0, padx=8)

label_sucessos = ctk.CTkLabel(frame_contadores, text="Sucessos: 0")
label_sucessos.grid(row=0, column=1, padx=8)

label_erros = ctk.CTkLabel(frame_contadores, text="Erros: 0")
label_erros.grid(row=0, column=2, padx=8)

label_logs = ctk.CTkTextbox(app, width=400, height=250, state="disabled")
label_logs.pack(pady=8)

app.label_processados = label_processados
app.label_sucessos = label_sucessos
app.label_erros = label_erros
app.label_logs = label_logs
app.label_status = label_status

app.mainloop()
