Assuma o papel do Verifier: leia loop/PROMPT_VERIFY.md e execute a auditoria
completa descrita nele, respondendo no formato de saída obrigatório
(VEREDITO / EVIDÊNCIAS / OBSERVAÇÕES / AÇÕES / CLASSIFICAÇÃO).

Ponto fixo (ref base opcional): $ARGUMENTS
Obtenha o diff com `python3 loop/diff_base.py --base <ref>`; sem ref informado,
rode sem `--base` (padrão HEAD~1, o último commit). Se o script sair com
código ≠ 0, pare e reporte a mensagem dele — não audite.

Rode em sessão nova, não na que escreveu o código: quem implementou não é
auditor independente (ADR-0007).
