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

def salvaNovoArquivo(novoArquivo, nomeArquivo):
    if (type(novoArquivo).__module__ == np.__name__):
        [cprint(line, 'white') for line in novoArquivo]
    else:
        cprint(nomeArquivo+" não precisou ser atualizado.", 'magenta')


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
    
    
def processaBlocos(linhasArquivo, nomeArquivo, inicio = 0):
    novoArquivo = linhasArquivo
    indicesCodigo = [indice for indice, linha in enumerate(linhasArquivo, inicio) if linha.startswith('```')]
    
    for indice, valIndice in enumerate(indicesCodigo):
        if (not linhasArquivo[valIndice].rstrip().endswith('```') and valIndice > 0):
            busca = re.search('<!--(.*)-->', linhasArquivo[valIndice-1])
            if (busca and len(busca.groups()) == 1):
                linhasArquivoScript = carregaScript(busca.group(1).strip(), nomeArquivo)
                if (linhasArquivoScript and not np.array_equal(linhasArquivoScript, linhasArquivo[valIndice+1:indicesCodigo[indice+1]])):
                    if (type(novoArquivo).__module__ == np.__name__):
                        novoArquivo = np.array(novoArquivo)
                    novoArquivo = alteraBloco(novoArquivo, valIndice+1, indicesCodigo[indice+1], linhasArquivoScript)
                    return processaBlocos(novoArquivo, nomeArquivo, indicesCodigo[indice+1]+1)
            else:
                cprint(nomeArquivo + " - Configuração do script de importação inválido no bloco [" + str(valIndice-1) + " .. " + str(indicesCodigo[indice+1]) + "]", 'yellow')
        
    return novoArquivo


def processaArquivo(nomeArquivo):
    linhasArquivo = [line.rstrip('\n') for line in open(nomeArquivo, 'r', encoding='UTF-8')]
    if (linhasArquivo):
        if (list(filter(lambda linha: linha.startswith('```'), linhasArquivo))):
            #cprint(nomeArquivo + " - " + str(len(list(filter(lambda linha: linha.startswith('```'), linhasArquivo)))), 'red');
            novoArquivo = processaBlocos(linhasArquivo, nomeArquivo)
            salvaNovoArquivo(novoArquivo, nomeArquivo)
        else:
            cprint(nomeArquivo + " - Não possui marca de código para atualizar.", 'magenta')
    else:
        cprint(nomeArquivo + " está vazio.", 'yellow')
    

def listaArquivos(diretorio = "."):
    arquivos = os.listdir(diretorio)
    if (len(sys.argv) == 2):
        diretorio = sys.argv[1]
        if (os.path.isfile(diretorio)):
            arquivo = os.path.basename(diretorio)
            assert arquivo.endswith(".md"), os.path.dirname(diretorio)+" não é um Markdown."
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
    #num_cores = multiprocessing.cpu_count()
    #Parallel(n_jobs=num_cores)(delayed(processaArquivo)(nomeArquivo) for nomeArquivo in arquivos)
    
    #processamento normal para debug
    for nomeArquivo in arquivos:
        processaArquivo(nomeArquivo)
        
    #processamento com o script npx em NODE
    #arquivos_parametro = reduce(lambda arq1, arq2: arq1+" "+arq2, arquivos)
    #subprocess.call("npx embedme " + arquivos_parametro, shell=True)
    
except AssertionError as error:
    cprint(error, 'red')
