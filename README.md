# ECD Parser

This repository contains a small utility for validating SPED ECD files.

## Usage

```
python ecd_parser.py --input caminho/do/arquivo_original.ECD --output caminho/do/arquivo_corrigido.ECD
```

The script checks whether the opening balances in the `I155` records match the closing balances from the previous year detailed by cost center (`I355`). If differences are found, `X935` records are generated automatically and inserted before the `X990` record in the output file.
