Mostre o status atual do SpecLoop de forma compacta:
1. Rode: cat loop/prd.json | jq '{feature, pendentes: [.userStories[] | select(.passes==false) | .id], completas: [.userStories[] | select(.passes==true) | .id]}'
2. Mostre as últimas 10 linhas de state/progress.md
3. Mostre as últimas 5 linhas de state/metrics.csv
4. Rode git log --oneline -5
Resuma em 3 linhas: onde o loop está, qual a próxima história e se há bloqueios.
