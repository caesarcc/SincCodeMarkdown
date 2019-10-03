import os
import sys
from functools import reduce
import re
import numpy as np
import multiprocessing
from joblib import Parallel, delayed
import PySimpleGUI as sg


def salva_arquivo_novo(arquivo, nome):
    if type(arquivo).__module__ == np.__name__:
        if "-atualizar" in sys.argv:
            sg.Popup(
                'Mandou atualizar o arquivo {} é sério?'.format(nome),
                title='Aviso!')
        with open(nome, "w+ ", encoding='UTF-8') as arquivo:
                arquivo.writelines([line + '\n' for line in arquivo])
        # else:
        #    [cprint(line, 'white') for line in arquivo]
    else:
        print(nome + " não precisou ser atualizado.")


def altera_bloco(arquivo, inicio, fim, script):
    novo_arquivo_atualizado = np.delete(arquivo, np.arange(inicio, fim))
    return np.insert(novo_arquivo_atualizado, inicio, script)


def compara_bloco(bloco_externo, bloco_markdown):
    if bloco_externo:
        npScript = np.array(bloco_externo, dtype=str)
        npArqMD = np.array(bloco_markdown, dtype=str)
        return (
            npScript.shape == npArqMD.shape and (npScript == npArqMD).all())
    return False


def carrega_script(nome_script, nome_do_arquivo):
    assert os.path.isfile(nome_script), "Script " + nome_script + " \
        marcado em " + nome_do_arquivo + " não existe."
    linhas_sem_quebra = [line.rstrip('\n') for line in open(
        nome_script, 'r', encoding='UTF-8')]
    return linhas_sem_quebra


def processa_script(
        linhas_do_arquivo, linhas_do_arquivoScript, linhaInicioMarca,
        linhaFimMarca):
    if not compara_bloco(
            linhas_do_arquivoScript,
            linhas_do_arquivo[linhaInicioMarca + 1:linhaFimMarca]):
        if type(linhas_do_arquivo).__module__ != np.__name__:
            linhas_do_arquivo = np.array(linhas_do_arquivo)
        return altera_bloco(
            linhas_do_arquivo, linhaInicioMarca + 1,
            linhaFimMarca, linhas_do_arquivoScript)
    return linhas_do_arquivo


def processa_blocos(linhas_do_arquivo, nome_do_arquivo, inicio=0):
    indices_do_codigo = [
        indice for indice, linha in enumerate(linhas_do_arquivo)
        if indice > inicio and linha.startswith('```')]

    if indices_do_codigo and len(indices_do_codigo) > 1:
        if not linhas_do_arquivo[indices_do_codigo[0]].rstrip().endswith('```'):
            busca = re.search(
                '<!--(.*)-->',
                linhas_do_arquivo[indices_do_codigo[0] - 1])
            if busca and len(busca.groups()) == 1 and busca.group(1).strip():
                arquivoScript = carrega_script(
                    busca.group(1).strip(),
                    nome_do_arquivo)
                qtd_linhas_adicionadas = len(arquivoScript) + 1
                linhas_do_arquivo = processa_script(
                    linhas_do_arquivo,
                    arquivoScript,
                    indices_do_codigo[0],
                    indices_do_codigo[1])
            else:
                qtd_linhas_adicionadas = indices_do_codigo[1] - 1
                sg.Popup(nome_do_arquivo + " - Configuração do script de \
                    importação inválido no bloco \
                    [" + str(indices_do_codigo[0] + 1) + " .. \
                    " + str(indices_do_codigo[1] + 1) + "]", title="Aviso!")
            return processa_blocos(
                linhas_do_arquivo,
                nome_do_arquivo,
                indices_do_codigo[0] + qtd_linhas_adicionadas)
        return linhas_do_arquivo


def processa_arquivo(nome_do_arquivo):
    linhas_do_arquivo = [
        line.rstrip('\n') for line in open(
            nome_do_arquivo,
            'r',
            encoding='UTF-8')
    ]
    if linhas_do_arquivo:
        if list(
            filter(lambda linha: linha.startswith('```'), linhas_do_arquivo)
        ):
            arquivo_novo = processa_blocos(linhas_do_arquivo, nome_do_arquivo)
            salva_arquivo_novo(arquivo_novo, nome_do_arquivo)
        else:
            sg.Popup(nome_do_arquivo + " - Não possui marca de código para \
                atualizar.", title='Aviso!')
    else:
        sg.Popup(nome_do_arquivo + " está vazio.", title='Aviso!')


def lista_arquivos(diretorio="."):
    arquivos = os.listdir(diretorio)
    if len(sys.argv) == 2:
        diretorio = sys.argv[1]
        if os.path.isfile(diretorio):
            arquivo = os.path.basename(diretorio)
            assert arquivo.endswith(".md"), os.path.dirname(diretorio) + " \
                não é um Markdown."
            os.chdir(os.path.dirname(diretorio))
            return [arquivo]
        assert os.path.isdir(diretorio), "Diretório ou arquivo \
            '{}' inválido.".format(diretorio)
        arquivos = os.listdir(diretorio)
        os.chdir(diretorio)

    assert arquivos, "Nenhum arquivo encontrado no \
        diretório '{}'.".format(diretorio)
    arquivos_md = list(
        filter(lambda arquivo: arquivo.endswith(".md"), arquivos)
    )
    assert arquivos_md, "Nenhum arquivo Markdown (*.md) encontrado no \
        diretório '{}'.".format(diretorio)
    return arquivos_md


if "__main__" == __name__:
    try:
        arquivos = lista_arquivos()

        # processamento paralelo (roda um arquivo por CPU disponível)
        num_cores = multiprocessing.cpu_count()
        Parallel(n_jobs=num_cores)(
            delayed(processa_arquivo)(nome_do_arquivo)
            for nome_do_arquivo in arquivos)

        # processamento normal para debug
        # for nome_do_arquivo in arquivos:
        #    processaArquivo(nome_do_arquivo)

    except AssertionError as error:
        sg.PopupError(error, title='Erro Fatal!')
