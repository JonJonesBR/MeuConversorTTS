#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste simples para verificar se pydub está funcionando corretamente.
"""

def test_pydub():
    try:
        from pydub import AudioSegment
        print("pydub importado com sucesso!")
        
        # Testar a funcionalidade básica
        silence = AudioSegment.silent(duration=100)  # 10ms de silêncio
        print("Funcionalidade de áudio funcionando!")
        
        # Testar exportação para MP3
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            silence.export(tmp_path, format="mp3")
            print(f"Exportação MP3 funcionando! Arquivo: {tmp_path}")
            
            # Limpar arquivo temporário
            os.unlink(tmp_path)
            print("Arquivo temporário removido.")
            
            return True
        except Exception as e:
            print(f"Erro ao exportar MP3: {e}")
            return False
            
    except ImportError as e:
        print(f"Erro ao importar pydub: {e}")
        return False
    except Exception as e:
        print(f"Erro geral: {e}")
        return False

if __name__ == "__main__":
    print("Teste de funcionalidade do pydub")
    print("=" * 40)
    
    sucesso = test_pydub()
    
    print("=" * 40)
    if sucesso:
        print("pydub esta funcionando corretamente!")
    else:
        print("pydub nao esta funcionando corretamente.")