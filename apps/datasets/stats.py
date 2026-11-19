from apps.datasets.models import Dataset


def count_by_type():
    """Return how many datasets exist for each type."""
    result = {}
    for dataset in Dataset.objects.all():
        key = dataset.type
        if key not in result:
            result[key] = 0
        result[key] += 1
    return result


def largest_dataset():
    """Return the dataset with the most files, or None."""
    return Dataset.objects.order_by("-file_count").first()
