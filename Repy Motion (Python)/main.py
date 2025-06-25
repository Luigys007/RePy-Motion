from tkinter import *
from tkinter import ttk, filedialog, simpledialog, messagebox
import os
import threading
import time
from PIL import Image, ImageTk
import funcoes as func
import serial

pastaApp = os.path.dirname(__file__)

# --- Variáveis Globais ---
passos_salvos = []
arquivo_salvo = ""
portaUSB = None
botao_ativo = False
velocidade = 5
status_atual = "Desconectado"

# --- Funções ---

def print_debug(msg):
    print(f"[DEBUG]: {msg}")

def atualizar_lista_passos():
    lista_passos.delete(0, END)
    for idx, passo in enumerate(passos_salvos, start=1):
        lista_passos.insert(END, f"{idx}: {passo}")

def atualizar_portas():
    cb_portas['values'] = func.serial_ports()

def atualizar_status(texto):
    global status_atual
    status_atual = texto
    status_label.config(text=f"Status: {texto}")

def conectar_porta():
    global portaUSB
    try:
        portaUSB = serial.Serial(cb_portas.get(), 9600, write_timeout=1)
        print(f"Conectado em {portaUSB.port}")
        velocidade_slider.set(5)
        atualizar_velocidade(5)
        atualizar_status("Conectado")
    except serial.SerialException as e:
        print(f"Erro de conexão: {e}")

def desconectar_porta():
    global portaUSB
    try:
        if portaUSB.is_open:
            portaUSB.close()
            print("Desconectado com sucesso.")
            atualizar_status("Desconectado")
    except NameError:
        print("Nenhuma porta conectada.")

def enviar_comando(comando):
    try:
        if portaUSB.is_open:
            portaUSB.write(str(comando).encode())
            print(f"Comando enviado: {comando}")
    except (NameError, AttributeError):
        print("Erro: Porta não conectada!")

def atualizar_velocidade(val):
    try:
        if portaUSB and portaUSB.is_open:
            comando = f"V{val}\n"
            portaUSB.write(comando.encode())
            print(f"Velocidade enviada: {val}")
    except Exception as e:
        print(f"Erro ao enviar velocidade: {e}")

def pressionar(comando):
    global botao_ativo
    botao_ativo = True
    def enviar():
        while botao_ativo:
            enviar_comando(comando)
            time.sleep(0.1)
    threading.Thread(target=enviar, daemon=True).start()

def soltar():
    global botao_ativo
    botao_ativo = False

def adicionar_passo():
    if portaUSB and portaUSB.is_open:
        try:
            portaUSB.reset_input_buffer()
            portaUSB.write(b'G\n')
            posicoes = portaUSB.readline().decode().strip()
            if posicoes and all(c.isdigit() or c == ',' for c in posicoes):
                passos_salvos.append(posicoes)
                atualizar_lista_passos()
                print(f"Posição adicionada: {posicoes}")
            else:
                print(f"Resposta inválida: {posicoes}")
        except Exception as e:
            print(f"Erro ao ler posição: {e}")

def excluir_passo():
    selecao = lista_passos.curselection()
    if selecao:
        idx = selecao[0]
        del passos_salvos[idx]
        atualizar_lista_passos()

def salvar_passos():
    if passos_salvos:
        nome_arquivo = simpledialog.askstring("Nome do Arquivo", "Digite o nome para salvar o arquivo de posições:")
        if nome_arquivo:
            caminho = os.path.join(pastaApp, f"{nome_arquivo}.txt")
            with open(caminho, "w") as file:
                for passo in passos_salvos:
                    file.write(passo + "\n")
            print(f"Arquivo {nome_arquivo}.txt salvo com sucesso!")
            messagebox.showinfo("Salvo", f"Arquivo {nome_arquivo}.txt salvo com sucesso!")

def rodar_sequencia(loop=True):
    global passos_salvos
    if not passos_salvos:
        print_debug("Nenhum passo salvo na lista.")
        return
    try:
        if portaUSB and portaUSB.is_open:
            sequencia = '|'.join(passos_salvos)
            comando = f"S{sequencia}\n"
            portaUSB.write(comando.encode())
            print_debug(f"Sequência enviada: {comando.strip()}")
            if not loop:
                threading.Thread(target=parar_depois, args=(len(passos_salvos) * 2,), daemon=True).start()
            atualizar_status("Rodando")
    except Exception as e:
        print_debug(f"Erro ao enviar sequência: {e}")

