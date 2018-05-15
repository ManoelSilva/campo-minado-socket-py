u""" CAMPO MINADO - Servidor UDP """
from socket import socket, AF_INET, SOCK_DGRAM
import random
import json
import re
import time
import os
from string import ascii_lowercase
import zmq

PORT = 5560
TAMANHO_DO_PAINEL = 9

if os.path.exists('jogada.json'):
    with open('jogada.json') as data_file:
        data = json.load(data_file)
        if data:
            MINAS = json.dumps(data['MINAS'])
            PAINEL_ATUAL = data['painel']
            PAINEL_CONFIGURADO = data['PAINEL_CONFIGURADO']
            BANDEIRAS = data['BANDEIRAS']
else:
    MINAS = None
    PAINEL_ATUAL = []
    PAINEL_CONFIGURADO = []
    BANDEIRAS = []

NUMERO_DE_MINAS = 10
MENSAGEM_DE_AJUDA = ("Digite a coluna seguida da linha (ex. d3) para sua jogada. "
                     "Para colocar ou remover uma bandeira, digite f logo após a celula desejada (exp. d3f).")
CONTINUAR_JOGO = "CONTINUA"
GAME_OVER = "GAME OVER"


def painel():
    global PAINEL_ATUAL
    PAINEL_ATUAL = [[' ' for i in range(TAMANHO_DO_PAINEL)]
                    for i in range(TAMANHO_DO_PAINEL)]
    painel = json.dumps(
        {"painel": PAINEL_ATUAL, "numeroDeMinas": NUMERO_DE_MINAS, "mensagem": MENSAGEM_DE_AJUDA})
    return painel


def getCelulaRandomica(painel):
    tamanhoPainel = len(painel)

    a = random.randint(0, tamanhoPainel - 1)
    b = random.randint(0, tamanhoPainel - 1)

    return (a, b)


def getVizinhos(painel, numeroLinha, numeroColuna):
    tamanhoPainel = len(painel)
    vizinhos = []

    for i in range(-1, 2):
        for j in range(-1, 2):
            if i == 0 and j == 0:
                continue
            elif -1 < (numeroLinha + i) < tamanhoPainel and -1 < (numeroColuna + j) < tamanhoPainel:
                vizinhos.append((numeroLinha + i, numeroColuna + j))

    return vizinhos


def getMinas(painel, inicio, numeroMinas):
    minas = []
    vizinhos = getVizinhos(painel, *inicio)

    for i in range(numeroMinas):
        celula = getCelulaRandomica(painel)
        while celula == inicio or celula in minas or celula in vizinhos:
            celula = getCelulaRandomica(painel)
        minas.append(celula)

    return minas


def getNumeros(painel):
    for numeroLinha, linha in enumerate(painel):
        for numeroColuna, celula in enumerate(linha):
            if celula != 'X':
                # Valores dos vizinhos
                valores = [painel[r][c] for r, c in getVizinhos(painel,
                                                                numeroLinha, numeroColuna)]

                # Conta quantas minas
                painel[numeroLinha][numeroColuna] = str(valores.count('X'))

    return painel


def getCelulas(linhaNumero, colunaNumero):
    global PAINEL_ATUAL, PAINEL_CONFIGURADO
    # Saida da funcao, celula ja exibida
    if PAINEL_ATUAL[linhaNumero][colunaNumero] != ' ':
        return

    # Mostra celula atual
    PAINEL_ATUAL[linhaNumero][colunaNumero] = PAINEL_CONFIGURADO[linhaNumero][colunaNumero]

    # Se a celular for vazia, pegar todos os vizinhos
    if PAINEL_CONFIGURADO[linhaNumero][colunaNumero] == "0":
        for r, c in getVizinhos(PAINEL_CONFIGURADO, linhaNumero, colunaNumero):
            # Repetir funcao para cada vizinho que nao possui bandeira
            if PAINEL_ATUAL[r][c] != 'F':
                getCelulas(r, c)


def configuraPainel(tamanhoPainel, celula, numeroMinas):
    global PAINEL_CONFIGURADO
    painelVazio = [['0' for i in range(tamanhoPainel)]
                   for i in range(tamanhoPainel)]

    minas = getMinas(painelVazio, celula, numeroMinas)

    for i, j in minas:
        painelVazio[i][j] = 'X'

    painel = getNumeros(painelVazio)

    PAINEL_CONFIGURADO = painel

    return (painel, minas)


def analisaInput(input):
    bandeira = False
    mensagem = "Indice de celula invalido! " + MENSAGEM_DE_AJUDA
    celula = None

    padrao = r'([a-{}])([0-9]+)(f?)'.format(ascii_lowercase[TAMANHO_DO_PAINEL - 1])
    inputValido = re.match(padrao, input)

    if input == "ajuda":
        mensagem = MENSAGEM_DE_AJUDA

    elif inputValido:
        linhaNumero = int(inputValido.group(2)) - 1
        colunaNumero = ascii_lowercase.index(inputValido.group(1))
        bandeira = bool(inputValido.group(3))

        if -1 < linhaNumero < TAMANHO_DO_PAINEL:
            celula = (linhaNumero, colunaNumero)
            mensagem = MENSAGEM_DE_AJUDA

    return {"celula": celula, "bandeira": bandeira, "mensagem": mensagem}


