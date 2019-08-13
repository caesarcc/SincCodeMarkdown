import os
import sys
from functools import reduce
import re
from termcolor import colored, cprint
import colorama
import numpy as np
import multiprocessing
from joblib import Parallel, delayed

def salvaNovoArquivo(novoArquivo, nomeArquivo):
    if type(novoArquivo).__module__ == np.__name__:
        if "-atualizar" in sys.argv:
            cprint("Mandou atualizar o arquivo {} é sério?".format(nomeArquivo), 'yellow')
            with open(nomeArquivo,"w+", encoding='UTF-8') as arquivo:
                arquivo.writelines([line + '\n' for line in novoArquivo])
        else:
            [cprint(line, 'white') for line in novoArquivo]
    else:
        cprint(nomeArquivo+" não precisou ser atualizado.", 'magenta')


def alteraBloco(novoArquivo, range_inicio, range_fim, arquivoScript):
    novoArquivoAtualizado = np.delete(novoArquivo, np.arange(range_inicio, range_fim))
    return np.insert(novoArquivoAtualizado, range_inicio, arquivoScript)
    

def isLinhasIgual(linhasArquivoScript, linhasArquivoMD):
    if linhasArquivoScript:
        npScript = np.array(linhasArquivoScript, dtype = str)
        npArqMD = np.array(linhasArquivoMD, dtype = str)
        return (npScript.shape == npArqMD.shape and (npScript == npArqMD).all())
    return False
    

def carregaScript(nomeScript, nome_arquivo):
    assert os.path.isfile(nomeScript), "Script "+nomeScript+" marcado em "+nome_arquivo+" não existe."
    linhasSemQuebra = [line.rstrip('\n') for line in open(nomeScript, 'r', encoding='UTF-8')]
    return linhasSemQuebra


def processaScript(linhasArquivo, linhasArquivoScript, linhaInicioMarca, linhaFimMarca):
    if not isLinhasIgual(linhasArquivoScript, linhasArquivo[linhaInicioMarca+1:linhaFimMarca]):
        if type(linhasArquivo).__module__ != np.__name__:
            linhasArquivo = np.array(linhasArquivo)
        return alteraBloco(linhasArquivo, linhaInicioMarca+1, linhaFimMarca, linhasArquivoScript)
    return linhasArquivo
    
    
def processaBlocos(linhasArquivo, nomeArquivo, inicio = 0):
    indicesCodigo = [indice for indice, linha in enumerate(linhasArquivo) if indice > inicio and linha.startswith('```')]
    
    if indicesCodigo and len(indicesCodigo) > 1 and not linhasArquivo[indicesCodigo[0]].rstrip().endswith('```'):
        busca = re.search('<!--(.*)-->', linhasArquivo[indicesCodigo[0]-1])
        if busca and len(busca.groups()) == 1 and busca.group(1).strip():
            arquivoScript = carregaScript(busca.group(1).strip(), nomeArquivo)
            qtdLinhaAdicionadas = len(arquivoScript)+1
            linhasArquivo = processaScript(linhasArquivo, arquivoScript, indicesCodigo[0], indicesCodigo[1])
        else:
            qtdLinhaAdicionadas = indicesCodigo[1]-1
            cprint(nomeArquivo + " - Configuração do script de importação inválido no bloco [" + str(indicesCodigo[0]+1) + " .. " + str(indicesCodigo[1]+1) + "]", 'yellow')
        
        return processaBlocos(linhasArquivo, nomeArquivo, indicesCodigo[0]+qtdLinhaAdicionadas)
    return linhasArquivo

def processaArquivo(nomeArquivo):
    linhasArquivo = [line.rstrip('\n') for line in open(nomeArquivo, 'r', encoding='UTF-8')]
    if linhasArquivo:
        if list(filter(lambda linha: linha.startswith('```'), linhasArquivo)):
            novoArquivo = processaBlocos(linhasArquivo, nomeArquivo)
            salvaNovoArquivo(novoArquivo, nomeArquivo)
        else:
            cprint(nomeArquivo + " - Não possui marca de código para atualizar.", 'magenta')
    else:
        cprint(nomeArquivo + " está vazio.", 'yellow')
    

def listaArquivos(diretorio = "."):
    arquivos = os.listdir(diretorio)
    if len(sys.argv) == 2:
        diretorio = sys.argv[1]
        if os.path.isfile(diretorio):
            arquivo = os.path.basename(diretorio)
            assert arquivo.endswith(".md"), os.path.dirname(diretorio)+" não é um Markdown."
            os.chdir(os.path.dirname(diretorio))
            return [arquivo]
        assert os.path.isdir(diretorio), "Diretório ou arquivo '{}' inválido.".format(diretorio)
        arquivos = os.listdir(diretorio)
        os.chdir(diretorio)
    
    assert arquivos, "Nenhum arquivo encontrado no diretório '{}'.".format(diretorio)
    arquivos_md = list(filter(lambda arquivo: arquivo.endswith(".md"), arquivos))
    assert arquivos_md, "Nenhum arquivo Markdown (*.md) encontrado no diretório '{}'.".format(diretorio)
    return arquivos_md

if "__main__" == __name__:
    try:
        colorama.init()
        arquivos = listaArquivos()
        
        #processamento paralelo (roda um arquivo por CPU disponível)
        num_cores = multiprocessing.cpu_count()
        Parallel(n_jobs=num_cores)(delayed(processaArquivo)(nomeArquivo) for nomeArquivo in arquivos)
        
        #processamento normal para debug
        #for nomeArquivo in arquivos:
        #    processaArquivo(nomeArquivo)
        
    except AssertionError as error:
        cprint(error, 'red')