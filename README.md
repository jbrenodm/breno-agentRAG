**Sistema de Análise Automatizada de Requisitos RAG (Retrivial Aumented Generation)**

**Objetivo:**  
Sistema automatizado que processe arquivos (.xls, .csv ou .txt) contendo requisitos estruturados linha a linha, com possíveis hierarquias (cabeçalhos e subitens), e retorne um arquivo padronizado com as respostas associadas a cada item.

**Funcionamento:**  

1. **Entrada de Dados:**  
   - Aceitar arquivos nos formatos: `.xls`, `.csv`, `.txt`.  
   - Estrutura do arquivo de entrada:  
     - Cada linha representa um requisito, cabeçalho ou subitem.  
     - Hierarquia opcional (ex.: cabeçalho principal > sublinha > subitem).  

2. **Processamento:**  
   - Leitura **linha por linha** (loop), identificando:  
     - Pergunta/requisito (texto da linha).  
     - Tipo (cabeçalho, subitem, item principal).  
   - Para cada linha, o sistema deve:  
     - Buscar a resposta correspondente usando o modelo de busca RAG.
     - Registrar no arquivo de saída:  
       - **Pergunta** (texto original).  
       - **Resposta** (encontrada).  
       - **Fonte** (origem da resposta, ex.: nome do documento).  
       - **Trecho** (texto específico onde a resposta foi localizada).  
       - **Página** (número da página, se aplicável).  

3. **Saída de Dados:**  
   - Gerar arquivo de retorno (.xls ou .csv) com a estrutura:  
     ```
     Pergunta; Resposta; Fonte; Trecho; Página  
     ```  
   - Manter a hierarquia original e AS LINHAS NA MESMA ORDEM DO DOCUMENTO FONTE. (cabeçalhos e subitens alinhados).  

**Exemplo de Arquivo de Saída:**  
| Pergunta               | Resposta           | Fonte          | Trecho                                     | Página |  
|------------------------|--------------------|----------------|--------------------------------------------|--------|  
| "Requisito 1.1"        | "Atendido"         | "Doc_X.pdf"    | "O sistema deve... (Seção 3.2)"           | 12     |  
| "Subitem 1.1.1"        | "Pendente"         | "API_Y"        | "Campo 'X' não encontrado..."             | N/A    |  

**Requisitos Técnicos:**  
- Compatibilidade com encoding UTF-8 (para caracteres especiais).  
- Tratamento de erros para linhas mal formatadas.  
- Opção de saída em `.xls` (com formatação) ou `.csv` (delimitado por vírgula ou ponto-e-vírgula).  

---




Proximo passo:
[PRONTO] Criar um arquivo onde vai pegar os requisitos de uma planilha .xls ou .csv ou .txt
[PRONTO] Estes requisitos deste documento serão passados linha por linha (via loop) para o arquivo "query_data.py" onde cada resposta recebida de cada linha, sera salva em [PRONTO]um arquivo ao lado de sua pergunta, tambem com sua fonte e pagina. A estrutura do arquivo deve ser: Pergunta; Resposta; Fonte; Página.
[PRONTO]O arquivo deverá ser salvo no formato em .csv ou .xls
[] No momento o arquivo gerado está vindo com as linhas fora de ordem. Preciso ordenar conforme a ordem do arquivo de entrada.
[] Fazer o tratamento de lista com sublista 
