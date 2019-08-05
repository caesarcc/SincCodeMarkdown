import os
import sys
from functools import reduce
import re
from termcolor import colored, cprint
import colorama
import numpy as np
import subprocess
import multiprocessing
from joblib import Parallel, delayed

def salvaNovoArquivo(novoArquivo, nome_arquivo):
    if (type(novoArquivo).__module__ == np.__name__):
        [cprint(line, 'white') for line in novoArquivo]
    else:
        cprint("Arquivo "+nome_arquivo+" não possui precisou ser atualizado.", 'magenta')


def alteraBloco(novoArquivo, range_inicio, range_fim, arquivoScript):
    novoArquivoAtualizado = np.delete(novoArquivo, np.arange(range_inicio, range_fim))
    return np.insert(novoArquivoAtualizado, range_inicio, arquivoScript)
    

def isLinhasIgual(linhasArquivoScript, linhasArquivoMD):
    if (linhasArquivoScript):
        npScript = np.array(linhasArquivoScript, dtype = str)
        npArqMD = np.array(linhasArquivoMD, dtype = str)
        return (npScript.shape == npArqMD.shape and (npScript == npArqMD).all())


def carregaScript(nomeScript, nome_arquivo):
    if (os.path.isfile(nomeScript)):
        linhasSemQuebra = [line.rstrip('\n') for line in open(nomeScript, 'r', encoding='UTF-8')]
        return linhasSemQuebra
    else:
        cprint("Script "+nomeScript+" marcado em "+nome_arquivo+" não existe.", 'yellow')
        return None
    
    
def processaBlocos(indicesComentarios, linhasArquivo, nome_arquivo):
    houveAlteracao = False
    novoArquivo = np.array(linhasArquivo)
    for indice, valIndice in enumerate(indicesComentarios):
        if (not linhasArquivo[valIndice].rstrip().endswith('```') and valIndice > 0):
            busca = re.search('<!--(.*)-->', linhasArquivo[valIndice-1])
            if (len(busca.groups()) == 1):
                linhasArquivoScript = carregaScript(busca.group(1).strip(), nome_arquivo)
                if (linhasArquivoScript and not np.array_equal(linhasArquivoScript, linhasArquivo[valIndice+1:indicesComentarios[indice+1]])):
                    houveAlteracao = True
                    novoArquivo = alteraBloco(novoArquivo, valIndice+1, indicesComentarios[indice+1], linhasArquivoScript)
            else:
                cprint("Configuração do script de importação inválida em " + linhasArquivo[indice-1], 'yellow')
    return houveAlteracao and novoArquivo


def processaArquivo(nome_arquivo):
    linhasArquivo = [line.rstrip('\n') for line in open(nome_arquivo, 'r', encoding='UTF-8')]
    if (linhasArquivo):
        indicesComentarios = [indice for indice, linha in enumerate(linhasArquivo) if linha.startswith('```')]
        if (indicesComentarios):
            #cprint(nome_arquivo + " linhas de comentário: " + reduce(lambda s1, s2: str(s1) + ", " + str(s2), indicesComentarios), 'white')
            novoArquivo = processaBlocos(indicesComentarios, linhasArquivo, nome_arquivo)
            salvaNovoArquivo(novoArquivo, nome_arquivo)
        else:
            cprint("Arquivo "+nome_arquivo+" não possui marca de código para atualizar.", 'magenta')
    else:
        cprint("Arquivo "+nome_arquivo+" está vazio.", 'yellow')
    

def listaArquivos(diretorio = "."):
    arquivos = os.listdir(diretorio)
    if (len(sys.argv) == 2):
        diretorio = sys.argv[1]
        if (os.path.isfile(diretorio)):
            arquivo = os.path.basename(diretorio)
            assert arquivo.endswith(".md"), "Arquivo '"+os.path.dirname(diretorio)+"' não é um Markdown."
            os.chdir(os.path.dirname(diretorio))
            return [arquivo]
        assert os.path.isdir(diretorio), "Diretório ou arquivo '"+diretorio+"' inválido."
        arquivos = os.listdir(diretorio)
        os.chdir(diretorio)
    
    assert arquivos, "Nenhum arquivo encontrado no diretório '"+diretorio+"'."
    arquivos_md = list(filter(lambda arquivo: arquivo.endswith(".md"), arquivos))
    assert arquivos_md, "Nenhum arquivo Markdown (*.md) encontrado no diretório '"+diretorio+"'."
    return arquivos_md


try:
    colorama.init()
    arquivos = listaArquivos()
    
    #processamento paralelo (roda um arquivo por CPU disponível)
    num_cores = multiprocessing.cpu_count()
    Parallel(n_jobs=num_cores)(delayed(processaArquivo)(nome_arquivo) for nome_arquivo in arquivos)
    
except AssertionError as error:
    cprint(error, 'red')