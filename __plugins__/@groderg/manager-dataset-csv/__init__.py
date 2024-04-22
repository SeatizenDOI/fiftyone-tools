import os
import cv2
import pandas as pd
from pathlib import Path
from datetime import datetime

import fiftyone as fo
import fiftyone.operators as foo
import fiftyone.utils.data as foud
import fiftyone.core.storage as fos
import fiftyone.operators.types as types

class ImportDataset(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="import_dataset_csv",
            label="Import dataset from CSV",
            light_icon="/assets/icon-import-light.svg",
            dark_icon="/assets/icon-import-dark.svg",
            dynamic=True,
        )
    
    def resolve_input(self, ctx):
        inputs = types.Object()

        ready = _install_import(ctx, inputs)
        if ready:
            _execution_mode(ctx, inputs)

        return types.Property(inputs, view=types.View(label="Import dataset from CSV"))
    
    def resolve_delegation(self, ctx):
        return ctx.params.get("delegate", False)

    def execute(self, ctx):
        dataset_name = ctx.params.get("dataset_name", "multilabel")
        dataset_dir = _parse_path(ctx, "dataset_folder")
        persistent = ctx.params.get("persistent", False)
        labels_files = [(lb.get("group_label_name"), lb.get("labels_path").get("absolute_path", None) if lb.get("labels_path") else None) for lb in ctx.params["labels_list"]]

        # Create dataset and import labels.
        if not dataset_dir or len(labels_files) < 1: return
        dataset =_import_labels(dataset_name, dataset_dir, labels_files, persistent)
       
        # If we tags import tags.
        needTags = ctx.params.get("import_tags", False)
        lb_file = None
        for _, path in labels_files:
            if "_labels.csv" in path:
                lb_file = path
        if not needTags or lb_file == None: return
        tags_path = lb_file.replace("_labels.csv", "_tags.csv")
        if not os.path.exists(tags_path): return
        _import_tags(dataset, tags_path)

class ExportDataset(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="export_dataset_csv",
            label="Export dataset to CSV",
            light_icon="/assets/icon-export-light.svg",
            dark_icon="/assets/icon-export-dark.svg",
            dynamic=True,
        )
    
    def resolve_input(self, ctx):
        inputs = types.Object()

        ready = _install_export(ctx, inputs)
        if ready:
            _execution_mode(ctx, inputs)

        return types.Property(inputs, view=types.View(label="Export dataset to CSV"))
    
    def resolve_delegation(self, ctx):
        return ctx.params.get("delegate", False)

    def execute(self, ctx):
        group_label = ctx.params.get("labels_choice", None)
        folder_path = _parse_path(ctx, "folder_path")
        exportingTag = ctx.params.get("export_tags", None)
        ctx.trigger("reload_dataset")
        
        if not group_label or not folder_path: return
        current_time = str(datetime.now().strftime("%Y%m%d_%H%M%S"))  

        # Export labels.
        csv_exporter = CSVLabelsDatasetExporter(
            export_dir=folder_path,
            file_name=f"{current_time}_{ctx.dataset.name}_{group_label}",
            default_classes=ctx.dataset.classes[group_label]
        )
        ctx.dataset.export(dataset_exporter=csv_exporter)
        
        # Export tags.
        if not exportingTag: return 
        default_tags = _get_all_tags(ctx.dataset)
        if default_tags == []: return
        csv_tags_path = os.path.join(folder_path, current_time+"_tags.csv")
        _export_csv_tags(ctx.dataset, default_tags, csv_tags_path)


def _install_import(ctx, inputs):

    # Dataset name.
    inputs.str("dataset_name", label="Dataset name", default="", required=True)

    # Dataset folder.
    file_explorer = types.FileExplorerView(
        choose_dir=True,
        button_label="Choose a directory...",
    )
    prop = inputs.file(
        "dataset_folder",
        required=True,
        label="Dataset",
        description="Choose a directory of media to add to this dataset",
        view=file_explorer,
    )
    directory = _parse_path(ctx, "dataset_folder")

    if directory:
        n = len(_glob_files(directory=directory))
        if n > 0:
            prop.view.caption = f"Found {n} files"
        else:
            prop.invalid = True
            prop.error_message = "No matching files"
    else:
        prop.view.caption = None
        return False

    # Labels file.
    labels_list = types.Object()
    prop_name = labels_list.str(
        "group_label_name", 
        label="Group labels name", 
        description="Choose the name of the group labels", 
        view=types.View(space=6),
        required=True
    )
    
    ext = ".csv"
    prop_file = labels_list.file(
        "labels_path",
        required=True,
        label="Path to labels file",
        description=f"Choose a {ext} file with the labels",
        view=types.View(space=6),
    )
    
    inputs.list("labels_list", labels_list, required=True, label="List of labels")

    if not ctx.params.get("labels_list"): return False

    labels_names = [lb.get("group_label_name") for lb in ctx.params.get("labels_list")]
    labels_paths = [lb.get("labels_path").get("absolute_path", None) if lb.get("labels_path") else None for lb in ctx.params.get("labels_list")]

    # Check for None.
    if None in labels_names or None in labels_paths:
        return False

    # Check for file extension.
    for lb in labels_paths:
        if os.path.splitext(lb)[1] != ext:
            prop_file.invalid = True
            prop_file.error_message = f"Please provide a {ext} path"
            return False
    # Check for different names.
    if len(set(labels_names)) != len(labels_names):
        prop_name.invalid = True
        prop_name.error_message = "Cannot have same name"
        return False
    
    # Persistent bool.
    inputs.bool(
        "persistent",
        default=False,
        label="Persistent dataset",
        description=("Persistent dataset even if server reboot"),
        view=types.CheckboxView(),
    )

    # Tags file.
    inputs.bool(
        "import_tags",
        default=False,
        label="Tags",
        description=("Import tags from a csv who have a matching name with labels file"),
        view=types.CheckboxView(),
    )
    
    needTags = ctx.params.get("import_tags", False)
    if needTags:
        lb_with = None
        for lb in labels_paths:
            if "_labels.csv" in lb:
                lb_with = lb
                break
        if lb_with == None:
            inputs.view(
                "warning",
                types.Error(label=f"Label doesn't have _labels.csv. Cannot find corresponding tag csv file"),
            )
            return False
        potential_csv_path = lb_with.replace("_labels.csv", "_tags.csv")
        isExisting = os.path.exists(potential_csv_path)
        if not isExisting:
            inputs.view(
                "warning",
                types.Error(label=f"File {potential_csv_path} doesn't exist."),
            )
            return False
    return True

