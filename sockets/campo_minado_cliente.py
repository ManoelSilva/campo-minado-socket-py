u""" CAMPO MINADO - Cliente UDP """
from string import ascii_lowercase
from socket import socket, AF_INET, SOCK_DGRAM
import os
import json

ENCODE = "UTF-8"
MAX_BYTES = 65535
PORT = 5000
HOST = '127.0.0.1'

MOSTRAR_PAINEL = "PAINEL"
JOGADA = "JOGAR"

u""" Função de envio de dados para o servidor """


def cliente():
    destino = (HOST, PORT)
    requisicao = json.dumps({"acao": MOSTRAR_PAINEL})

    socketInstancia = socket(AF_INET, SOCK_DGRAM)
    socketInstancia.sendto(requisicao.encode(), destino)
    data, address = socketInstancia.recvfrom(MAX_BYTES)

    resposta = data.decode()
    resposta = json.loads(resposta)

    os.system('cls')
    showPainel(resposta.get("painel"))

    socketInstancia.close()

    gameOn = True

    while gameOn:
        usuarioInput = input(resposta.get("mensagem") +
                             " ({} minas restantes): ".format(resposta.get("numeroDeMinas")))

        socketInstancia = socket(AF_INET, SOCK_DGRAM)
        requisicao = json.dumps(
            {"acao": JOGADA, "jogada": {'input': usuarioInput}})
        socketInstancia.sendto(requisicao.encode(), destino)
        data, address = socketInstancia.recvfrom(MAX_BYTES)
        
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

        socketInstancia.close()


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
