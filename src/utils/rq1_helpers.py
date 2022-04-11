import itertools

import numpy as np
import pandas as pd
from internal_configs import all_refactoring_types, arch_refactoring_types, all_smell_types
from sklearn.cluster import KMeans

label_categories = {
    5: [
        'Very Low',
        'Low',
        'Medium',
        'High',
        'Very High',
    ],
    3: [
        'Low',
        'Medium',
        'High',
    ]
}


def get_restricted_ref_set(df_xy):
    """
    These two lines below can only have the columns in 'samir_and_our_rows', or can drop the columns from
        the same list. If intersecting the columns, make sure to add timeSpent as1 a column to keep!
    """
    df = df_xy[df_xy.columns.intersection(arch_refactoring_types)]
    df = df.drop(columns=[col for col in arch_refactoring_types if col in df.columns])

    return df


def standardize_columns_by_list(df, attribute_groups, sort_groups=False):
    """
       Standardizes a dataframe.
       @param: df
           Columns should only include refactorings. Index is ignored.
       @return:
           Manipulated df, including:
               ► All refactoring columns. If a refactoring did not occur in the df, then the columns is filled with 0s
               ► Alphabetical sorting of columns
               ► Casting of all data to float
       """
    df = df.copy()

    # get every attribute into one large list
    attribute_groups_sorted = None
    if sort_groups:
        attribute_groups_sorted = [sorted(group) for group in attribute_groups]
    else:
        attribute_groups_sorted = [group for group in attribute_groups]

    every_attribute = list(itertools.chain.from_iterable(attribute_groups_sorted))
    # Rename columns from "Sample Smell" to "sample_smell" appropriately; BEST EFFORT
    df.columns = df.apply(
        lambda x: x.name.lower().replace(' ', '_')
        if x.name.lower().replace(' ', '_') in every_attribute else
        x.name,
        axis=0)

    df = df.merge(pd.DataFrame(columns=every_attribute), how='left').fillna(0)
    df_list = df[every_attribute].astype(float, errors='ignore')
    df_non_list = df[df.columns.symmetric_difference(every_attribute, sort=False)]

    # Sort list columns alphabetically
    # df_attributes = df_list.reindex(columns=sorted(df_list.columns))
    # print(df_attributes.columns)

    return pd.concat([df_non_list, df_list], axis=1)


def standardize_smells_columns(df):
    return standardize_columns_by_list(df, [all_smell_types])


def standardize_refactoring_columns(df):
    return standardize_columns_by_list(df, [all_refactoring_types])


def discretize_series(original_series, n_classes, categorization_method):
    """
    @param: original_series
        Target pandas.Series object
    @param: n_classes
        Discrete number of classes
    @param: categorization_method
        Algorithm string to divide original_series into n_classes. Options:
            'quantile', 'quantile_uneven_bins', 'quantile_original', 'kmeans'

    @return: original_series with same indices, only with categories in place of numeric values
    """

    y = original_series.tolist()

    if len(y) <= 0:
        raise Exception('NO VALUES IN SERIES WHEN DISCRETIZING')

    category_labels = label_categories.get(n_classes)

    if not category_labels:
        raise Exception(f'Invalid class number: {n_classes}')

    class_values = None
    if categorization_method == 'quantile_even_bins':
        # Each bin attempts to have an equal number of values
        # Duplicate values often make the bin sizes non-even, though that is not problematic for this project
        try:
            class_values = pd.qcut(y, n_classes, labels=category_labels)
        except:
            class_values = ['Medium'] * len(y)
    elif categorization_method == 'quantile_uneven_bins':
        # Each bin attempts to have the same range
        # Very vulnerable to outliers
        class_values = pd.cut(y, n_classes, labels=category_labels)
    elif categorization_method == 'kmeans':
        try:
            y_reshaped = np.array(y).reshape((len(y), 1))
            kmeans = KMeans(n_clusters=n_classes, random_state=0).fit(y_reshaped)
            cluster_ownership = list(kmeans.labels_)

            # Find one Jira time spent for each unique cluster. These clusters are not ordered.
            # Ex:     Clusters: [   2,    0,    1]
            #      Time Spents: [4500, 3000, 6000]
            cluster_value_tuples = []
            for cluster_id in range(0, n_classes):
                first_index_with_cluster = cluster_ownership.index(cluster_id)
                cluster_value_tuples.append((y[first_index_with_cluster], cluster_id))

            # print(cluster_value_tuples)

            # Sort Jira times & cluster tuples in parallel, based on the first value in the tuple (time_spent)
            # Ex:     Clusters: [   0,    2,    1]
            #      Time Spents: [3000, 4500, 6000]
            sorted_cluster_values, sorted_clusters = zip(*sorted(cluster_value_tuples))

            # Find mapping from ordered cluster number (0, 2, 1) to string categories ('Low', 'Medium', 'High')
            cluster_map = {}
            for i, cluster_id in enumerate(sorted_clusters):
                cluster_map[cluster_id] = category_labels[i]

            # Apply map from instance clusters to instance class value
            named_clusters = list(map(lambda x: cluster_map[x], cluster_ownership))

            class_values = pd.DataFrame({'class_value': named_clusters}, index=original_series.index)
        except:
            class_values = ['Medium'] * len(y)
    else:
        raise Exception('Invalid categorization algorithm: ' + str(categorization_method))

    return pd.DataFrame(class_values)


