# Deprecated path

`data/figure_data/` has been split to reduce ambiguity:

- `data/table_data/` for table-derived exports (Tables 2-7, 11-16)
- `data/figure_series/` for figure/graph datasets (Figure 4-8 and appendix figure series)

Use:

```bash
python scripts/export_figure_data.py
```

or scoped exports:

```bash
python scripts/export_figure_data.py --tables-only
python scripts/export_figure_data.py --figures-only
```
