import rpyc
from string import ascii_lowercase
from socket import socket, AF_INET, SOCK_DGRAM
import os
import json

class CampoMinadoClient:
    ENCODE = "UTF-8"
    JOGADA = "JOGAR"
    MOSTRAR_PAINEL = "PAINEL"

    def __init__(self):
        self.config = {'allow_public_attrs': True}
        self.proxy = rpyc.connect('localhost', 18861, config=self.config)
        self.conn = self.proxy.root.CampoMinadoServGame()

    def cliente(self):
        requisicao = json.dumps({"acao": self.MOSTRAR_PAINEL})
        resposta = self.conn.painel()
        resposta = json.loads(resposta)

        os.system('cls')
        self.showPainel(resposta.get("painel"))

        gameOn = True

        while gameOn:
            usuarioInput = input(resposta.get("mensagem") +
                                " ({} minas restantes): ".format(resposta.get("numeroDeMinas")))

            requisicao = json.dumps(
                {"acao": self.JOGADA, "jogada": {'input': usuarioInput}})
            
            resposta = self.conn.realizaJogada(requisicao)
            resposta = json.loads(resposta)

            if resposta.get('acao') == "CONTINUA":
                os.system('cls')
                self.showPainel(resposta.get("painel"))
            elif resposta.get('acao') == "GAME OVER":
                os.system('cls')
                self.showPainel(resposta.get("painel"))
                print(resposta.get("mensagem"))
                gameOn = False


    def showPainel(self, painel):
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
    novo_jogo = CampoMinadoClient()
    novo_jogo.cliente()
