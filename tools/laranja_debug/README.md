# Laboratório Senhor Laranja — P-Slice Mobile

Este conjunto de arquivos foi criado para diagnosticar **um problema de mod**, nao para alterar automaticamente a engine.

## O que o GitHub realmente verifica
- Um workflow consegue validar codigo, arquivos de configuracao e builds **quando executado**.
- Ele **nao** recebe espontaneamente os logs nem os screenshots do P-Slice no seu Android.
- A camera que mostra o BF cortado deve ser medida no jogo ou em uma execucao grafica reproduzida.

## Como usar o diagnostico no celular
1. Faca backup de `.PSliceEngine/mods/VsSenhorLaranja_PSlice_Teste`.
2. Pegue o arquivo [laranja-debug.lua](laranja-debug.lua) desta pasta.
3. Coloque uma copia em:

   `.PSliceEngine/mods/VsSenhorLaranja_PSlice_Teste/data/reboot-teste/laranja-debug.lua`

   **Nao** substitua `script.lua`; este e um arquivo Lua adicional, de diagnostico.
4. Feche e reabra a P-Slice e inicie o **Reboot Teste**.
5. Tire dois prints: (a) quando a camera acompanha o Senhor Laranja e (b) quando acompanha o BF.
6. Em ambos os prints, mantenha visiveis os valores "BF y/h", "Camera scrollY" e "segueBF".

Se o texto nao aparecer, o port pode nao estar carregando scripts Lua adicionais da pasta de musica; nesse caso, envie o log e a lista de arquivos que estao na pasta `data/reboot-teste` em vez de alterar o codigo no escuro.

## Como interpretar os dados
- `BF y + altura` e a posicao vertical de referencia do sprite no mundo. Nao e equivalente a um pixel exato da tela.
- `scrollY` e `zoom` fazem o mesmo sprite aparecer em alturas diferentes conforme o cantor ativo.
- Se o BF so fica cortado quando `segueBF=false`, investigue **camera_opponent** e a distancia entre os personagens no stage.
- Se continua cortado quando `segueBF=true`, compare **camera_boyfriend** e o personagem `bf`, alem das dimensoes do sprite.
- O personagem do Story Mode usa `images/menucharacters/*.json`; seu campo `position` define o **offset** visual, nao um ponto absoluto.

## Validar arquivos locais
Se voce tiver os arquivos do mod em um computador:

```bash
python tools/laranja_debug/validate_mod.py /caminho/para/VsSenhorLaranja_PSlice_Teste
python -m unittest discover -s tools/laranja_debug/tests -v
```

## Antes de gerar APK
A workflow de build herdada do P-Slice utiliza caches e credenciais de assinatura. Sem configuracao especifica do fork, a build pode falhar por motivos que nao sao bugs no gameplay. Use primeiro o workflow **Laranja — Preflight (sem APK)**.

**Nenhuma correcao para a camera foi aplicada automaticamente ao codigo da engine.** O proximo passo e reproduzir o enquadramento com valores reais.
