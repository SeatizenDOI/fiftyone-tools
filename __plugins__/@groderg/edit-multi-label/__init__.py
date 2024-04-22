import fiftyone.operators as foo
import fiftyone.operators.types as types
import fiftyone as fo

GROUND_TRUTH = "ground_truth_multilabel"

# Return a list of unique occurence of label in an image for a fo.Classifictions
def _get_labels(sample, field):
    return list(set([a["label"] for a in sample[field]["classifications"]])) if type(sample[field]) == fo.Classifications else []

# Return true if label_to_find is in field. Field is a fo.Classifications
def _label_in_fields(fields, label_to_find):
    for field in fields:
        if field["label"] == label_to_find:
            return True
    return False

class ManageModalLabel(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="manage_modal_label",
            label="Manage label",
            light_icon="/assets/icon-modal-light.svg",
            dark_icon="/assets/icon-modal-dark.svg",
            dynamic=True,
        )
    
    def resolve_placement(self, ctx):
        return types.Placement(
            types.Places.SAMPLES_VIEWER_ACTIONS,
            types.Button(
                label="Manage label",
                prompt=True,
            ),
        )
    
    def resolve_input(self, ctx):
        form_view = types.View(label="Add or remove label")
        inputs = types.Object()
        
        _install_manage_label(ctx, inputs)

        return types.Property(inputs, view=form_view)
    
    def execute(self, ctx):
        sample = ctx.dataset[ctx.current_sample]
        for group in ctx.dataset.classes:
            labels_to_manage = ctx.params.get(f"{group}_labels", [])

            # Get label to add and label to remove
            existing_labels = _get_labels(sample, group)
            label_to_add = [a for a in labels_to_manage if a not in existing_labels]
            label_to_remove = [a for a in existing_labels if a not in labels_to_manage]

            # Update sample
            for la in label_to_add:
                sample[group]["classifications"].append(fo.Classification(label=la))
            
            _removeLabelClassifications(sample, group, label_to_remove)
            
        sample.save()

class AddGridLabel(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="add_grid_label",
            label="Add label",
            light_icon="/assets/icon-grid-light.svg",
            dark_icon="/assets/icon-grid-dark.svg",
            dynamic=True,
        )
    
    def resolve_placement(self, ctx):
        return types.Placement(
            types.Places.SAMPLES_GRID_SECONDARY_ACTIONS,
            types.Button(
                label="Add label",
                prompt=True,
            ),
        )
    
    def resolve_input(self, ctx):
        form_view = types.View(label="Add label")

        inputs = types.Object()

        _install_grid_label(ctx, inputs)

        return types.Property(inputs, view=form_view)
    
    def execute(self, ctx):
        for group in ctx.dataset.classes:
            labels_to_add = ctx.params.get(f"{group}_labels", None)
            if not labels_to_add: continue

            # Iter on each selected samples
            for sampleId in ctx.selected:
                sample = ctx.dataset[sampleId]
                        
                # Iter on each label and check if not in sample fields
                for la in labels_to_add:
                    if not _label_in_fields(sample[group]["classifications"], la):
                        sample[group]["classifications"].append(fo.Classification(label=la))
                sample.save()

class RemoveGridLabel(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="remove_grid_label",
            label="Remove label",
            light_icon="/assets/icon-grid-light.svg",
            dark_icon="/assets/icon-grid-dark.svg",
            dynamic=True,
        )
    
    def resolve_placement(self, ctx):
        return types.Placement(
            types.Places.SAMPLES_GRID_SECONDARY_ACTIONS,
            types.Button(
                label="Remove label",
                prompt=True,
            ),
        )
    
    def resolve_input(self, ctx):
        form_view = types.View(label="Remove label")
        inputs = types.Object()

        _install_grid_label(ctx, inputs)

        return types.Property(inputs, view=form_view)
    
    def execute(self, ctx):
        for group in ctx.dataset.classes:
            labels_to_remove = ctx.params.get(f"{group}_labels", None)
            if not labels_to_remove: continue

            # Iter on each selected samples
            for sampleId in ctx.selected:
                sample = ctx.dataset[sampleId]
                _removeLabelClassifications(sample, group, labels_to_remove)
                sample.save()

