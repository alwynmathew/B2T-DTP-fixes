# BIM2TWIN DTP fixes

This repo fixes issues in BIM2TWIN DTP originated from Orange IFC injector. The python script will add `asDesigned` and
replace `ifc:Class` with `https://www.bim2twin.eu/ontology/Core#hasElementType` in as-planned element nodes.

The code was extracted from the internal code of WP3.

> **Warning**
> CAUTION: This script modified multiple nodes in the graph.

You can run the script with the below command:

```shell
python3 fix_graph.py --log_dir path/to/session-log/dir
```

Please use simulation node with flag `--simulation` or `-s` if you are unsure how the script will perform in your DTP
domain and check the log files.