def _import_labels(dataset_name, dataset_dir, labels_path, persistent):

    # As Importer cannot import multiple labels in the same time.
    # We get the first tuple and we add the next labels after.
    first_label_name, first_label_path = labels_path[0]

    # Create importer
    csv_importer = CSVLabelsDatasetImporter(
        dataset_dir,
        csv_labels = first_label_path
    )

    # Create dataset
    dataset = fo.Dataset.from_importer(
        csv_importer, 
        name=dataset_name,
        label_field=first_label_name,
        progress=True,
        persistent=persistent
    )

    # Process all other labels
    for label_name, label_path in labels_path[1:]:
        # dataset.add_sample_field(label_name, fo.EmbeddedDocumentField)
        df = pd.read_csv(label_path)
        # Build a dict with filename: [label]
        labels_for_file = {}
        for _, row in df.iterrows():
            name = row.iloc[0]
            labels_for_file[name] = []
            for class_label in range(len(df.columns)):
                if row.iloc[class_label] == 1:
                    labels_for_file[name].append(fo.Classification(label=df.columns[class_label]))

        for sample in dataset.iter_samples(progress=True):
            b = fo.Classifications() 
            if Path(sample.filepath).name in labels_for_file:
                b.classifications = labels_for_file[Path(sample.filepath).name]
            sample[label_name] = b
            sample.save()

    # Add year, month and day as primitive
    dataset.add_sample_field("year", fo.IntField)
    dataset.add_sample_field("month", fo.IntField)
    dataset.add_sample_field("day", fo.IntField)

    for sample in dataset.iter_samples(progress=True):
        date = Path(sample.filepath).name.split("_")[0]
        sample.year = int(date[0:4])
        sample.month = int(date[4:6])
        sample.day = int(date[6:8])
        sample.save()

    # Store labels for each classes in classes
    for label_name, label_path in labels_path:
        with open(label_path, "r") as file:
            for row in file:
                dataset.classes[label_name] = row.replace("\n", "").split(',')[1:]
                break
    dataset.save()
    return dataset

def _import_tags(dataset, tags_path):
    # Read and update tags
    df = pd.read_csv(tags_path)
    for sample in dataset.iter_samples():
        row = df[df["FileName"] == sample.filename].iloc[:, 1:]
        for tag in row:
            if (row[tag] == 1).iloc[0]:
                sample.tags.append(tag)
        sample.save()

def _install_export(ctx, inputs):
    labels_choices = types.Choices()
    for dt in ctx.dataset.classes:
        labels_choices.add_choice(dt, label=dt)

    inputs.enum("labels_choice", 
                labels_choices.values(), 
                view=labels_choices, 
                label="Groups labels", 
                description="Choose group label to export", 
                default=labels_choices.choices[0].value)

    inputs.bool(
        "export_tags",
        default=False,
        label="Tags",
        description=("Export another csv file for tags associated to samples?"),
        view=types.CheckboxView(),
    )

    file_explorer = types.FileExplorerView(button_label="Choose a file...", choose_dir=True)
    inputs.file(
        "folder_path",
        required=True,
        label="Folder to export",
        description=f"Choose a folder for the csv file",
        view=file_explorer,
    )

    labels_path = _parse_path(ctx, "folder_path")
    if labels_path is None:
        return False

    return True