def rodar_sequencia_loop():
    if not arquivo_salvo:
        print("Nenhum arquivo de posições selecionado.")
        return
    try:
        if portaUSB.is_open:
            with open(arquivo_salvo, "r") as file:
                linhas = file.readlines()
                sequencia = '|'.join([linha.strip() for linha in linhas])
                portaUSB.write(f"S{sequencia}\n".encode())
                print("Sequência enviada para o Arduino!")
    except Exception as e:
        print(f"Erro ao enviar sequência: {e}")

def parar_depois(segundos):
    time.sleep(segundos)
    parar_sequencia()

def parar_sequencia():
    try:
        if portaUSB.is_open:
            portaUSB.write(b'P')
            print("Comando de parar enviado!")
            atualizar_status("Parado")
    except (NameError, AttributeError):
        print("Erro: Porta não conectada!")

def resetar_posicoes():
    try:
        if portaUSB.is_open:
            portaUSB.write(b'P')
            time.sleep(0.1)
            portaUSB.write(b'R')
            print("Comando de reset enviado!")
            atualizar_status("Resetando")
    except (NameError, AttributeError):
        print("Erro: Porta não conectada!")

def selecionar_arquivo():
    global arquivo_salvo
    arquivo_salvo = filedialog.askopenfilename(initialdir=pastaApp, title="Selecione um arquivo de posições", filetypes=[("Arquivos TXT", "*.txt")])
    if arquivo_salvo:
        print(f"Arquivo selecionado: {arquivo_salvo}")

def criar_frame_controle(master, titulo, comando_esq, comando_dir):
    frame = Frame(master, bg="#1f253d", bd=3, relief=RIDGE)
    Label(frame, text=titulo, font=('Helvetica', 11, 'bold'), bg="#1f253d", fg="white").pack(anchor=N, pady=5)

    btn_esq = Button(frame, image=icone_esquerda, relief=FLAT, bg="#2d334a")
    btn_esq.bind("<ButtonPress>", lambda e: pressionar(comando_esq))
    btn_esq.bind("<ButtonRelease>", lambda e: soltar())
    btn_esq.place(x=40, y=30, width=60, height=30)

    btn_dir = Button(frame, image=icone_direita, relief=FLAT, bg="#2d334a")
    btn_dir.bind("<ButtonPress>", lambda e: pressionar(comando_dir))
    btn_dir.bind("<ButtonRelease>", lambda e: soltar())
    btn_dir.place(x=200, y=30, width=60, height=30)

    Label(frame, text="Esquerda", bg="#1f253d", fg="white", font=('Helvetica', 9)).place(x=30, y=65)
    Label(frame, text="Direita", bg="#1f253d", fg="white", font=('Helvetica', 9)).place(x=200, y=65)
    return frame

def atualizar_posicoes_servos():
    if portaUSB and portaUSB.is_open:
        try:
            portaUSB.reset_input_buffer()
            portaUSB.write(b'G\n')
            posicoes = portaUSB.readline().decode().strip().split(',')
            if len(posicoes) == 4:
                for i, lbl in enumerate([servo1_lbl, servo2_lbl, servo3_lbl, servo4_lbl]):
                    lbl.config(text=posicoes[i])
        except:
            pass
    app.after(500, atualizar_posicoes_servos)

# --- Interface Principal ---

print_debug("Inicializando interface principal...")

app = Tk()
app.title("Garra Robótica")
app.geometry("1100x650")
app.configure(background="#111427")

foto_Robo = ImageTk.PhotoImage(file=os.path.join(pastaApp, "Modelo.jpg"))
icone_esquerda = ImageTk.PhotoImage(file=os.path.join(pastaApp, "esquerda_azul.png"))
icone_direita = ImageTk.PhotoImage(file=os.path.join(pastaApp, "direita_azul.png"))

Label(app, image=foto_Robo, bg="#111427").place(x=10, y=10, width=280, height=537)

status_label = Label(app, text="Status: Desconectado", font=('Helvetica', 10, 'bold'), background="#111427", foreground="white")
status_label.place(x=800, y=10)

print_debug("Adicionando controles de movimento...")
fr_movimento1 = criar_frame_controle(app, "Movimento 1", 1, 2)
fr_movimento1.place(x=300, y=50, width=300, height=100)

fr_movimento2 = criar_frame_controle(app, "Movimento 2", 3, 4)
fr_movimento2.place(x=300, y=160, width=300, height=100)

