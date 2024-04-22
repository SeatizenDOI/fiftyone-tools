import cv2
import os
import pandas as pd

import fiftyone as fo
import fiftyone.utils.data as foud

## Inspired from : 
# https://voxel51.com/docs/fiftyone/recipes/custom_importer.html
## to implement multilabel classifications, see : 
# https://voxel51.com/docs/fiftyone/user_guide/using_datasets.html?highlight=multilabel

class CSVImageClassificationDatasetImporter(foud.LabeledImageDatasetImporter):
    """Importer for image classification datasets whose filepaths and labels
    are stored on disk in a CSV file.

    Datasets of this type should contain a ``labels.csv`` file in their
    dataset directories in the following format::

        filepath,size_bytes,mime_type,width,height,num_channels,label
        <filepath>,<size_bytes>,<mime_type>,<width>,<height>,<num_channels>,<label>
        <filepath>,<size_bytes>,<mime_type>,<width>,<height>,<num_channels>,<label>
        ...

    Args:
        dataset_dir: the dataset directory
        shuffle (False): whether to randomly shuffle the order in which the
            samples are imported
        seed (None): a random seed to use when shuffling
        max_samples (None): a maximum number of samples to import. By default,
            all samples are imported
    """

    def __init__(
        self,
        dataset_dir,
        csv_labels,
        shuffle=False,
        seed=None,
        max_samples=None,
        isNewArchi=False
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
        self.isNewArchi = isNewArchi

    def __iter__(self):
        self._iter_labels = iter(self._labels)
        return self

    def __next__(self):
        """Returns information about the next sample in the dataset.

        Returns:
            an  ``(image_path, image_metadata, label)`` tuple, where

            -   ``image_path``: the path to the image on disk
            -   ``image_metadata``: an
                :class:`fiftyone.core.metadata.ImageMetadata` instances for the
                image, or ``None`` if :meth:`has_image_metadata` is ``False``
            -   ``label``: an instance of :meth:`label_cls`, or a dictionary
                mapping field names to :class:`fiftyone.core.labels.Label`
                instances, or ``None`` if the sample is unlabeled

        Raises:
            StopIteration: if there are no more samples to import
        """
        (
            image,
            size_bytes,
            width,
            height,
            num_channels,
            label
        ) = next(self._iter_labels)
        image_metadata = fo.ImageMetadata(
            size_bytes=size_bytes,
            width=width,
            height=height,
            num_channels=num_channels,
        )

        label = fo.Classifications(classifications=label)
        return image, image_metadata, label

    def __len__(self):
        """The total number of samples that will be imported.

        Raises:
            TypeError: if the total number is not known
        """
        return len(self._labels)

    @property
    def has_dataset_info(self):
        """Whether this importer produces a dataset info dictionary."""
        return False

    @property
    def has_image_metadata(self):
        """Whether this importer produces
        :class:`fiftyone.core.metadata.ImageMetadata` instances for each image.
        """
        return True

    @property
    def label_cls(self):
        """The :class:`fiftyone.core.labels.Label` class(es) returned by this
        importer.

        This can be any of the following:

        -   a :class:`fiftyone.core.labels.Label` class. In this case, the
            importer is guaranteed to return labels of this type
        -   a list or tuple of :class:`fiftyone.core.labels.Label` classes. In
            this case, the importer can produce a single label field of any of
            these types
        -   a dict mapping keys to :class:`fiftyone.core.labels.Label` classes.
            In this case, the importer will return label dictionaries with keys
            and value-types specified by this dictionary. Not all keys need be
            present in the imported labels
        -   ``None``. In this case, the importer makes no guarantees about the
            labels that it may return
        """
        return fo.Classifications

    def setup(self):
        """Performs any necessary setup before importing the first sample in
        the dataset.

        This method is called when the importer's context manager interface is
        entered, :func:`DatasetImporter.__enter__`.
        """
        labels = []
        df_multilabel = pd.read_csv(self.csv_labels)
        filename = "FileName" if self.isNewArchi else "OriginalFileName"

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
                if row[class_label] == 1:
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
        """Performs any necessary actions after the last sample has been
        imported.

        This method is called when the importer's context manager interface is
        exited, :func:`DatasetImporter.__exit__`.

        Args:
            *args: the arguments to :func:`DatasetImporter.__exit__`
        """
        pass