def _execution_mode(ctx, inputs):
    delegate = ctx.params.get("delegate", False)

    if delegate:
        description = "Uncheck this box to execute the operation immediately"
    else:
        description = "Check this box to delegate execution of this task"

    inputs.bool(
        "delegate",
        default=False,
        label="Delegate execution?",
        description=description,
        view=types.CheckboxView(),
    )

    if delegate:
        inputs.view(
            "notice",
            types.Notice(
                label=(
                    "You've chosen delegated execution. Note that you must "
                    "have a delegated operation service running in order for "
                    "this task to be processed. See "
                    "https://docs.voxel51.com/plugins/using_plugins.html#delegated-operations "
                    "for more information"
                )
            ),
        )

def _parse_path(ctx, key):
    value = ctx.params.get(key, None)
    return value.get("absolute_path", None) if value else None

def _glob_files(directory=None, glob_patt=None):
    if directory is not None:
        glob_patt = f"{directory}/*"

    if glob_patt is None:
        return []

    return fos.get_glob_matches(glob_patt)

def _get_all_tags(dataset):
    tags = []
    for sample in dataset.iter_samples(progress=True):
        tags = tags + sample.tags
    return list(set(tags))

def _export_csv_tags(dataset, default_tags, csv_tags_path):
    # Write the labels CSV file
    with open(csv_tags_path, "w") as f:
        f.write("FileName,"+",".join(default_tags)+"\n")
        for sample in dataset.iter_samples(progress=True):
            filename = Path(sample.filepath).name
            row = ["1" if default_tag in sample.tags else "0" for default_tag in default_tags]
            f.write(filename+","+",".join(row)+"\n")


class CSVLabelsDatasetImporter(foud.LabeledImageDatasetImporter):
    def __init__(
        self,
        dataset_dir,
        csv_labels,
        shuffle=False,
        seed=None,
        max_samples=None
    ):
        super().__init__(
            dataset_dir=dataset_dir,
            shuffle=shuffle,
            seed=seed,
            max_samples=max_samples
        )
        self._labels_file = None
        self._labels = None
        self._iter_labels = None
        self.csv_labels = csv_labels
        self.dataset_dir = dataset_dir

    def __iter__(self):
        self._iter_labels = iter(self._labels)
        return self

    def __next__(self): 
        (image, size_bytes, width, height, num_channels, label) = next(self._iter_labels)
        image_metadata = fo.ImageMetadata(
            size_bytes=size_bytes,
            width=width,
            height=height,
            num_channels=num_channels,
        )

        label = fo.Classifications(classifications=label)
        return image, image_metadata, label

    def __len__(self):
        return len(self._labels)

    @property
    def has_dataset_info(self):
        return False

    @property
    def has_image_metadata(self):
        return True

    @property
    def label_cls(self):
        return fo.Classifications

    def setup(self):
        labels = []
        df_multilabel = pd.read_csv(self.csv_labels)
        filename = "FileName"

        for _, row in df_multilabel.iterrows():
            annotations_per_image = []

            # -- Metadata part
            # Get size_bytes of image
            size_bytes = os.path.getsize(os.path.join(self.dataset_dir, str(row[filename])))
            # Get height, width and channels
            im = cv2.imread(os.path.join(self.dataset_dir, str(row[filename])))
            height, width, num_channels = im.shape

            # All class_label for the image
            for class_label in range(len(df_multilabel.columns)):
                if row.iloc[class_label] == 1:
                    classification = fo.Classification(label=df_multilabel.columns[class_label])
                    annotations_per_image.append(classification)
            
            # Store all information
            labels.append((
                os.path.join(self.dataset_dir, str(row[filename])),
                size_bytes, 
                width, 
                height, 
                num_channels,
                annotations_per_image))

        # The `_preprocess_list()` function is provided by the base class
        # and handles shuffling/max sample limits
        self._labels = self._preprocess_list(labels)

    def close(self, *args):
        pass

class CSVLabelsDatasetExporter(foud.LabeledImageDatasetExporter):
    def __init__(self, export_dir, file_name, default_classes):
        self._labels_path = None
        self._labels = None
        self.export_dir = export_dir
        self.labels_csv = file_name + "_labels.csv"
        self.default_classes = sorted(default_classes)

    @property
    def requires_image_metadata(self):
        return True

    @property
    def label_cls(self):
        return fo.Classifications

    def setup(self):
        self._labels_path = os.path.join(self.export_dir, self.labels_csv)
        self._labels = []

    def export_sample(self, image_or_path, label, metadata=None):
        labels_image = [label.classifications[n_label].label for n_label in range(len(label.classifications))]
        row_label = ["1" if default_classe in labels_image else "0" for default_classe in self.default_classes]
        self._labels.append((
            image_or_path.split("/")[-1] if "/" in image_or_path else image_or_path.split("\\")[-1],
            row_label,  # here, `row_label` is a list of 0 or 1 and position refering to the label in default classes
        ))

    def close(self, *args):
        # Ensure the base output directory exists
        basedir = os.path.dirname(self._labels_path)
        if basedir and not os.path.isdir(basedir):
            os.makedirs(basedir)

        # Write the labels CSV file
        with open(self._labels_path, "w") as f:
            f.write("FileName,"+",".join(self.default_classes)+"\n")

            for row in self._labels:
                f.write(row[0]+","+",".join(row[1])+"\n")

def register(p):
    p.register(ExportDataset)
    p.register(ImportDataset)