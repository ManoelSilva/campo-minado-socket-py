u""" CAMPO MINADO - Cliente UDP """
from string import ascii_lowercase
from socket import socket, AF_INET, SOCK_DGRAM
import os
import json
import zmq

PORT = 5559

ENCODE = "UF-8"

MOSTRAR_PAINEL = "PAINEL"
JOGADA = "JOGAR"

u""" Função de envio de dados para o servidor """


def cliente():
    context = zmq.Context()
    requisicao = json.dumps({"acao": MOSTRAR_PAINEL})

    socketInstancia = context.socket(zmq.REQ)
    socketInstancia.connect("tcp://localhost:%s" % PORT)

    socketInstancia.send(requisicao.encode())
    data = socketInstancia.recv()

    resposta = data.decode()
    resposta = json.loads(resposta)

    os.system('cls')
    showPainel(resposta.get("painel"))

    gameOn = True

    while gameOn:
        usuarioInput = input(resposta.get("mensagem") +
                             " ({} minas restantes): ".format(resposta.get("numeroDeMinas")))

        requisicao = json.dumps(
            {"acao": JOGADA, "jogada": {'input': usuarioInput}})
        socketInstancia.send(requisicao.encode())
        data = socketInstancia.recv()
        
        resposta = data.decode()
        resposta = json.loads(resposta)

        if resposta.get('acao') == "CONTINUA":
            os.system('cls')
            showPainel(resposta.get("painel"))
        elif resposta.get('acao') == "GAME OVER":
            os.system('cls')
            showPainel(resposta.get("painel"))
            print(resposta.get("mensagem"))
            gameOn = False


def showPainel(painel):
    painelTamanho = len(painel)

    textoHorizontal = '   ' + (4 * painelTamanho * '-') + '-'

    # Imprimir cabecalhos do topo
    cabecalhos = '     '

    for i in ascii_lowercase[:painelTamanho]:
        cabecalhos = cabecalhos + i + '   '

    print(cabecalhos + '\n' + textoHorizontal)

    # Imprimir numeros a esquerda
    for idx, i in enumerate(painel):
        linha = '{0:2} |'.format(idx + 1)

        for j in i:
            linha = linha + ' ' + j + ' |'

        print(linha + '\n' + textoHorizontal)

    print('')


if __name__ == '__main__':
    cliente()
