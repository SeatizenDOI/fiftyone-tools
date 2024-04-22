
# Create env

```bash
conda create --name fiftyone_env python=3.9
conda activate fiftyone_env
pip install fiftyone
```

Before to install plugins we need to change the default path to use plugins.

If you are using an unix machine, tap this command at the root of this folder:
```bash
echo 'export FIFTYONE_PLUGINS_DIR="$(pwd)/__plugins__"' >> $HOME/.bashrc
echo 'export FIFTYONE_MODULE_PATH="$(pwd)/__plugins__"' >> .bashrc
```

After install fiftyone, we have a command line tools to manage plugins

List all installed plugins
```bash
fiftyone plugins list
```

Install a remote plugins like io
```bash
fiftyone plugins download https://github.com/voxel51/fiftyone-plugins --plugin-names @voxel51/io
fiftyone plugins download https://github.com/voxel51/fiftyone-plugins --plugin-names @voxel51/plugins
```

# Dataset manage

Your dataset need to be in a dataset folder.

Your labels csv need to be in a labels_csv folder.

Your export csv will be export in a export_csv folder.

# Todo

- Add plugins exporter
- Add group labels selector 