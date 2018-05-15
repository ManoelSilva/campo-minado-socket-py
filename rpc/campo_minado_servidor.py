import rpyc
from rpyc.utils.server import ThreadedServer

import sys
import random
import json
import re
import time
import os
import json
from string import ascii_lowercase


class CampoMinadoServer(rpyc.Service):
    class exposed_CampoMinadoServGame(object):
        NUMERO_DE_MINAS = 10
        MENSAGEM_DE_AJUDA = ("Digite a coluna seguida da linha (ex. d3) para sua jogada. "
                             "Para colocar ou remover uma bandeira, digite f logo após a celula desejada (exp. d3f).")
        CONTINUAR_JOGO = "CONTINUA"
        GAME_OVER = "GAME OVER"
        PAINEL_CONFIGURADO = None
        PAINEL_ATUAL = None
        TAMANHO_DO_PAINEL = 9
        BANDEIRAS = None
        PAINEL_ATUAL = None
        MINAS = None

        def __init__(self):
            if os.path.exists('jogada.json'):
                with open('jogada.json') as data_file:
                    data = json.load(data_file)
                    if data:
                        self.MINAS = json.dumps(data['MINAS'])
                        self.NUMERO_DE_MINAS = int(json.dumps(data['numeroDeMinas']))
                        self.PAINEL_ATUAL = data['painel']
                        self.PAINEL_CONFIGURADO = data['PAINEL_CONFIGURADO']
                        self.BANDEIRAS = data['BANDEIRAS']
            else:
                self.MINAS = None
                self.PAINEL_ATUAL = []
                self.PAINEL_CONFIGURADO = []
                self.BANDEIRAS = []
                self.PAINEL_ATUAL = [[' ' for i in range(self.TAMANHO_DO_PAINEL)]
                                     for i in range(self.TAMANHO_DO_PAINEL)]

        def exposed_painel(self):
            painel = json.dumps(
                {"painel": self.PAINEL_ATUAL, "numeroDeMinas": self.NUMERO_DE_MINAS, "mensagem": self.MENSAGEM_DE_AJUDA})

            if os.path.exists('jogada.json'):
                with open('jogada.json') as data_file:
                    data = json.load(data_file)
                    if data:
                        painel = json.dumps(
                            {"painel": data["painel"], "numeroDeMinas": self.NUMERO_DE_MINAS, "mensagem": data["mensagem"]})

            return painel

        def getCelulaRandomica(self, painel):
            tamanhoPainel = len(painel)

            a = random.randint(0, tamanhoPainel - 1)
            b = random.randint(0, tamanhoPainel - 1)

            return (a, b)

        def getVizinhos(self, painel, numeroLinha, numeroColuna):
            tamanhoPainel = len(painel)
            vizinhos = []

            for i in range(-1, 2):
                for j in range(-1, 2):
                    if i == 0 and j == 0:
                        continue
                    elif -1 < (numeroLinha + i) < tamanhoPainel and -1 < (numeroColuna + j) < tamanhoPainel:
                        vizinhos.append((numeroLinha + i, numeroColuna + j))

            return vizinhos

        def getMinas(self, painel, inicio, numeroMinas):
            minas = []
            vizinhos = self.getVizinhos(painel, *inicio)

            for i in range(numeroMinas):
                celula = self.getCelulaRandomica(painel)
                while celula == inicio or celula in minas or celula in vizinhos:
                    celula = self.getCelulaRandomica(painel)
                minas.append(celula)

            return minas

        def getNumeros(self, painel):
            for numeroLinha, linha in enumerate(painel):
                for numeroColuna, celula in enumerate(linha):
                    if celula != 'X':
                        # Valores dos vizinhos
                        valores = [painel[r][c] for r, c in self.getVizinhos(painel,
                                                                        numeroLinha, numeroColuna)]

                        # Conta quantas minas
                        painel[numeroLinha][numeroColuna] = str(
                            valores.count('X'))

            return painel

        def getCelulas(self, linhaNumero, colunaNumero):
            # Saida da funcao, celula ja exibida
            if self.PAINEL_ATUAL[linhaNumero][colunaNumero] != ' ':
                return

            # Mostra celula atual
            self.PAINEL_ATUAL[linhaNumero][colunaNumero] = self.PAINEL_CONFIGURADO[linhaNumero][colunaNumero]

            # Se a celular for vazia, pegar todos os vizinhos
            if self.PAINEL_CONFIGURADO[linhaNumero][colunaNumero] == "0":
                for r, c in self.getVizinhos(self.PAINEL_CONFIGURADO, linhaNumero, colunaNumero):
                    # Repetir funcao para cada vizinho que nao possui bandeira
                    if self.PAINEL_ATUAL[r][c] != 'F':
                        self.getCelulas(r, c)

        def configuraPainel(self, tamanhoPainel, celula, numeroMinas):
            painelVazio = [['0' for i in range(tamanhoPainel)]
                           for i in range(tamanhoPainel)]

            minas = self.getMinas(painelVazio, celula, numeroMinas)

            for i, j in minas:
                painelVazio[i][j] = 'X'

            painel = self.getNumeros(painelVazio)

            self.PAINEL_CONFIGURADO = painel

            return (painel, minas)

        def analisaInput(self, input):
            bandeira = False
            mensagem = "Indice de celula invalido! " + self.MENSAGEM_DE_AJUDA
            celula = None

            padrao = r'([a-{}])([0-9]+)(f?)'.format(
                ascii_lowercase[self.TAMANHO_DO_PAINEL - 1])
            inputValido = re.match(padrao, input)

            if input == "ajuda":
                mensagem = self.MENSAGEM_DE_AJUDA

            elif inputValido:
                linhaNumero = int(inputValido.group(2)) - 1
                colunaNumero = ascii_lowercase.index(inputValido.group(1))
                bandeira = bool(inputValido.group(3))

                if -1 < linhaNumero < self.TAMANHO_DO_PAINEL:
                    celula = (linhaNumero, colunaNumero)
                    mensagem = self.MENSAGEM_DE_AJUDA

            return {"celula": celula, "bandeira": bandeira, "mensagem": mensagem}

        def exposed_realizaJogada(self, input):
            print(json.loads(input))
            resposta = []
            resultado = self.analisaInput(json.loads(input)['jogada']['input'])

            mensagem = resultado["mensagem"]
            celula = resultado["celula"]
            minasRestantes = self.NUMERO_DE_MINAS - len(self.BANDEIRAS)

            if celula:
                numeroLinha, numeroColuna = celula

                celulaAtual = self.PAINEL_ATUAL[numeroLinha][numeroColuna]
                bandeira = resultado["bandeira"]

                if not self.PAINEL_CONFIGURADO:
                    self.PAINEL_CONFIGURADO, self.MINAS = self.configuraPainel(
                        self.TAMANHO_DO_PAINEL, celula, self.NUMERO_DE_MINAS)

                if bandeira:
                    # Adiciona bandeira se a celula esta vazia
                    if celulaAtual == ' ':
                        self.PAINEL_ATUAL[numeroLinha][numeroColuna] = "F"
                        self.BANDEIRAS.append(celula)
                        mensagem = "Bandeira adicionada com sucesso. " + self.MENSAGEM_DE_AJUDA
                    # Remove bandeira se ja existe uma
                    elif celulaAtual == "F":
                        self.PAINEL_ATUAL[numeroLinha][numeroColuna] = ' '
                        self.BANDEIRAS.remove(celula)
                        mensagem = "Bandeira removida com sucesso. " + self.MENSAGEM_DE_AJUDA
                    else:
                        mensagem = "Não se pode colocar uma bandeira na celula informada. " + \
                            self.MENSAGEM_DE_AJUDA

                    resposta = {"painel": self.PAINEL_ATUAL,
                                "mensagem": mensagem, "acao": self.CONTINUAR_JOGO, "numeroDeMinas": minasRestantes}

                # Se ha uma bandeira, exibir uma mensagem
                elif celula in self.BANDEIRAS:
                    mensagem = "Ja existe uma bandeira na celula informada. " + self.MENSAGEM_DE_AJUDA

                elif self.PAINEL_CONFIGURADO[numeroLinha][numeroColuna] == 'X':
                    mensagem = "Game Over!!!"
                    resposta = {"painel": self.PAINEL_CONFIGURADO,
                                "mensagem": mensagem, "acao": self.GAME_OVER}
                    if os.path.exists('jogada.json'):
                        os.remove('jogada.json')

                elif celulaAtual == ' ':
                    self.getCelulas(numeroLinha, numeroColuna)
                    resposta = {"painel": self.PAINEL_ATUAL,
                                "mensagem": mensagem, "acao": self.CONTINUAR_JOGO,  "numeroDeMinas": minasRestantes}

                else:
                    mensagem = "Esta celula ja foi selecionada"
                    resposta = {"painel": self.PAINEL_ATUAL,
                                "mensagem": mensagem, "acao": self.CONTINUAR_JOGO,  "numeroDeMinas": minasRestantes}

                if set(self.BANDEIRAS) == set(self.MINAS):
                    mensagem = "Parabens!!! Voce GANHOU!!!"
                    resposta = {"painel": self.PAINEL_CONFIGURADO,
                                "mensagem": mensagem, "acao": self.GAME_OVER}
                    if os.path.exists('jogada.json'):
                        os.remove('jogada.json')

            else:
                resposta = {"painel": self.PAINEL_ATUAL,
                            "mensagem": mensagem, "acao": self.CONTINUAR_JOGO,  "numeroDeMinas": minasRestantes}

            if resposta["acao"] != self.GAME_OVER:
                resposta['MINAS'] = self.MINAS
                resposta['BANDEIRAS'] = self.BANDEIRAS
                resposta['PAINEL_CONFIGURADO'] = self.PAINEL_CONFIGURADO

                with open('jogada.json', 'w') as outfile:
                    json.dump(resposta, outfile, sort_keys=False, indent=1)

            return json.dumps(resposta)


if __name__ == "__main__":
    try:
        thread = ThreadedServer(CampoMinadoServer, port=18861)
        print("Thread start, press ctrl + c to interrupt..")
        thread.start()
    except:
        for val in sys.exc_info():
            print(val)