def process_outlier_removal(df, inspecting_column, removal_type='top_n_percent'):
    """
    Removes outliers from dataframe based on an inspecting column. Should not modify df.
    @param: df
        A full dataframe containing a column with inspecting_column
    @param: inspecting_column
        A string describing the column of interest for outlier removal
    @param: removal_type
        One of TODO several outlier removal algorithms

    @return: df, but with outliers removed
    """
    rows_to_keep = None

    if removal_type == 'top_n_percent':
        inspecting_series = df[inspecting_column]
        max_value = max(inspecting_series)
        border_value = max_value - (0.1 * max_value)
        rows_to_keep = inspecting_series[inspecting_series < border_value]
    elif removal_type == 'top_5_percentile':
        inspecting_series = df[inspecting_column]
        rows_to_keep = inspecting_series[inspecting_series < np.percentile(inspecting_series, 95)]
    elif removal_type is None:
        return df

    return df.loc[rows_to_keep.index].reset_index(drop=True)


if __name__ == '__main__':
    df = pd.DataFrame({
        'project': ['ambari', 'zookeeper'],
        'version': ['1.4', '2.0'],
        'code_churn': [16, 122],
        'package': ['A', 'B'],
        'ambiguous_interface': [2, 5],
        'broken_modularization': [663, 123],
        'Rename Parameter': [6, 3],
        'Rename Attribute': [7, 4]
    })
    df = standardize_columns_by_list(df, [all_metric_types, all_refactoring_types, all_smell_types])
    print(df.to_string())
    # df = standardize_refactoring_columns(df)
    # print(df.to_string())

    # #ar = [21600.0, 17280.0, 26400.0, 26400.0, 43200.0, 23400.0, 21600.0, 21600.0, 21000.0, 20400.0, 19200.0, 18000.0, 17400.0, 16800.0, 16200.0, 15600.0, 15000.0, 14400.0, 14400.0, 13800.0, 13200.0, 13200.0, 13200.0, 12600.0, 12600.0, 12000.0, 12000.0, 12000.0, 11400.0, 11400.0, 11400.0, 11400.0, 10800.0, 10800.0, 10800.0, 10800.0, 10800.0, 10800.0, 10200.0, 10200.0, 10200.0, 10200.0, 10200.0, 10200.0, 9600.0, 9600.0, 9600.0, 9600.0, 9600.0, 9600.0, 9600.0, 9600.0, 9600.0, 9600.0, 9000.0, 9000.0, 9000.0, 9000.0, 9000.0, 9000.0, 9000.0, 9000.0, 9000.0, 9000.0, 8400.0, 8400.0, 8400.0, 8400.0, 8400.0, 8400.0, 7800.0, 7800.0, 7800.0, 7800.0, 7800.0, 7800.0, 7800.0, 7800.0, 7800.0, 7800.0, 7800.0, 7800.0, 7800.0, 7200.0, 7200.0, 7200.0, 7200.0, 7200.0, 7200.0, 7200.0, 7200.0, 7200.0, 7200.0, 7200.0, 6600.0, 6600.0, 6600.0, 6600.0, 6600.0, 6600.0, 6600.0, 6600.0, 6600.0, 6600.0, 6600.0, 6000.0, 6000.0, 6000.0, 6000.0, 6000.0, 6000.0, 6000.0, 6000.0, 6000.0, 6000.0, 6000.0, 6000.0, 6000.0, 5400.0, 5400.0, 5400.0, 5400.0, 5400.0, 5400.0, 5400.0, 5400.0, 5400.0, 5400.0, 5400.0, 5400.0, 5400.0, 5400.0, 5400.0, 5400.0, 5400.0, 4800.0, 4800.0, 4800.0, 4800.0, 4800.0, 4800.0, 4800.0, 4800.0, 4800.0, 4800.0, 4800.0, 4800.0, 4800.0, 4200.0, 4200.0, 4200.0, 4200.0, 4200.0, 4200.0, 4200.0, 4200.0, 4200.0, 4200.0, 4200.0, 4200.0, 4200.0, 4200.0, 4200.0, 4200.0, 4200.0, 3600.0, 3600.0, 3600.0, 3600.0, 3600.0, 3600.0, 3600.0, 3600.0, 3600.0, 3600.0, 3600.0, 3600.0, 3600.0, 3600.0, 3600.0, 3600.0, 3600.0, 3600.0, 3600.0, 3600.0, 3600.0, 3600.0, 3600.0, 3600.0, 3600.0, 3600.0, 3600.0, 3600.0, 3600.0, 3600.0, 3600.0, 3000.0, 3000.0, 3000.0, 3000.0, 3000.0, 3000.0, 3000.0, 3000.0, 3000.0, 3000.0, 3000.0, 3000.0, 3000.0, 3000.0, 3000.0, 3000.0, 3000.0, 3000.0, 2400.0, 2400.0, 2400.0, 2400.0, 2400.0, 2400.0, 2400.0, 2400.0, 2400.0, 2400.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1800.0, 1200.0, 1200.0, 1200.0, 1200.0, 1200.0, 1200.0, 1200.0, 1200.0, 1200.0, 600.0]
    # ar = [10, 15, 20, 30, 50, 70, 100]
    # my_series = pd.Series(ar)
    # x = discretize_series(my_series, 3, 'quantile_uneven_bins')
    #
    # print(x.to_string())
    # print(x.value_counts().to_string())
    # print(my_series.value_counts().sort_index())
