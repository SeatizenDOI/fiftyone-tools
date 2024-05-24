<p align="center">
  <a href="https://github.com/SeatizenDOI/fiftyone-tools/graphs/contributors"><img src="https://img.shields.io/github/contributors/SeatizenDOI/fiftyone-tools" alt="GitHub contributors"></a>
  <a href="https://github.com/SeatizenDOI/fiftyone-tools/network/members"><img src="https://img.shields.io/github/forks/SeatizenDOI/fiftyone-tools" alt="GitHub forks"></a>
  <a href="https://github.com/SeatizenDOI/fiftyone-tools/issues"><img src="https://img.shields.io/github/issues/SeatizenDOI/fiftyone-tools" alt="GitHub issues"></a>
  <a href="https://github.com/SeatizenDOI/fiftyone-tools/blob/master/LICENSE"><img src="https://img.shields.io/github/license/SeatizenDOI/fiftyone-tools" alt="License"></a>
  <a href="https://github.com/SeatizenDOI/fiftyone-tools/pulls"><img src="https://img.shields.io/github/issues-pr/SeatizenDOI/fiftyone-tools" alt="GitHub pull requests"></a>
  <a href="https://github.com/SeatizenDOI/fiftyone-tools/stargazers"><img src="https://img.shields.io/github/stars/SeatizenDOI/fiftyone-tools" alt="GitHub stars"></a>
  <a href="https://github.com/SeatizenDOI/fiftyone-tools/watchers"><img src="https://img.shields.io/github/watchers/SeatizenDOI/fiftyone-tools" alt="GitHub watchers"></a>
</p>

<div align="center">
  <a href="https://github.com/SeatizenDOI/fiftyone-tools">View framework</a>
  ·
  <a href="https://github.com/SeatizenDOI/fiftyone-tools/issues">Report Bug</a>
  ·
  <a href="https://github.com/SeatizenDOI/fiftyone-tools/issues">Request Feature</a>
</div>

<div align="center">

# Fiftyone tools

</div>


## Summary

* [Installation](#installation)
* [Usage](#usage)
* [Tips](#tips)
* [Plugins](#plugins)
* [Contributing](#contributing)
* [License](#license)

## Installation

To ensure a consistent environment for all users, this project uses a Conda environment defined in a `fiftyone_env.yml` file. Follow these steps to set up your environment:

1. **Install Conda:** If you do not have Conda installed, download and install [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/products/distribution).

2. **Create the Conda Environment:** Navigate to the root of the project directory and run the following command to create a new environment from the `fiftyone_env.yml` file:
   ```bash
   conda env create -f fiftyone_env.yml
   ```

3. **Activate the Environment:** Once the environment is created, activate it using:
   ```bash
   conda activate fiftyone_env
   ```

4. **Export global variable:** Export global variable to use plugins
    ```bash
    echo "export FIFTYONE_PLUGINS_DIR=\"$(pwd)/__plugins__\"" >> ~/.bashrc
    ```

## Usage

In `fiftyone.ipynb`, execute the first cell to launch application. When importing dataset, always check delegated checkbox.

To delete all present dataset, execute the second cell.

Launch fiftyone delegated in bash terminal
```bash
fiftyone delegated launch
```

## Tips

List all installed plugins
```bash
fiftyone plugins list
```

Install a remote plugins like io
```bash
fiftyone plugins download https://github.com/voxel51/fiftyone-plugins --plugin-names @voxel51/io
fiftyone plugins download https://github.com/voxel51/fiftyone-plugins --plugin-names @voxel51/plugins
```


## Plugins

### TODO: Edit multi label

### TODO: Manager dataset csv 


## Contributing

Contributions are welcome! To contribute, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or fix.
3. Commit your changes with clear, descriptive messages.
4. Push your branch and submit a pull request.

## License

This framework is distributed under the wtfpl license. See `LICENSE` for more information.