fr_movimento3 = criar_frame_controle(app, "Movimento 3", 5, 6)
fr_movimento3.place(x=300, y=270, width=300, height=100)

fr_garra = criar_frame_controle(app, "Garra", 7, 8)
fr_garra.place(x=300, y=380, width=300, height=100)

frame_lista = Frame(app, bg="#111427")
frame_lista.place(x=620, y=100, width=360, height=300)

scrollbar = Scrollbar(frame_lista)
scrollbar.pack(side=RIGHT, fill=Y)

lista_passos = Listbox(frame_lista, yscrollcommand=scrollbar.set, bg="#1f253d", fg="white", font=('Helvetica', 10), highlightbackground="#2d334a", selectbackground="#3b4252")
lista_passos.pack(fill=BOTH, expand=True)
scrollbar.config(command=lista_passos.yview)

fr_portas = Frame(app, bg="#111427")
fr_portas.place(x=625, y=5, width=170, height=90)

Label(fr_portas, text="Porta", font=('Helvetica', 11, 'bold'), bg="#111427", fg="white").pack(anchor=N)
cb_portas = ttk.Combobox(fr_portas, values=func.serial_ports(), state="readonly", postcommand=atualizar_portas)
cb_portas.pack(pady=5)
Button(fr_portas, text="Conectar", command=conectar_porta, bg="#2d334a", fg="white").pack(side=LEFT, padx=5)
Button(fr_portas, text="Desconectar", command=desconectar_porta, bg="#2d334a", fg="white").pack(side=LEFT, padx=5)

frame_posicoes = Frame(app, bg="#1f253d")
frame_posicoes.place(x=620, y=410, width=360, height=160)

Label(frame_posicoes, text="Posições Servos", font=('Helvetica', 12, 'bold'), bg="#1f253d", fg="white").pack(pady=5)
servo1_lbl = Label(frame_posicoes, text="", font=('Helvetica', 10), bg="#1f253d", fg="white")
servo1_lbl.pack()
servo2_lbl = Label(frame_posicoes, text="", font=('Helvetica', 10), bg="#1f253d", fg="white")
servo2_lbl.pack()
servo3_lbl = Label(frame_posicoes, text="", font=('Helvetica', 10), bg="#1f253d", fg="white")
servo3_lbl.pack()
servo4_lbl = Label(frame_posicoes, text="", font=('Helvetica', 10), bg="#1f253d", fg="white")
servo4_lbl.pack()

print_debug("Adicionando painel de botões de controle...")
fr_controles = Frame(app, bg="#1f253d", bd=3, relief=RIDGE)
fr_controles.place(x=300, y=580, width=680, height=50)

Button(fr_controles, text="Adicionar Passo", command=adicionar_passo, bg="#2d334a", fg="white").pack(side=LEFT, padx=5)
Button(fr_controles, text="Excluir Passo", command=excluir_passo, bg="#2d334a", fg="white").pack(side=LEFT, padx=5)
Button(fr_controles, text="Salvar", command=salvar_passos, bg="#2d334a", fg="white").pack(side=LEFT, padx=5)
Button(fr_controles, text="Rodar (Loop)", command=rodar_sequencia_loop, bg="#2d334a", fg="white").pack(side=LEFT, padx=5)
Button(fr_controles, text="Rodar 1x", command=lambda: rodar_sequencia(loop=False), bg="#2d334a", fg="white").pack(side=LEFT, padx=5)
Button(fr_controles, text="Parar", command=parar_sequencia, bg="#d32f2f", fg="white").pack(side=LEFT, padx=5)
Button(fr_controles, text="Reset", command=resetar_posicoes, bg="#2d334a", fg="white").pack(side=LEFT, padx=5)
Button(fr_controles, text="Selecionar Arquivo", command=selecionar_arquivo, bg="#2d334a", fg="white").pack(side=LEFT, padx=5)

Label(app, text="Velocidade", font=('Helvetica', 11, 'bold'), background="#111427", foreground="white").place(x=300, y=500)
velocidade_slider = Scale(app, from_=1, to=10, orient=HORIZONTAL, background="#1f253d", foreground="white", troughcolor="#2d334a", highlightthickness=0, command=lambda val: atualizar_velocidade(val))
velocidade_slider.set(5)
velocidade_slider.place(x=390, y=490)

print_debug("Interface carregada. Iniciando loop principal.")

atualizar_posicoes_servos()


app.mainloop()