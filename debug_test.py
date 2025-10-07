#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de debug para identificar problemas no texto processado.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from text_processing import formatar_texto_para_tts
import re

def debug_chapter_formatting():
    """Debuga especificamente o problema com os títulos de capítulo."""
    
    # Teste com o trecho específico que apresenta problemas
    test_text = """Capítulo 1 - Introdução
=======================

O Senhor e a Srª Dursley; da rua dos Alfeneiros, n.º quatro, se orgulhavam de dizer que eram perfeitamente normais, muito bem,. obrigadº Eram as últimas pessoas no mundo que se esperaria que se metessem em alguma coisa estranha ou misteriosa, porque simplesmente não compactuavam com esse tipo de bobagem.

O Senhor Dursley era Diretor de uma firma chamada Grunnings, fazia perfurações.

Era um homem alto e corpulento quase sem pescoço, embora tivesse enormes bigodes.

A Srª Dursley era e loura e tinha um pescoço quase duas vezes mais comprido que o normal o que era muito útil porque ela passava grande parte do tempo espichando-o por cima da cerca do jardim para espiar os vizinhos.

Os Dursley tinham um filhinho chamado Dudley; o Duda, e em sua opinião não havia garoto melhor em nenhum lugar do mundº Os Dursley tinham tudo que queriam, mas tinham também um segredo, e seu maior receio era que alguém o descobrisse.

Achavam que não iriam agüentar se alguém descobrisse a existência dos Potter.

A Srª Potter era irmã da Srª Dursley; mas não se viam muitos anos; na realidade a Srª Dursley fingia que não tinha irmã, porque esta e o marido imprestável eram o que havia de menos parecido possível com os Dursley;

Eles estremeciam só de pensar o que os vizinhos iriam dizer se os Potter. aparecessem na ruª Os Dursley sabiam que os Potter tinham um filhinho, também mas nunca o tinham vistº O 

garoto era mais uma razão para manter os Potter a distância; eles não queriam que Duda se misturasse com uma criança daquelas.

Quando o Senhor e a Srª Dursley acordaram na terça-feira dois 

monótona e cinzenta em que a nossa história começa não havia nada no céu nublado lá fora sugerindo as coisas estranhas e misteriosas que não tardariam. a acontecer por todo o pais.

O Senhor Dursley cantarolava ao escolher ª gravata mais sem graça do mundo para ir trabalhar e a Srª Dursley fofocava alegremente enquanto lutava para encaixar um Duda aos berros na cadeirinha altª 

Nenhum deles reparou em uma coruja parda que passou, batendo as asas, pela janelª"""

    print("Texto original:")
    print("-" * 50)
    print(repr(test_text))  # Mostra os caracteres especiais
    print("-" * 50)
    
    # Aplicar o pipeline de formatação para TTS
    formatted_text = formatar_texto_para_tts(test_text)
    
    print("\nTexto formatado:")
    print("-" * 50)
    print(repr(formatted_text))  # Mostra os caracteres especiais
    print("-" * 50)
    
    print("\nTexto formatado legível:")
    print("-" * 50)
    print(formatted_text)
    print("-" * 50)

if __name__ == "__main__":
    debug_chapter_formatting()