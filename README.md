# Fichário / Lista de Restrições — Atualização de Privacidade e Segurança

**Base correta utilizada:** `Listanegra-main(2).zip`, enviado em 26/10/2026. Este pacote é uma **atualização de código-fonte**; NÃO inclui banco de dados, fotos, planilhas com CPF, pastas `build`/`dist` ou executável `.exe` do arquivo original.

## Melhorias

- Central de **Configurações** por engrenagem discreta, aviso de privacidade, termos de uso e ciência de confidencialidade, versão e data do aceite.
- Acesso por **administrador / RH / cadastro / visualizador**, com permissões conferidas no servidor; o perfil visualizador vê CPF mascarado no painel e não acessa fichas completas ou fotos.
- Removida a criação de conta com senha padrão. **Contas anteriores exigem liberação por um administrador.** Novo administrador criado em terminal com senha escolhida (12+ caracteres).
- Chave de sessão gerada aleatoriamente e persistente na pasta `instance`, cookies `HttpOnly`/`SameSite`, inatividade de 45 minutos, proteção CSRF para operações POST e bloqueio temporário após tentativas inválidas.
- Operações como restringir, liberar, alterar status, excluir e limpar listas deixam de ser executadas por requisições GET. A interface converte links existentes em operações POST autenticadas com confirmação.
- Pesquisa sensível do colaborador passa a POST para não escrever CPF em parâmetro de URL. Uploads Excel deixam de salvar uma cópia desnecessária em `uploads`.
- Fotos novas são guardadas em `instance/fotos` com nomes aleatórios. Fotos antigas podem ser lidas pelo caminho privado `/foto-colaborador/<id>` e migradas da pasta pública com comando de manutenção.
- Exportação CSV passou ao servidor, com autorização, logs e prevenção básica de fórmulas maliciosas. Exportações Excel também ficam restritas aos perfis autorizados.
- Trilha de auditoria para consulta sensível, alteração, login, exportação, aceites e atos administrativos; não cria cópias extras dos dados pessoais dentro do log.
- Correção para **não vincular restrições a pessoas apenas por semelhança parcial de nome**; quando houver CPF, exigir igualdade do CPF. A liberação no fichário também retira a restrição correspondente na lista.
- O painel paginado, os filtros, a pré-admissão, a importação Excel e a lista de restrições da versão enviada foram mantidos.

## INSTALAÇÃO segura no Windows (leia antes de copiar)

1. **Feche o sistema** e mantenha uma cópia intacta da instalação atual. Para backup do banco, fotos e upload, copie **primeiro** somente o script `backup_antes_atualizar.py` para a pasta atual do sistema e rode `py backup_antes_atualizar.py`. O backup criado é confidencial e não criptografado; guarde em unidade protegida. Recomenda-se também copiar a pasta original inteira para outro disco e confirmar que consegue restaurar o banco.
2. Confirme que a instalação ativa realmente usa `instance/colaboradores.db`. Há também um banco em `dist/instance/colaboradores.db` na versão original, e o executável Windows pode usar locais diferentes. O `app.py` atualizado usa `sqlite:///colaboradores.db` do Flask, normalmente dentro de `instance`, salvo se `DATABASE_URL` tiver sido configurada.
3. Faça **teste em cópia da pasta original**, nunca diretamente no sistema usado no RH.
4. Copie para a pasta de teste o **conteúdo de código** deste pacote, como `app.py`, `models.py`, `security.py`, `templates/`, `static/security.js`, `requirements.txt` e scripts `.bat`. Não apague/substitua `instance/`, `uploads/`, `static/fotos/` nem nenhum `.db` da instalação antiga.
5. Execute `INICIAR_WINDOWS.bat` para criar o ambiente e instalar as dependências. Feche após iniciar uma vez e conferir a criação das tabelas novas.
6. Execute `CONFIGURAR_ADMIN_WINDOWS.bat`, informe o **nome de sua conta existente**, caso queira reaproveitá-la, e escolha uma **nova senha segura com no mínimo 12 caracteres**. Esse passo é indispensável: não existe senha padrão nesta versão.
7. Inicie novamente pelo `INICIAR_WINDOWS.bat`, acesse `http://127.0.0.1:5000`, registre a ciência do termo e abra a engrenagem. Preencha a razão social do controlador, contato de privacidade e responsável. Autorize individualmente as demais contas antigas.
8. Faça backup das fotos; com o terminal aberto, execute `\.venv\Scripts\python.exe -m flask --app app migrar-fotos`. O comando pergunta se você deseja **retirar originais públicos após conferência por hash**. Se preferir, mantenha originais temporariamente enquanto valida a cópia.
9. Teste login, fichas, filtros, fotos, importações, exportações, pré-admissão, restrições, liberação, exclusão autorizada, audit trail e permissões de cada perfil. Só depois publique para o RH.

> **Atenção:** o `.exe` que veio no ZIP original é uma versão antiga e **não foi reconstruído**. Se você inicia o fichário pelo `dist/app.exe`, os arquivos `.py` modificados não atualizam esse executável. A versão entregue deve ser executada com Python ou empacotada novamente por técnico, com testes dos caminhos do banco e das fotos.

### Instalação manual (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m flask --app app definir-admin
.\.venv\Scripts\python.exe app.py
```

### Publicação externa / Railway / servidor

- Configure `SECRET_KEY` como uma string aleatória longa persistente; não comite a chave, `.env`, banco ou fotos no Git.
- Configure `COOKIE_SECURE=1` quando HTTPS estiver funcionando.
- O banco SQLite e `instance/fotos` precisam de **armazenamento persistente**. No Railway, tenha um volume montado no caminho efetivamente usado pelo banco e faça testes de restauração. Não use disco efêmero para arquivos reais.
- Não coloque `/instance`, `/uploads`, backups ou `/static/fotos` como pastas públicas no proxy/CDN. O Flask já barra `/static/fotos`, mas outro servidor pode expor a pasta se estiver configurado incorretamente.
- Configuração de `HOST` padrão: `127.0.0.1` (acesso apenas local). Para permitir acesso na rede, revise firewall, proxy reverso, HTTPS e autenticação antes de alterar.
- Mantenha backup criptografado com restauração testada, proteja os acessos físicos e estabeleça procedimento interno de incidentes e retenção de documentos.

### LGPD — limites desta entrega

Os textos legais são **modelos operacionais**, não parecer jurídico nem certificação de conformidade. Precisam ser personalizados e revistos pela empresa/jurídico. O aceite de confidencialidade é de **usuários internos**, não substitui base legal para tratar dados dos colaboradores. A empresa precisa definir por que utiliza a lista de restrições, quem pode alterá-la, como revisa contestações e por quanto tempo mantém os registros. **Não foi implementada exclusão automática de documentos por prazo**: exigiria mapa de retenção legal aprovado.

### Testes feitos

Realizados: compilação dos arquivos Python; renderização de todos os templates Jinja com dados fictícios; análise sintática de JavaScript; verificação de referências e exclusão de dados pessoais do novo pacote. **Ainda não foi possível testar o aplicativo rodando com Flask nem o instalador no Windows**, pois o ambiente de preparação não disponibilizou o pacote Flask. O primeiro uso deve ocorrer numa cópia de teste da instalação.