class CreateGroundTruthLabel(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="create_gt_label",
            label="Create ground_truth label",
            light_icon="/assets/icon-create-light.svg",
            dark_icon="/assets/icon-create-dark.svg",
            dynamic=True,
        )
    
    def resolve_input(self, ctx):
        inputs = types.Object()
        # Groups labels.
        dropdown_groups = types.DropdownView(description="Choose which group labels to edit")
        for group in ctx.dataset.classes:
            dropdown_groups.add_choice(group, label=group)

        inputs.enum("groups", dropdown_groups.values(), view=dropdown_groups, default=dropdown_groups.choices[0].value)
        inputs.str("label", label="Label", required=True)

        return types.Property(inputs, view=types.View(label="Create ground_truth label"))

    def execute(self, ctx):
        group = ctx.params.get("groups", None)
        labelToAdd = ctx.params.get("label", None)
        if not labelToAdd or not group: return

        ctx.dataset.classes[group].append(labelToAdd)

class DeleteGroundTruthLabel(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="delete_gt_label",
            label="Delete ground_truth label",
            light_icon="/assets/icon-delete-light.svg",
            dark_icon="/assets/icon-delete-dark.svg",
            dynamic=True,
        )
    
    def resolve_input(self, ctx):
        inputs = types.Object()

        _install_grid_label(ctx, inputs)

        return types.Property(inputs, view=types.View(label="Delete ground_truth label"))
    
    
    def resolve_delegation(self, ctx):
        return ctx.params.get("delegate", False)


    def resolve_delegation(self, ctx):
        return ctx.params.get("delegate", False)

    def execute(self, ctx):
        for group in ctx.dataset.classes:
            labelsToRemove = ctx.params.get(f"{group}_labels", None)
            if not labelsToRemove: continue

            # Iter on each samples and delete the label
            for sample in ctx.dataset.iter_samples(progress=True):
                _removeLabelClassifications(sample, group, labelsToRemove)
                sample.save()
            
            for label in labelsToRemove:
                if label in ctx.dataset.classes[group]:
                    ctx.dataset.classes[group].remove(label)
        
        ctx.trigger("reload_dataset")

def _removeLabelClassifications(sample, groups, labels_to_remove):
    if sample[groups] == None: return 

    # Iter on each labels and found label index to remove
    label_index_to_remove = [index for index, a in enumerate(sample[groups]["classifications"]) if a["label"] in labels_to_remove]

    # Iter on index to remove but reverse to not shift index position
    for index in label_index_to_remove[::-1]:
        sample[groups]["classifications"].pop(index)

def _install_manage_label(ctx, inputs):
    sample = ctx.dataset[ctx.current_sample]

    for group in ctx.dataset.classes:
        dropdown_labels = types.DropdownView(label=group, description="Select one or more labels")

        for lb in ctx.dataset.classes[group]:
            dropdown_labels.add_choice(lb, label=lb)
        labels = _get_labels(sample, group)    

        inputs.list(f"{group}_labels", types.String(), view=dropdown_labels, default=labels)
    return True

def _install_grid_label(ctx, inputs):
    for group in ctx.dataset.classes:
        dropdown_labels = types.DropdownView(label=group, description="Select one or more labels")
        for lb in ctx.dataset.classes[group]:
            dropdown_labels.add_choice(lb, label=lb)
        inputs.list(f"{group}_labels", types.String(), view=dropdown_labels, default=None)

    return True


def register(p):
    p.register(ManageModalLabel)
    p.register(AddGridLabel)
    p.register(RemoveGridLabel)
    p.register(CreateGroundTruthLabel)
    p.register(DeleteGroundTruthLabel)