def realizaJogada(input):
    global PAINEL_CONFIGURADO, PAINEL_ATUAL, TAMANHO_DO_PAINEL, BANDEIRAS, NUMERO_DE_MINAS, MINAS
    resposta = []
    resultado = analisaInput(input)
    mensagem = resultado["mensagem"]
    celula = resultado["celula"]
    minasRestantes = NUMERO_DE_MINAS - len(BANDEIRAS)

    print(celula)
    if celula:
        numeroLinha, numeroColuna = celula

        celulaAtual = PAINEL_ATUAL[numeroLinha][numeroColuna]
        bandeira = resultado["bandeira"]

        if not PAINEL_CONFIGURADO:
            PAINEL_CONFIGURADO, MINAS = configuraPainel(
                TAMANHO_DO_PAINEL, celula, NUMERO_DE_MINAS)

        if bandeira:
            # Adiciona bandeira se a celula esta vazia
            if celulaAtual == ' ':
                PAINEL_ATUAL[numeroLinha][numeroColuna] = "F"
                BANDEIRAS.append(celula)
                mensagem = "Bandeira adicionada com sucesso. " + MENSAGEM_DE_AJUDA
            # Remove bandeira se ja existe uma
            elif celulaAtual == "F":
                PAINEL_ATUAL[numeroLinha][numeroColuna] = ' '
                BANDEIRAS.remove(celula)
                mensagem = "Bandeira removida com sucesso. " + MENSAGEM_DE_AJUDA
            else:
                mensagem = "Não se pode colocar uma bandeira na celula informada. " + MENSAGEM_DE_AJUDA

            resposta = {"painel": PAINEL_ATUAL,
                        "mensagem": mensagem, "acao": CONTINUAR_JOGO, "numeroDeMinas": minasRestantes}

        # Se a uma bandeira, exibir uma mensagem
        elif celula in BANDEIRAS:
            mensagem = "Ja existe uma bandeira na celula informada. " + MENSAGEM_DE_AJUDA

        elif PAINEL_CONFIGURADO[numeroLinha][numeroColuna] == 'X':
            mensagem = "Game Over!!!"
            resposta = {"painel": PAINEL_CONFIGURADO,
                        "mensagem": mensagem, "acao": GAME_OVER}
            if os.path.exists('jogada.json'):
                os.remove('jogada.json')

        elif celulaAtual == ' ':
            getCelulas(numeroLinha, numeroColuna)
            resposta = {"painel": PAINEL_ATUAL,
                        "mensagem": mensagem, "acao": CONTINUAR_JOGO,  "numeroDeMinas": minasRestantes}

        else:
            mensagem = "Esta celula ja foi selecionada"
            resposta = {"painel": PAINEL_ATUAL,
                        "mensagem": mensagem, "acao": CONTINUAR_JOGO,  "numeroDeMinas": minasRestantes}

        if set(BANDEIRAS) == set(MINAS):
            mensagem = "Parabens!!! Voce GANHOU!!!"
            resposta = {"painel": PAINEL_CONFIGURADO,
                        "mensagem": mensagem, "acao": GAME_OVER}
            if os.path.exists('jogada.json'):
                os.remove('jogada.json')

    else:
        resposta = {"painel": PAINEL_ATUAL,
                    "mensagem": mensagem, "acao": CONTINUAR_JOGO,  "numeroDeMinas": minasRestantes}

    if resposta["acao"] != GAME_OVER:
        resposta['MINAS'] = MINAS
        resposta['BANDEIRAS'] = BANDEIRAS
        resposta['PAINEL_CONFIGURADO'] = PAINEL_CONFIGURADO

        with open('jogada.json', 'w') as outfile:
            json.dump(resposta, outfile, sort_keys=True, indent=4)

    return resposta


u""" Implementação de um servidor que faz uso de um socket, com fila, UDP """


def server():
    context = zmq.Context()
    socketInstancia = context.socket(zmq.REP)
    socketInstancia.connect("tcp://localhost:%s" % PORT)

    while True:
        print("Servidor ativo..")
        data = socketInstancia.recv()

        requisicao = json.loads(data.decode())
        if requisicao.get('acao') == "PAINEL":
            if os.path.exists('jogada.json'):
                with open('jogada.json') as data_file:
                    data = json.load(data_file)
                    if data:
                        resposta = json.dumps(
                            {"painel": data["painel"], "numeroDeMinas": NUMERO_DE_MINAS, "mensagem": data["mensagem"]})
            else:
                resposta = painel()

        elif requisicao.get('acao') == "JOGAR":
            resposta = realizaJogada(requisicao.get('jogada').get('input'))
            resposta = json.dumps(resposta)

        print("Resposta ao tipo de requisicao: " + resposta)

        data = resposta.encode()
        socketInstancia.send(data)


if __name__ == "__main__":
    server()
